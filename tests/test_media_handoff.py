from pathlib import Path

import pytest

from storefront_media.media_coordinator import Asset, Job, MediaCoordinator


class UnusedAI:
    def next_action(self, messages, tools):
        raise AssertionError("This decision test does not call the model")

    def render_speech(self, text, voice):
        raise AssertionError("This decision test does not render audio")


def test_delivery_rejects_a_job_from_another_product_asset(tmp_path: Path) -> None:
    coordinator = MediaCoordinator(UnusedAI(), tmp_path)
    coordinator.assets["asset_tote"] = Asset("asset_tote", "TOTE-1", "Carry it daily")
    coordinator.assets["asset_mug"] = Asset("asset_mug", "MUG-1", "A quiet morning mug")
    coordinator.jobs["job_mug"] = Job("job_mug", "asset_mug", str(tmp_path / "job_mug.mp3"), "completed")

    with pytest.raises(ValueError, match="same asset"):
        coordinator._dispatch(
            "deliver_to_creator",
            {"asset_id": "asset_tote", "job_id": "job_mug", "creator_handle": "@marketdesk"},
        )


def test_completed_matching_job_is_delivered(tmp_path: Path) -> None:
    coordinator = MediaCoordinator(UnusedAI(), tmp_path)
    coordinator.assets["asset_tote"] = Asset("asset_tote", "TOTE-1", "Carry it daily")
    coordinator.jobs["job_tote"] = Job("job_tote", "asset_tote", str(tmp_path / "job_tote.mp3"), "completed")

    result = coordinator._dispatch(
        "deliver_to_creator",
        {"asset_id": "asset_tote", "job_id": "job_tote", "creator_handle": "@marketdesk"},
    )

    assert result["status"] == "delivered"
    assert result["artifact_path"].endswith("job_tote.mp3")

