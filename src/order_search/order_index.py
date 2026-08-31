from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field


class OrderEvent(BaseModel):
    event_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    event_type: str = Field(pattern="^(checkout|fulfillment|receipt|order_update)$")
    message: str = Field(min_length=1, max_length=2000)
    occurred_at: str = Field(min_length=1)


class SearchRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class SearchHit(BaseModel):
    event_id: str
    order_id: str
    event_type: str
    message: str
    occurred_at: str
    relevance: float


class SearchResponse(BaseModel):
    customer_id: str
    hits: list[SearchHit]


class SearchBackend(Protocol):
    def embed(self, text: str, model: str) -> list[float]:
        raise AssertionError

    def query(
        self, collection: str, embedding: list[float], customer_id: str, top_k: int
    ) -> dict[str, Any]:
        raise AssertionError

    def rerank(self, query: str, candidates: list[str], top_k: int) -> dict[str, Any]:
        raise AssertionError


@dataclass(frozen=True)
class OrderSearch:
    backend: SearchBackend
    collection: str = "commerce-order-events"
    embedding_model: str = "text-embedding-3-small"

    def search(self, request: SearchRequest) -> SearchResponse:
        embedding = self.backend.embed(request.query, self.embedding_model)
        query_data = self.backend.query(
            self.collection, embedding, request.customer_id, request.limit * 3
        )
        matches = query_data.get("matches", [])
        candidates = [self._candidate_text(match["metadata"]) for match in matches]
        if not candidates:
            return SearchResponse(customer_id=request.customer_id, hits=[])

        reranked = self.backend.rerank(request.query, candidates, request.limit)
        hits: list[SearchHit] = []
        for item in reranked.get("results", []):
            match = matches[int(item["index"])]
            metadata = match["metadata"]
            # Defense in depth: tenancy is checked even though the vector query is filtered.
            if metadata["customer_id"] != request.customer_id:
                continue
            hits.append(
                SearchHit(
                    event_id=match["id"],
                    order_id=metadata["order_id"],
                    event_type=metadata["event_type"],
                    message=metadata["message"],
                    occurred_at=metadata["occurred_at"],
                    relevance=float(item["score"]),
                )
            )
        return SearchResponse(customer_id=request.customer_id, hits=hits)

    @staticmethod
    def _candidate_text(metadata: dict[str, Any]) -> str:
        return f'{metadata["event_type"]}: {metadata["message"]}'
