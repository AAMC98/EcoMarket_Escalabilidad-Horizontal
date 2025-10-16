"""notificaciones_consumer.py
Consumer que se suscribe al evento UsuarioCreado y simula el envío de un email.

Funcionalidades mínimas:
- Declara exchange 'user_events' tipo fanout
- Declara cola durable 'notificaciones_user_queue' ligada al exchange
- Valida campos básicos (id, nombre, email)
- Usa DLQ para mensajes inválidos
"""
import pika
import json
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")


def get_connection_params():
    return pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('ecomarket_user', 'ecomarket_password'),
        heartbeat=600,
        blocked_connection_timeout=300
    )


def validar_evento(evt: dict) -> bool:
    if not isinstance(evt, dict):
        return False
    required = ('id', 'nombre', 'email')
    if not all(k in evt for k in required):
        return False
    if not EMAIL_RE.match(evt.get('email', '')):
        return False
    return True


def on_message(ch, method, properties, body):
    try:
        evt = json.loads(body)
    except Exception as e:
        logger.error("JSON inválido: %s", e)
        # mensaje corrupto -> no requeue -> direct to DLQ (via queue args)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    if not validar_evento(evt):
        logger.error("Evento inválido recibido: %s", evt)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    # Simular envío de correo
    logger.info("[NOTIFICACIONES] Enviando email de bienvenida a %s <%s>", evt['nombre'], evt['email'])
    print(f"[EMAIL SIMULADO] Hola {evt['nombre']} <{evt['email']}> — ¡Bienvenido a EcoMarket!")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    params = get_connection_params()
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Exchange fanout
    channel.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    # Declarar cola durable con DLQ
    channel.queue_declare(
        queue='notificaciones_user_queue',
        durable=True,
        arguments={
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': 'notificaciones_user_dlq'
        }
    )
    # Declarar DLQ también
    channel.queue_declare(queue='notificaciones_user_dlq', durable=True)

    channel.queue_bind(exchange='user_events', queue='notificaciones_user_queue')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='notificaciones_user_queue', on_message_callback=on_message)

    logger.info("Esperando mensajes en 'notificaciones_user_queue' (CTRL+C para salir)")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Cerrando consumidor de notificaciones...")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == '__main__':
    main()
