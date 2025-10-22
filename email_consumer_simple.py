"""
email_consumer_simple.py
Consumer simple que se bindea al exchange fanout `user_events` y procesa eventos UsuarioCreado.
Uso: python email_consumer_simple.py
"""
import os
import json
import logging
from events import get_connection_params, republish_to_retry_queue, publish_to_dead_letters
import pika

logging.basicConfig(level=logging.INFO)


MAX_RETRIES = 3
# Support FAST_RETRY for demos: if FAST_RETRY=1 then use small delays (ms)
if os.environ.get('FAST_RETRY', '') == '1':
    RETRY_DELAYS_MS = [2000, 4000, 6000]
else:
    # Default production-like delays
    RETRY_DELAYS_MS = [5000, 30000, 120000]  # 5s, 30s, 2min


def process_user_created_email(ch, method, props, body):
    try:
        message = json.loads(body)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if message.get('event_type') == 'UsuarioCreado' or 'email' in message:
        email = message.get('email')
        try:
            headers = props.headers or {}
            retries = int(headers.get('x-retries', 0))

            # Simulación de fallo controlado para demos: si simulate_fail True y no llegamos a max retries
            if message.get('simulate_fail') and retries < MAX_RETRIES:
                raise RuntimeError('Simulated failure (email)')

            logging.info(f"📧 Enviando email a {email}")
            # Lógica real de envío aquí
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logging.error('Error enviando email: %s', e)
            headers = props.headers or {}
            retries = int(headers.get('x-retries', 0))
            if retries >= MAX_RETRIES:
                logging.warning('Retries excedidos para mensaje; enviando a dead_letters')
                publish_to_dead_letters(message, headers=headers)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # Republish to retry queue with increasing delay
                new_headers = dict(headers)
                new_headers['x-retries'] = retries + 1
                delay = RETRY_DELAYS_MS[min(retries, len(RETRY_DELAYS_MS)-1)]
                republish_to_retry_queue('email_queue', message, headers=new_headers, delay_ms=delay)
                logging.info('Re-publicado a retry-queue (delay %d ms) retries=%d', delay, retries+1)
                ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_email_consumer():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    # Declarar cola durable nombrada para email con DLQ
    args = {
        'x-dead-letter-exchange': 'dead_letters',
    }
    ch.queue_declare(queue='email_queue', durable=True, arguments=args)
    ch.queue_bind(exchange='user_events', queue='email_queue')

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue='email_queue', on_message_callback=process_user_created_email)

    logging.info('🎧 Email consumer esperando en queue email_queue...')
    ch.start_consuming()


if __name__ == '__main__':
    start_email_consumer()
