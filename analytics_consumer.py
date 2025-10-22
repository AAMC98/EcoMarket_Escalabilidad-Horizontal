"""
analytics_consumer.py
Consumer simple que registra los eventos (y sirve como ejemplo para procesamiento adicional).
"""
import json
import logging
from events import get_connection_params
import pika

logging.basicConfig(level=logging.INFO)


def process_user_created_analytics(ch, method, props, body):
    try:
        message = json.loads(body)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    logging.info(f"📊 Analytics: evento recibido: {message.get('event_type')} id={message.get('event_id')}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_analytics_consumer():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Declarar exchange fanout
    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    # Declarar cola durable nombrada para analytics con DLQ
    args = {
        'x-dead-letter-exchange': 'dead_letters',
    }
    ch.queue_declare(queue='analytics_queue', durable=True, arguments=args)
    ch.queue_bind(exchange='user_events', queue='analytics_queue')

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue='analytics_queue', on_message_callback=process_user_created_analytics)

    logging.info('🎧 Analytics consumer esperando en queue analytics_queue...')
    ch.start_consuming()


if __name__ == '__main__':
    start_analytics_consumer()
