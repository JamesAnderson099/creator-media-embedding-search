from creator_media_search.media_catalog import AssetIngestRequest, MediaCatalog, MediaSearchRequest


class KeywordEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [
            [float("transcript" in text.lower()), float("lighting" in text.lower())]
            for text in texts
        ]


def test_search_delivers_the_best_segment_at_its_playback_time() -> None:
    catalog = MediaCatalog(KeywordEmbedder())
    receipt = catalog.ingest(
        AssetIngestRequest.model_validate(
            {
                "asset_id": "lesson-9",
                "creator_id": "creator-7",
                "title": "A practical rough cut",
                "playback_url": "https://media.example/lesson-9",
                "segments": [
                    {"start_seconds": 45, "end_seconds": 64, "text": "Use transcript highlights to assemble the rough cut."},
                    {"start_seconds": 8, "end_seconds": 25, "text": "Place the key light beside the camera."},
                ],
            }
        )
    )

    hits = catalog.search(MediaSearchRequest(query="transcript editing", limit=1))

    assert receipt.model_dump() == {"asset_id": "lesson-9", "job_state": "ready", "indexed_segments": 2}
    assert hits[0].excerpt == "Use transcript highlights to assemble the rough cut."
    assert hits[0].playback_url == "https://media.example/lesson-9#t=45"
    assert hits[0].score == 1.0
