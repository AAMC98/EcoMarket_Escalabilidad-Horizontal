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
        try:
            logging.info(f"📧 Enviando email a {email}")
            # Simular fallo aleatorio para prueba (podrías quitar esto en prod)
            # Aquí iría la lógica real de envío (SMTP, provider API, etc.)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error('Error enviando email: %s', e)
            # Manejo de reintentos simple: usar header x-retries
            headers = props.headers or {}
            retries = int(headers.get('x-retries', 0))
            if retries >= 3:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                # Republishing con header incrementado
                new_headers = dict(headers)
                new_headers['x-retries'] = retries + 1
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                # En un sistema real haríamos republish a la misma queue con delay
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
