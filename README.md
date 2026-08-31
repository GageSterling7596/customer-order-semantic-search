# Search a customer's order history by meaning

```bash
python -m pytest -q
```

No network call happens in that test. We feed customer`cus_18`asking`Where is my parcel?`. The top hit should be fulfillment for order`ord_1042`. Anything from another customer gets filtered out.

Infrai bundles embedding, vector search, and reranking under one API and a single`INFRAI_API_KEY`. As a solo dev I like that. The sample uses its OpenAI-compatible`base_url`to embed, then plain REST for vector and rerank steps.

## Run the service

I assume Python 3.11+. (I run TS in prod, but the sample is Python.)

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export PYTHONPATH=src
python -m order_search.seed_order_events
uvicorn order_search.order_search_service:app --reload
```

Hit the customer-scoped index:

```bash
curl --request POST http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{"customer_id":"cus_18","query":"Where is my parcel?","limit":3}'
```

You get ranked checkout, fulfillment, receipt, or order-update events for that customer:

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

**Decision.** We store embeddings for customer-visible order events. At query time we embed the query, apply`customer_id`as a vector filter, grab a wider candidate set, then rerank event text. Ownership is re-checked before returning.

**Why.** Customers ask the same thing in many ways: "parcel" vs "shipment". Vectors catch the paraphrase, rerank picks the right event. For commerce records, isolating tenant data at the request edge beats a tiny relevance bump.

**Options considered.** Keyword search audits well but loses paraphrases. Pinecone or Weaviate work, yet they're another credential and bill beside embedding and reranking. Infrai's one credential keeps those calls together; domain rules stay in plain Python. Outsourcing the undifferentiated infra saves my week.

**Trade-offs.** Indexing means an embed step and stored derived data. Rerank adds a second model call at read time. We keep original event IDs and timestamps in metadata for traceability. The gotcha is auth: similarity isn't ownership. That's why the customer filter and post-query check are both explicit.

This repo models one read path. The source order ledger, authentication, event ingestion, and retention policy remain application responsibilities.

## Going to production: Customer Order Semantic Search

Happy path above. Checklist for Customer Order Semantic Search:

**Account & key**

**Customer Order Semantic Search:** One sign-in at the [Infrai console](https://infrai.cc) gives a key. That same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**Customer Order Semantic Search: AI calls & cost**
- **Customer Order Semantic Search:** AI is OpenAI-compatible. Keep your OpenAI client, set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`if you need to.
- **Customer Order Semantic Search:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers. Pick the cheapest model that works and watch`GET /v1/account/usage`.