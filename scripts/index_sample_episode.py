import json

from creator_media_search.infrai_embeddings import InfraiEmbeddings
from creator_media_search.media_catalog import AssetIngestRequest, MediaCatalog, MediaSearchRequest


def main() -> None:
    catalog = MediaCatalog(InfraiEmbeddings())
    receipt = catalog.ingest(
        AssetIngestRequest.model_validate(
            {
                "asset_id": "episode-17",
                "creator_id": "creator-42",
                "title": "Editing a documentary interview",
                "playback_url": "https://media.example/episode-17",
                "segments": [
                    {"start_seconds": 0, "end_seconds": 18, "text": "Set the interview scene and label every camera source."},
                    {"start_seconds": 18, "end_seconds": 43, "text": "Build a paper edit from transcript highlights before cutting video."},
                    {"start_seconds": 43, "end_seconds": 68, "text": "Deliver a review link to the director and collect timecoded notes."},
                ],
            }
        )
    )
    hits = catalog.search(MediaSearchRequest(query="How do I edit from transcript highlights?", limit=1))
    print(json.dumps({"processing": receipt.model_dump(), "hits": [hit.model_dump() for hit in hits]}, indent=2))


if __name__ == "__main__":
    main()
