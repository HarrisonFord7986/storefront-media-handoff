from typing import Literal

from pydantic import BaseModel, Field


class MediaAutomationRequest(BaseModel):
    product_sku: str = Field(min_length=1)
    campaign_name: str = Field(min_length=1)
    source_copy: str = Field(min_length=1)
    creator_handle: str = Field(min_length=1)
    voice: str = "alloy"


class DeliveryReceipt(BaseModel):
    asset_id: str
    job_id: str
    creator_handle: str
    artifact_path: str
    status: Literal["delivered"]


class AutomationResult(BaseModel):
    summary: str
    delivery: DeliveryReceipt

