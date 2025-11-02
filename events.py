"""events.py
Encapsula la lógica de publicación de eventos a RabbitMQ para el Taller 4.

Provee una función `publish_user_created` con reintentos simples.
"""

import os
import pika
import json
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def get_connection_params():
    """Construye ConnectionParameters leyendo variables de entorno con valores por defecto."""
    # In Docker Compose the RabbitMQ service is reachable via the service name 'rabbitmq'
    host = os.environ.get('RABBIT_HOST', 'rabbitmq')
    port = int(os.environ.get('RABBIT_PORT', '5672'))
    user = os.environ.get('RABBIT_USER', 'ecomarket_user')
    password = os.environ.get('RABBIT_PASS', 'ecomarket_password')
    return pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=pika.PlainCredentials(user, password),
        heartbeat=600,
        blocked_connection_timeout=300
    )


def publish_user_created(user_data: Dict[str, Any], max_retries: int = 5, backoff_seconds: float = 1.5) -> bool:
    """Publica un evento UsuarioCreado al exchange 'user_events'.

    Retorna True si el publish fue exitoso, False si falló después de reintentos.
    """
    body = {
        **user_data,
        "event_type": "UsuarioCreado"
    }

    attempt = 0
    while attempt < max_retries:
        try:
            params = get_connection_params()
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
            channel.basic_publish(
                exchange='user_events',
                routing_key='',
                body=json.dumps(body),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
            logger.info("Evento UsuarioCreado publicado: %s", body)
            return True
        except Exception as e:
            attempt += 1
            logger.error("Error publicando evento (intento %d/%d): %s", attempt, max_retries, e)
            time.sleep(backoff_seconds * attempt)

    logger.error("No se pudo publicar evento UsuarioCreado después de %d intentos", max_retries)
    return False


def republish_to_retry_queue(queue_name: str, message: Dict[str, Any], headers: Optional[Dict[str, Any]] = None, delay_ms: int = 5000) -> None:
    """Publica el mensaje en una retry-queue con TTL que dead-letters a la queue original.

    retry queue name: {queue_name}.retry.{delay_ms}
    La retry-queue tiene x-message-ttl = delay_ms y x-dead-letter-routing-key = queue_name
    """
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    retry_queue = f"{queue_name}.retry.{delay_ms}"
    args = {
        'x-dead-letter-exchange': '',
        'x-dead-letter-routing-key': queue_name,
        'x-message-ttl': delay_ms,
    }
    ch.queue_declare(queue=retry_queue, durable=True, arguments=args)

    props = pika.BasicProperties(headers=headers or {}, delivery_mode=2, content_type='application/json')
    ch.basic_publish(exchange='', routing_key=retry_queue, body=json.dumps(message), properties=props)
    conn.close()


def publish_to_dead_letters(message: Dict[str, Any], headers: Optional[Dict[str, Any]] = None) -> None:
    """Publica un mensaje a la exchange `dead_letters` para inspección/operaciones manuales."""
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange='dead_letters', exchange_type='fanout', durable=True)
    props = pika.BasicProperties(headers=headers or {}, delivery_mode=2, content_type='application/json')
    ch.basic_publish(exchange='dead_letters', routing_key='', body=json.dumps(message), properties=props)
    conn.close()
