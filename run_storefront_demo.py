from pathlib import Path

from storefront_media.media_coordinator import InfraiMediaAI, MediaCoordinator
from storefront_media.models import MediaAutomationRequest


request = MediaAutomationRequest(
    product_sku="LINEN-TOTE-NAVY",
    campaign_name="Weekend market edit",
    source_copy="The navy linen tote carries a laptop, market finds, and the small things you reach for at checkout.",
    creator_handle="@marketdesk",
)

result = MediaCoordinator(InfraiMediaAI(), Path("artifacts")).run(request)
print(result.model_dump_json(indent=2))

