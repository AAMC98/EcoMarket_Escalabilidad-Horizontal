"""
email_consumer_simple.py
Consumer simple que se bindea al exchange fanout `user_events` y procesa eventos UsuarioCreado.
Uso: python email_consumer_simple.py
"""
import json
import logging
from events import get_connection_params
import pika

logging.basicConfig(level=logging.INFO)


def process_user_created_email(ch, method, props, body):
    try:
        message = json.loads(body)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if message.get('event_type') == 'UsuarioCreado' or 'email' in message:
        email = message.get('email')
        logging.info(f"📧 Enviando email a {email}")
        # Aquí iría la lógica real de envío (SMTP, provider API, etc.)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_email_consumer():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    # Cola exclusiva (auto-delete cuando el consumer se desconecta)
    result = ch.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    ch.queue_bind(exchange='user_events', queue=queue_name)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=queue_name, on_message_callback=process_user_created_email)

    logging.info('🎧 Email consumer esperando eventos en exchange user_events...')
    ch.start_consuming()


if __name__ == '__main__':
    start_email_consumer()
