from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Literal, Protocol

from pydantic import BaseModel, Field, model_validator


class TranscriptSegment(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    text: str = Field(min_length=1)

    @model_validator(mode="after")
    def end_follows_start(self) -> "TranscriptSegment":
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must follow start_seconds")
        return self


class AssetIngestRequest(BaseModel):
    asset_id: str = Field(min_length=1)
    creator_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    playback_url: str = Field(min_length=1)
    segments: list[TranscriptSegment] = Field(min_length=1)


class MediaSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=20)


class SearchHit(BaseModel):
    asset_id: str
    title: str
    creator_id: str
    start_seconds: float
    playback_url: str
    excerpt: str
    score: float


class ProcessingReceipt(BaseModel):
    asset_id: str
    job_state: Literal["ready"]
    indexed_segments: int


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError("protocol method")


@dataclass(frozen=True)
class IndexedSegment:
    asset_id: str
    creator_id: str
    title: str
    playback_url: str
    segment: TranscriptSegment
    embedding: list[float]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions must match")
    denominator = sqrt(sum(x * x for x in left)) * sqrt(sum(x * x for x in right))
    return sum(x * y for x, y in zip(left, right, strict=True)) / denominator if denominator else 0.0


class MediaCatalog:
    def __init__(self, embedder: Embedder) -> None:
        self._embedder = embedder
        self._segments: list[IndexedSegment] = []

    def ingest(self, asset: AssetIngestRequest) -> ProcessingReceipt:
        ordered = sorted(asset.segments, key=lambda segment: segment.start_seconds)
        vectors = self._embedder.embed([segment.text for segment in ordered])
        if len(vectors) != len(ordered):
            raise ValueError("embedding count must match transcript segments")

        self._segments = [item for item in self._segments if item.asset_id != asset.asset_id]
        self._segments.extend(
            IndexedSegment(
                asset_id=asset.asset_id,
                creator_id=asset.creator_id,
                title=asset.title,
                playback_url=asset.playback_url,
                segment=segment,
                embedding=vector,
            )
            for segment, vector in zip(ordered, vectors, strict=True)
        )
        return ProcessingReceipt(asset_id=asset.asset_id, job_state="ready", indexed_segments=len(ordered))

    def search(self, request: MediaSearchRequest) -> list[SearchHit]:
        query_vector = self._embedder.embed([request.query])[0]
        ranked = sorted(
            self._segments,
            key=lambda item: cosine_similarity(query_vector, item.embedding),
            reverse=True,
        )[: request.limit]
        return [
            SearchHit(
                asset_id=item.asset_id,
                title=item.title,
                creator_id=item.creator_id,
                start_seconds=item.segment.start_seconds,
                playback_url=f"{item.playback_url}#t={item.segment.start_seconds:g}",
                excerpt=item.segment.text,
                score=round(cosine_similarity(query_vector, item.embedding), 6),
            )
            for item in ranked
        ]
