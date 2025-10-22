"""
dead_letter_consumer.py
Consume mensajes de la exchange `dead_letters` para inspección manual.
"""
import json
import logging
from events import get_connection_params
import pika

logging.basicConfig(level=logging.INFO)


def process_dead_letter(ch, method, props, body):
    try:
        message = json.loads(body)
    except Exception:
        logging.error('DLQ: mensaje inválido')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    logging.warning(f"DLQ: mensaje recibido: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_dead_letter_consumer():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange='dead_letters', exchange_type='fanout', durable=True)

    result = ch.queue_declare(queue='dead_letter_queue', durable=True)
    ch.queue_bind(exchange='dead_letters', queue='dead_letter_queue')

    ch.basic_consume(queue='dead_letter_queue', on_message_callback=process_dead_letter)
    logging.info('🚨 Dead letter consumer esperando mensajes...')
    ch.start_consuming()


if __name__ == '__main__':
    start_dead_letter_consumer()
