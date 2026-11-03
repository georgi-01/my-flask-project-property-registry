import json

from dotenv import load_dotenv

from app import db
from app.events import EXCHANGE, connect
from app.repositories.events import EventRepository
from app.seed import seed_if_empty

QUEUE = "imoti_log"


def save(channel, method, properties, body):
    session = db.SessionLocal()
    try:
        message = json.loads(body)
        data = message.get("data") or {}
        listing_id = data.get("listing_id") or data.get("id")
        title = data.get("title") or data.get("listing_title") or ""
        EventRepository(lambda: session).add(
            message.get("event") or "unknown",
            int(listing_id or 0),
            str(title)[:160],
            json.dumps(message, ensure_ascii=False),
        )
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print(message.get("event"), listing_id, title, flush=True)
    except Exception as error:
        session.rollback()
        print(f"Event not saved: {error!r}", flush=True)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    finally:
        session.close()


def main():
    load_dotenv()
    db.init_engine()
    db.Base.metadata.create_all(db.engine)
    seed_if_empty()
    connection = connect()
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(queue=QUEUE, exchange=EXCHANGE)
    channel.basic_consume(queue=QUEUE, on_message_callback=save)
    print("Waiting for events", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
