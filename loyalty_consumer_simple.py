"""
loyalty_consumer_simple.py
Consumer simple que activa lealtad al recibir UsuarioCreado.
Uso: python loyalty_consumer_simple.py
"""
import json
import logging
from events import get_connection_params, republish_to_retry_queue, publish_to_dead_letters
import pika

logging.basicConfig(level=logging.INFO)


MAX_RETRIES = 3
RETRY_DELAYS_MS = [5000, 30000, 120000]


def process_user_created_loyalty(ch, method, props, body):
    try:
        message = json.loads(body)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if message.get('event_type') == 'UsuarioCreado' or 'user_id' in message:
        user_id = message.get('user_id') or message.get('id')
        try:
            headers = props.headers or {}
            retries = int(headers.get('x-retries', 0))

            if message.get('simulate_fail') and retries < MAX_RETRIES:
                raise RuntimeError('Simulated failure (loyalty)')

            logging.info(f"🎁 Activando lealtad para {user_id}")
            # Lógica de activación aquí
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error('Error activando lealtad: %s', e)
            headers = props.headers or {}
            retries = int(headers.get('x-retries', 0))
            if retries >= MAX_RETRIES:
                logging.warning('Retries excedidos para mensaje; enviando a dead_letters')
                publish_to_dead_letters(message, headers=headers)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                new_headers = dict(headers)
                new_headers['x-retries'] = retries + 1
                delay = RETRY_DELAYS_MS[min(retries, len(RETRY_DELAYS_MS)-1)]
                republish_to_retry_queue('loyalty_queue', message, headers=new_headers, delay_ms=delay)
                logging.info('Re-publicado a retry-queue (delay %d ms) retries=%d', delay, retries+1)
                ch.basic_ack(delivery_tag=method.delivery_tag)
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
