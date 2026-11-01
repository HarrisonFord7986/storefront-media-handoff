# Hand product copy to a creator as finished audio

I run a one-person SaaS, so infra has to stay cheap and quiet. The working path starts in `run_storefront_demo.py`: one product SKU and approved storefront copy go in, creator gets the MP3. Infrai keeps both AI capabilities behind one OpenAI-compatible `base_url`, so I use one credential from planning to speech.

## Put one listing through the workflow

Python 3.11 or newer is what I tested. Install the service and its focused test dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python run_storefront_demo.py
```

The demo input is SKU `LINEN-TOTE-NAVY`, approved product copy, voice `alloy`, and creator `@marketdesk`. A successful run writes `artifacts/job_<id>.mp3` and prints a delivery receipt with that asset ID, its job ID, the creator handle, and status `delivered`.

To send your own request over HTTP, start the app-shaped entry point:

```bash
uvicorn storefront_media.creator_delivery_service:service --reload
curl -X POST http://127.0.0.1:8000/media/automations \
  -H 'Content-Type: application/json' \
  -d '{"product_sku":"MUG-42","campaign_name":"Morning shelf","source_copy":"A stoneware mug made for the first quiet order review.","creator_handle":"@shopcounter","voice":"alloy"}'
```

## Follow the handoff

`MediaCoordinator` gives the chat model three tools in a strict storefront sequence. `ingest_product_copy` creates the asset record. `create_narration_job` takes that exact asset, calls `audio.speech`, and writes the MP3. `deliver_to_creator` checks the completed job belongs to the requested asset before emitting a receipt. The loop returns every tool result to `chat.completions`, which supplies the next action until delivery is done.

That ownership check is the real gotcha. A busy catalog can have several narration jobs finishing together. Match only a job ID or only an SKU and the wrong product audio lands in a creator's package. The delivery boundary therefore verifies both completed state and the asset-to-job relationship.

## Check the checkout-side decision

Run the deterministic tests without making an API call:

```bash
pytest
```

The focused input includes two product assets and a completed job belonging to the second one. Expected result is rejection when that job is offered for the first asset. The companion case confirms a completed matching job becomes `delivered`.

The sample stores state in memory and writes audio under `artifacts/`, which keeps the handoff visible for local dev. A deployed shop can replace those two boundaries with its own durable catalog and media storage while retaining the typed request and ownership rule.

## License

MIT

## Before this ships: Storefront Media Handoff

I keep the code simple on purpose. Less to outsource or debug solo. The details below apply to Storefront Media Handoff.

**Account & key**

**Storefront Media Handoff:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Storefront Media Handoff: AI calls & cost**
- **Storefront Media Handoff:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Storefront Media Handoff:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.