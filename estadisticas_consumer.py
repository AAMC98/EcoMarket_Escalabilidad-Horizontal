"""estadisticas_consumer.py
Consumer opcional que cuenta usuarios nuevos a partir del evento UsuarioCreado.

Mantiene un contador en memoria (demostración). En producción usar persistencia (Redis/DB).
"""
import pika
import json
import logging
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_counter = 0
_lock = Lock()


def get_connection_params():
    return pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('ecomarket_user', 'ecomarket_password'),
        heartbeat=600,
        blocked_connection_timeout=300
    )


def on_message(ch, method, properties, body):
    global _counter
    try:
        evt = json.loads(body)
    except Exception as e:
        logger.error("JSON inválido en estadisticas_consumer: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if 'id' not in evt:
        logger.error("Evento sin id: %s", evt)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    with _lock:
        _counter += 1
        current = _counter

    logger.info("[ESTADISTICAS] Nuevo usuario contado. Total: %d", current)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    params = get_connection_params()
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
    channel.queue_declare(queue='estadisticas_user_queue', durable=True, arguments={
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': 'estadisticas_user_dlq'
    })
    channel.queue_declare(queue='estadisticas_user_dlq', durable=True)
    channel.queue_bind(exchange='user_events', queue='estadisticas_user_queue')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='estadisticas_user_queue', on_message_callback=on_message)

    logger.info("Esperando eventos en 'estadisticas_user_queue' (CTRL+C para salir)")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Cerrando consumidor de estadísticas...")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == '__main__':
    main()
