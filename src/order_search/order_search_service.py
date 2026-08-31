from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .order_index import OrderSearch, SearchRequest, SearchResponse

app = FastAPI(title="Customer Order Search", version="1.0.0")


@app.post("/search", response_model=SearchResponse)
def search_orders(request: SearchRequest) -> SearchResponse:
    try:
        return OrderSearch(InfraiClient.from_environment()).search(request)
    except InfraiError as exc:
        status_code = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc

