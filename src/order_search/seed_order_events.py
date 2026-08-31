from __future__ import annotations

from .infrai_client import InfraiClient
from .order_index import OrderEvent

EVENTS = [
    OrderEvent(
        event_id="evt_checkout_1042",
        customer_id="cus_18",
        order_id="ord_1042",
        event_type="checkout",
        message="Card accepted and order confirmed.",
        occurred_at="2026-08-25T09:30:00Z",
    ),
    OrderEvent(
        event_id="evt_fulfillment_1042",
        customer_id="cus_18",
        order_id="ord_1042",
        event_type="fulfillment",
        message="Parcel handed to the carrier with tracking reference ZX42.",
        occurred_at="2026-08-26T03:10:00Z",
    ),
    OrderEvent(
        event_id="evt_receipt_1042",
        customer_id="cus_18",
        order_id="ord_1042",
        event_type="receipt",
        message="Receipt issued for the completed card payment.",
        occurred_at="2026-08-25T09:31:00Z",
    ),
]


def main() -> None:
    client = InfraiClient.from_environment()
    embedded = [(event, client.embed(event.message, "text-embedding-3-small")) for event in EVENTS]
    client.create_collection("commerce-order-events", len(embedded[0][1]))
    vectors = [
        {
            "id": event.event_id,
            "values": vector,
            "metadata": event.model_dump(exclude={"event_id"}),
        }
        for event, vector in embedded
    ]
    client.upsert("commerce-order-events", vectors)
    print(f"Indexed {len(vectors)} customer order events.")


if __name__ == "__main__":
    main()

