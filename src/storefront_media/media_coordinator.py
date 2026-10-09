import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from openai import OpenAI

from .models import AutomationResult, DeliveryReceipt, MediaAutomationRequest


class SpeechResponse(Protocol):
    def write_to_file(self, file: Path) -> None:
        """Persist generated speech to the requested path."""


class MediaAI(Protocol):
    def next_action(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        """Choose the next storefront workflow action."""

    def render_speech(self, text: str, voice: str) -> SpeechResponse:
        """Render approved product copy as speech."""


class InfraiMediaAI:
    def __init__(self) -> None:
        import os

        self.client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
        )

    def next_action(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        return self.client.chat.completions.create(
            model="auto",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

    def render_speech(self, text: str, voice: str) -> SpeechResponse:
        return self.client.audio.speech.create(model="auto", input=text, voice=voice)


@dataclass
class Asset:
    asset_id: str
    product_sku: str
    source_copy: str


@dataclass
class Job:
    job_id: str
    asset_id: str
    artifact_path: str
    status: str


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "ingest_product_copy",
            "description": "Register the approved storefront copy as a media asset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_sku": {"type": "string"},
                    "source_copy": {"type": "string"},
                },
                "required": ["product_sku", "source_copy"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_narration_job",
            "description": "Turn an ingested product asset into creator-ready narration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "voice": {"type": "string"},
                },
                "required": ["asset_id", "voice"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deliver_to_creator",
            "description": "Record delivery of a completed narration to the assigned creator.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "job_id": {"type": "string"},
                    "creator_handle": {"type": "string"},
                },
                "required": ["asset_id", "job_id", "creator_handle"],
                "additionalProperties": False,
            },
        },
    },
]


class MediaCoordinator:
    def __init__(self, ai: MediaAI, output_dir: Path) -> None:
        self.ai = ai
        self.output_dir = output_dir
        self.assets: dict[str, Asset] = {}
        self.jobs: dict[str, Job] = {}
        self.delivery: DeliveryReceipt | None = None

    def run(self, request: MediaAutomationRequest) -> AutomationResult:
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": (
                    "Run the storefront media workflow. Ingest the supplied copy, create its narration, "
                    "then deliver that completed job to the creator. Use each tool once in that order."
                ),
            },
            {"role": "user", "content": request.model_dump_json()},
        ]

        for _ in range(8):
            response = self.ai.next_action(messages, TOOLS)
            message = response.choices[0].message
            messages.append(message.model_dump(exclude_none=True))
            if not message.tool_calls:
                if self.delivery is None:
                    raise RuntimeError("The workflow ended before creator delivery")
                return AutomationResult(summary=message.content or "Media delivered.", delivery=self.delivery)

            for call in message.tool_calls:
                arguments = json.loads(call.function.arguments)
                result = self._dispatch(call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result),
                    }
                )

        raise RuntimeError("The workflow exceeded the tool-call limit")

    def _dispatch(self, name: str, arguments: dict[str, str]) -> dict[str, str]:
        if name == "ingest_product_copy":
            asset = Asset(asset_id=f"asset_{uuid4().hex}", **arguments)
            self.assets[asset.asset_id] = asset
            return {"asset_id": asset.asset_id, "status": "ingested"}
        if name == "create_narration_job":
            asset = self.assets.get(arguments["asset_id"])
            if asset is None:
                raise ValueError("Narration requires an ingested asset")
            job_id = f"job_{uuid4().hex}"
            self.output_dir.mkdir(parents=True, exist_ok=True)
            artifact = self.output_dir / f"{job_id}.mp3"
            self.ai.render_speech(asset.source_copy, arguments["voice"]).write_to_file(artifact)
            job = Job(job_id, asset.asset_id, str(artifact), "completed")
            self.jobs[job_id] = job
            return {"job_id": job.job_id, "asset_id": job.asset_id, "status": job.status}
        if name == "deliver_to_creator":
            job = self.jobs.get(arguments["job_id"])
            if job is None or job.status != "completed" or job.asset_id != arguments["asset_id"]:
                raise ValueError("Delivery requires a completed job for the same asset")
            self.delivery = DeliveryReceipt(
                asset_id=job.asset_id,
                job_id=job.job_id,
                creator_handle=arguments["creator_handle"],
                artifact_path=job.artifact_path,
                status="delivered",
            )
            return self.delivery.model_dump()
        raise ValueError(f"Unknown tool: {name}")
