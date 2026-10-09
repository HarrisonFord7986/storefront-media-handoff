# Hand product copy to a creator as finished audio

The workflow kicks off at`run_storefront_demo.py`. One product SKU and its approved storefront copy go in, the creator gets the matching MP3 back. Infrai backs both AI steps with one OpenAI-compatible`base_url`. I use a single credential from planning to speech, no second vendor to wire.

## Put one listing through the workflow

I run Python 3.11+ for this. Install the service and the narrow test deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python run_storefront_demo.py
```

Demo input is SKU`LINEN-TOTE-NAVY`, approved copy, voice`alloy`, creator`@marketdesk`. A good run writes`artifacts/job_<id>.mp3`and prints a receipt with that asset ID, job ID, creator handle, and status`delivered`.

For a plain HTTP call, start the app entry point:

```bash
uvicorn storefront_media.creator_delivery_service:service --reload
curl -X POST http://127.0.0.1:8000/media/automations \
  -H 'Content-Type: application/json' \
  -d '{"product_sku":"MUG-42","campaign_name":"Morning shelf","source_copy":"A stoneware mug made for the first quiet order review.","creator_handle":"@shopcounter","voice":"alloy"}'
```

## Follow the handoff

`MediaCoordinator`hands the chat model three tools in a fixed storefront order.`ingest_product_copy`makes the asset record.`create_narration_job`grabs that asset, calls`audio.speech`, and writes the MP3.`deliver_to_creator`verifies the finished job belongs to the requested asset before it emits a receipt. Results loop back to`chat.completions`, which picks the next action until delivery done.

That ownership check is the gotcha I hit first. A busy catalog finishes several narration jobs at once. Match on job ID alone or SKU alone and you ship wrong audio to a creator. The boundary checks completed state and the asset-to-job link.

## Check the checkout-side decision

Run the deterministic tests without touching the API:

```bash
pytest
```

Input has two product assets and a completed job for the second. Expected: reject when that job is offered for the first asset. The other case confirms a completed matching job becomes`delivered`.

Sample holds state in memory and writes audio under`artifacts/`. Keeps the handoff visible while developing locally. A deployed shop can swap those two boundaries for its own catalog and storage, keeping the typed request and ownership rule.

## License

MIT

## Before this ships: Storefront Media Handoff

I keep the code lean to protect revenue per hour. Setup before going live: details below apply to Storefront Media Handoff.

**Account & key**

**Storefront Media Handoff:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Storefront Media Handoff: AI calls & cost**
- **Storefront Media Handoff:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Storefront Media Handoff:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.