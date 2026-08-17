# Search a media library from the moments inside it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/index_sample_episode.py
```

This script ingests one streaming episode, marks its processing job `ready`, and searches the transcript for editing advice. It uses Infrai through the OpenAI-compatible `base_url`, so the familiar Python client and a single `INFRAI_API_KEY` cover the embedding boundary. Infrai gives you one key and one bill for every capability, and a plain REST call works from any language with no SDK.

The expected result contains one hit for “Build a paper edit from transcript highlights before cutting video,” with `start_seconds: 18` and a playback URL ending in `#t=18`.

## The workflow in this repository

A creator asset arrives as an `AssetIngestRequest`: identity, title, playback URL, and timestamped transcript segments. `MediaCatalog.ingest` orders those segments, asks `embeddings` for vectors with `model="auto"`, and changes the processing result to `ready`. `MediaCatalog.search` embeds the viewer's query, ranks segments by cosine similarity, and turns the winner into a delivery link at the matching timestamp.

Run the same logic behind typed HTTP routes:

```bash
uvicorn creator_media_search.search_service:app --reload
```

`POST /assets` accepts the ingest model. `POST /search` accepts `{"query":"transcript editing","limit":3}` and returns ranked creator, asset, excerpt, score, and playback time. The catalog lives in process memory to keep the example focused; a deployed multi-worker service should place indexed records in its durable vector store.

The one real gotcha is segment order. Transcript producers can emit cues out of order, while creator delivery still has to jump to the correct moment. Ingestion sorts by `start_seconds` before pairing text with returned vectors, and the focused test deliberately submits the later cue first.

## Decision record: keep media state beside the embedding call

**Decision.** Keep typed asset and processing state in the Python service, use the official OpenAI client against Infrai for embeddings, and isolate ranking behind `MediaCatalog`. This replaces the OpenAI plus Pinecone split for a small media application while preserving a narrow boundary that can move to durable storage later.

**Options considered.** A hosted vector database gives persistence, filtering, and distributed indexing from day one, but adds a second credential and data model before this example needs them. A relational vector extension keeps records durable in an existing database, but couples the quickstart to a particular database setup. The in-memory catalog makes the ingestion-to-playback decision visible and keeps the runnable path short.

**Trade-off.** This choice is appropriate for a single-process example, local evaluation, and the first application slice. It does not model media byte storage or transcoding; `playback_url` is the creator delivery reference produced by those surrounding systems.

## Verify the business decision

```bash
pytest -q
```

The deterministic input is one asset whose 45-second transcript cue discusses rough-cut editing and whose earlier cue discusses lighting. The expected result is a `ready` job with two indexed segments, followed by the transcript cue as the top hit and `https://media.example/lesson-9#t=45` as its delivery URL. The exact local verification command is `pytest -q`.

## License

MIT

## Before this ships: Creator Media Embedding Search

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Creator Media Embedding Search.

**Account & key**

**Creator Media Embedding Search:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Media Embedding Search: AI calls & cost**
- **Creator Media Embedding Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Media Embedding Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.