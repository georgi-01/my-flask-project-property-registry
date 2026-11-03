import json
import os

import pika

EXCHANGE = "imoti"


def enabled():
    return os.environ.get("RABBITMQ_ENABLED", "1") != "0"


def connect():
    credentials = pika.PlainCredentials(os.environ["RABBITMQ_USER"], os.environ["RABBITMQ_PASSWORD"])
    parameters = pika.ConnectionParameters(
        host=os.environ["RABBITMQ_HOST"],
        credentials=credentials,
        socket_timeout=2,
        blocked_connection_timeout=2,
        connection_attempts=1,
        retry_delay=0,
    )
    return pika.BlockingConnection(parameters)


def publish(event, data):
    if not enabled():
        return
    message = {"event": event, "data": data}
    try:
        connection = connect()
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="fanout")
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key="",
            body=json.dumps(message, ensure_ascii=False),
        )
        connection.close()
    except Exception as error:
        print(f"Event {event} not sent: {error!r}", flush=True)
