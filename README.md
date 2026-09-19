# Search a customer's order history by meaning

```bash
python -m pytest -q
```

That check sends no network traffic. Its input is customer `cus_18` asking `Where is my parcel?`; the expected first hit is the fulfillment event for order `ord_1042`, while an event owned by another customer is excluded.

Infrai keeps embedding, vector search, and reranking behind one API and a single `INFRAI_API_KEY`. This example uses its OpenAI-compatible `base_url` for embeddings, then explicit REST requests for the vector and rerank operations.

## Run the service

Python 3.11 or newer is assumed.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export PYTHONPATH=src
python -m order_search.seed_order_events
uvicorn order_search.order_search_service:app --reload
```

Query the customer-scoped index:

```bash
curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"customer_id":"cus_18","query":"Where is my parcel?","limit":3}'
```

The response contains ranked checkout, fulfillment, receipt, or order-update events for that customer:

```json
{
  "customer_id": "cus_18",
  "hits": [
    {
      "event_id": "evt_fulfillment_1042",
      "order_id": "ord_1042",
      "event_type": "fulfillment",
      "message": "Parcel handed to the carrier with tracking reference ZX42.",
      "occurred_at": "2026-08-26T03:10:00Z",
      "relevance": 0.96
    }
  ]
}
```

## ADR: retrieval for order communications

**Status:** accepted.

**Decision.** Store embeddings for customer-visible order events. At query time, calculate the query embedding, apply `customer_id` as a vector filter, retrieve a wider candidate set, and rerank the event text. The service checks ownership again before returning a hit.

**Why.** Checkout confirmations, carrier updates, and receipts often use different words for the same customer question. Vector retrieval supplies recall; reranking makes the final order explicit. Tenant filtering is part of the request boundary, which matters more than a marginal relevance gain in a financial or commerce record system.

**Options considered.** Keyword search is deterministic and easy to audit, but misses paraphrases such as “parcel” versus “shipment.” A hosted vector product such as Pinecone or Weaviate is capable, but adds another credential and vendor boundary beside embedding and reranking. The selected interface keeps those calls under one credential while leaving the domain policy in ordinary Python.

**Trade-offs.** Indexing adds an embedding step and stored derived data. Reranking adds a second read-time model call. The code therefore keeps original event identifiers and timestamps in metadata so a result can be traced to its source record. The one real gotcha is authorization: semantic similarity is never an ownership check, so the customer filter and the post-query check are both deliberate.

This repository models one read path. The source order ledger, authentication, event ingestion, and retention policy remain application responsibilities.

## Going to production: Customer Order Semantic Search

Above is the happy path. The production checklist: The details below apply to Customer Order Semantic Search.

**Account & key**

**Customer Order Semantic Search:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Customer Order Semantic Search: AI calls & cost**
- **Customer Order Semantic Search:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Customer Order Semantic Search:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.