from pathlib import Path

from fastapi import FastAPI, HTTPException

from .media_coordinator import InfraiMediaAI, MediaCoordinator
from .models import AutomationResult, MediaAutomationRequest

service = FastAPI(title="Storefront media handoff")


@service.post("/media/automations", response_model=AutomationResult)
def automate_media(request: MediaAutomationRequest) -> AutomationResult:
    try:
        return MediaCoordinator(InfraiMediaAI(), Path("artifacts")).run(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

