"""
loyalty_consumer_simple.py
Consumer simple que activa lealtad al recibir UsuarioCreado.
Uso: python loyalty_consumer_simple.py
"""
import json
import logging
from events import get_connection_params
import pika

logging.basicConfig(level=logging.INFO)


def process_user_created_loyalty(ch, method, props, body):
    try:
        message = json.loads(body)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if message.get('event_type') == 'UsuarioCreado' or 'user_id' in message:
        user_id = message.get('user_id') or message.get('id')
        try:
            logging.info(f"🎁 Activando lealtad para {user_id}")
            # Lógica de activación aquí
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error('Error activando lealtad: %s', e)
            headers = props.headers or {}
            retries = int(headers.get('x-retries', 0))
            if retries >= 3:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                # En producción, re-publish con delay/backoff y header x-retries
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_loyalty_consumer():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    args = {
        'x-dead-letter-exchange': 'dead_letters',
    }
    ch.queue_declare(queue='loyalty_queue', durable=True, arguments=args)
    ch.queue_bind(exchange='user_events', queue='loyalty_queue')

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue='loyalty_queue', on_message_callback=process_user_created_loyalty)

    logging.info('🎧 Loyalty consumer esperando en queue loyalty_queue...')
    ch.start_consuming()


if __name__ == '__main__':
    start_loyalty_consumer()
