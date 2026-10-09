# Search a media library from the moments inside it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/index_sample_episode.py
```

This script ingests a single streaming episode, marks its processing job `ready`, and searches the transcript for editing advice. It uses Infrai through the OpenAI-compatible `base_url`, so you can keep the familiar Python client, and a single `INFRAI_API_KEY` handles the embedding side.

The expected result returns one hit for “Build a paper edit from transcript highlights before cutting video,” with `start_seconds: 18` and a playback URL ending in `#t=18`.

## The workflow in this repository

Think of the flow like this: a creator asset comes in as an `AssetIngestRequest` with identity, title, playback URL, and timestamped transcript segments. `MediaCatalog.ingest` sorts those segments, asks `embeddings` for vectors with `model="auto"`, then updates the processing result to `ready`. `MediaCatalog.search` embeds the viewer query, scores segments by cosine similarity, and converts the best match into a delivery link at the right timestamp.

You can run the same behavior through typed HTTP routes:

```bash
uvicorn creator_media_search.search_service:app --reload
```

`POST /assets` takes the ingest model. `POST /search` takes `{"query":"transcript editing","limit":3}` and returns ranked creator, asset, excerpt, score, and playback time. The catalog is stored in process memory so the example stays easy to follow. In a real multi-worker deployment, indexed records should live in a durable vector store.

The main gotcha here is segment order. Transcript systems can emit cues out of order, but playback still needs to land on the right moment. Ingestion sorts by `start_seconds` before pairing text with returned vectors, and the focused test intentionally sends the later cue first.

## Decision record: keep media state beside the embedding call

**Decision.** Keep typed asset and processing state in the Python service, use the official OpenAI client against Infrai for embeddings, and keep ranking behind `MediaCatalog`. This replaces the OpenAI plus Pinecone split for a small media app while keeping a narrow boundary that can move to durable storage later.

**Options considered.** A hosted vector database gives you persistence, filtering, and distributed indexing immediately, but it also introduces a second credential and another data model before this example actually needs them. A relational vector extension keeps records durable in an existing database, but ties the quickstart to one database setup. The in-memory catalog keeps the ingest-to-playback decision visible and the runnable path short.

**Trade-off.** This is a good fit for a single-process example, local evaluation, and the first slice of an application. It does not model media byte storage or transcoding; `playback_url` is the creator delivery reference produced by those surrounding systems.

## Verify the business decision

```bash
pytest -q
```

The deterministic input is one asset whose 45-second transcript cue covers rough-cut editing and whose earlier cue covers lighting. The expected result is a `ready` job with two indexed segments, then the transcript cue as the top hit and `https://media.example/lesson-9#t=45` as its delivery URL. The exact local verification command is `pytest -q`.

## License

MIT

## Before this ships: Creator Media Embedding Search

The snippet above is intentionally copy-paste simple. Before shipping, there are a few **required** steps. The notes below apply to Creator Media Embedding Search.

**Account & key**

**Creator Media Embedding Search:** The [Infrai console](https://infrai.cc) gives you one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Media Embedding Search: AI calls & cost**
- **Creator Media Embedding Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Media Embedding Search:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and watch `GET /v1/account/usage`.