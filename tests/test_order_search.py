from order_search.order_index import OrderSearch, SearchRequest


class RecordedBackend:
    def __init__(self) -> None:
        self.customer_filter = ""

    def embed(self, text: str, model: str) -> list[float]:
        return [0.2, 0.8]

    def query(self, collection, embedding, customer_id, top_k):
        self.customer_filter = customer_id
        return {
            "matches": [
                {
                    "id": "evt_receipt",
                    "metadata": {
                        "customer_id": "cus_18",
                        "order_id": "ord_1042",
                        "event_type": "receipt",
                        "message": "Receipt issued after payment.",
                        "occurred_at": "2026-08-25T09:31:00Z",
                    },
                },
                {
                    "id": "evt_delivery",
                    "metadata": {
                        "customer_id": "cus_other",
                        "order_id": "ord_9999",
                        "event_type": "fulfillment",
                        "message": "Parcel delivered.",
                        "occurred_at": "2026-08-26T12:00:00Z",
                    },
                },
                {
                    "id": "evt_tracking",
                    "metadata": {
                        "customer_id": "cus_18",
                        "order_id": "ord_1042",
                        "event_type": "fulfillment",
                        "message": "Parcel handed to carrier ZX42.",
                        "occurred_at": "2026-08-26T03:10:00Z",
                    },
                },
            ]
        }

    def rerank(self, query, candidates, top_k):
        return {
            "results": [
                {"index": 2, "score": 0.96},
                {"index": 1, "score": 0.91},
                {"index": 0, "score": 0.52},
            ]
        }


def test_tracking_search_is_ranked_and_customer_scoped():
    backend = RecordedBackend()
    response = OrderSearch(backend).search(
        SearchRequest(customer_id="cus_18", query="Where is my parcel?", limit=3)
    )

    assert backend.customer_filter == "cus_18"
    assert [hit.event_id for hit in response.hits] == ["evt_tracking", "evt_receipt"]
    assert response.hits[0].order_id == "ord_1042"

