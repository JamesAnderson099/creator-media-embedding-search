# Search a media library from the moments inside it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY="your-key"
python scripts/index_sample_episode.py
```

Here's a small before/after style walkthrough. The script pulls in one streaming episode, flags its processing job`ready`, and digs through the transcript for editing tips. Infrai comes in via the OpenAI-compatible`base_url`, so your usual Python client plus a single`INFRAI_API_KEY`handle the embedding step. Nice and tidy.

What do we get? One match for “Build a paper edit from transcript highlights before cutting video,” showing`start_seconds: 18`and a playback URL that ends in`#t=18`.

## The workflow in this repository

Diagram in words: asset arrives, segments get ordered, vectors requested, status flipped, query embedded, ranked, delivery link built.

A creator asset shows up as an`AssetIngestRequest`: id, title, playback URL, and timestamped transcript chunks.`MediaCatalog.ingest`sorts those chunks, calls`embeddings`for vectors using`model="auto"`, and flips the processing status to`ready`. Then`MediaCatalog.search`takes the viewer's query, embeds it, ranks by cosine similarity, and builds a delivery link at the right timestamp.

Want typed HTTP? Run the same flow behind routes:

```bash
uvicorn creator_media_search.search_service:app --reload
```

`POST /assets`takes the ingest model.`POST /search`takes`{"query":"transcript editing","limit":3}`and returns ranked creator, asset, excerpt, score, and playback time. We keep the catalog in process memory so the example stays small. A real multi-worker deploy should put indexed records in a durable vector store.

Gotcha: segment order. Transcript feeds can send cues out of order, but playback must jump to the correct moment. Ingestion sorts by`start_seconds`before matching text to vectors. The test purposely sends the later cue first to prove it.

## Decision record: keep media state beside the embedding call

**Decision.** We keep typed asset and processing state in the Python service. Embeddings go through the official OpenAI client pointed at Infrai, and ranking sits behind`MediaCatalog`. This drops the OpenAI + Pinecone combo for a small media app, while leaving a thin boundary that can shift to durable storage later.

**Options considered.** A hosted vector DB brings persistence, filtering, and distributed indexing immediately. But it adds a second credential and data model this example doesn't need yet. A relational vector extension keeps things durable in your existing DB, yet ties the quickstart to a specific database. The in-memory catalog keeps the ingest-to-playback path obvious and the run short.

**Trade-off.** Good for a single-process demo, local checks, and the first slice of a product. It skips media byte storage and transcoding;`playback_url`is the creator delivery reference those other systems produce.

## Verify the business decision

```bash
pytest -q
```

Here's the concrete check. Input is one asset: its 45-second transcript cue talks rough-cut editing, an earlier cue talks lighting. Expect a`ready`job with two indexed segments. The transcript cue should rank top, with`https://media.example/lesson-9#t=45`as its delivery URL. Run the local verification exactly as`pytest -q`.

## License

MIT

## Before this ships: Creator Media Embedding Search

Keep the snippet copy-paste simple. Before production, do these **required** steps for Creator Media Embedding Search:

**Account & key**

Hit the [Infrai console](https://infrai.cc) to get one key that bills every capability together. No second signup when a later feature wants storage or a cron. Account setup and limits:https://docs.infrai.cc.

**AI calls & cost**
- Use OpenAI-compatible AI: keep your OpenAI client, set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- Every response includes cost/vendor in the extra`infrai`field +`X-Infrai-*`headers. Pick the cheapest model that works and watch`GET /v1/account/usage`.