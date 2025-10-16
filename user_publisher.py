"""user_publisher.py
Script mínimo para publicar eventos UsuarioCreado en RabbitMQ (exchange fanout 'user_events').

Usa las mismas credenciales y parámetros que el proyecto existente.
"""
import pika
import json
import uuid
from datetime import datetime
import argparse


def get_connection_params():
    return pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('ecomarket_user', 'ecomarket_password'),
        heartbeat=600,
        blocked_connection_timeout=300
    )


def publish_usuario_creado(user_id: str, nombre: str, email: str):
    params = get_connection_params()
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    # declaramos exchange fanout durable
    channel.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    event = {
        'id': user_id,
        'nombre': nombre,
        'email': email,
        'created_at': datetime.utcnow().isoformat()
    }

    channel.basic_publish(
        exchange='user_events',
        routing_key='',
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2)  # persistent
    )
    connection.close()
    print("[PUBLISH] UsuarioCreado publicado:", event)


def main():
    parser = argparse.ArgumentParser(description='Publicar evento UsuarioCreado a RabbitMQ')
    parser.add_argument('--id', help='ID del usuario (UUID)', default=str(uuid.uuid4()))
    parser.add_argument('--nombre', help='Nombre del usuario', default='Usuario Demo')
    parser.add_argument('--email', help='Email del usuario', default='demo@example.com')
    args = parser.parse_args()

    publish_usuario_creado(args.id, args.nombre, args.email)


if __name__ == '__main__':
    main()
