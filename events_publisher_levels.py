"""
Script para demo: publisher en 3 niveles (simple, persistente, robusto con confirms).
Uso: python events_publisher_levels.py --level 1 --nombre "Ana" --email "ana@example.com"
"""
import argparse
import json
import uuid
from datetime import datetime
import time
import pika


def get_conn_params():
    return pika.ConnectionParameters('localhost')


def publish_level1(user_data: dict):
    conn = pika.BlockingConnection(get_conn_params())
    ch = conn.channel()
    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
    ch.basic_publish(exchange='user_events', routing_key='', body=json.dumps(user_data))
    conn.close()
    print('Publicado (nivel 1)')


def publish_level2_persistent(user_data: dict):
    message = {**user_data, 'event_type': 'UsuarioCreado', 'event_id': str(uuid.uuid4()), 'timestamp': datetime.utcnow().isoformat()}
    conn = pika.BlockingConnection(get_conn_params())
    ch = conn.channel()
    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
    ch.basic_publish(exchange='user_events', routing_key='', body=json.dumps(message), properties=pika.BasicProperties(delivery_mode=2, content_type='application/json'))
    conn.close()
    print('Publicado (nivel 2 persistent)')


def publish_level3_confirm(user_data: dict, max_retries: int = 3):
    message = {**user_data, 'event_type': 'UsuarioCreado', 'event_id': str(uuid.uuid4()), 'timestamp': datetime.utcnow().isoformat()}
    attempt = 0
    while attempt < max_retries:
        try:
            conn = pika.BlockingConnection(get_conn_params())
            ch = conn.channel()
            ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
            ch.confirm_delivery()
            ch.basic_publish(exchange='user_events', routing_key='', body=json.dumps(message), properties=pika.BasicProperties(delivery_mode=2, content_type='application/json'), mandatory=True)
            conn.close()
            print(f'Publicado y confirmado (nivel 3) {message["event_id"]}')
            return True
        except Exception as e:
            attempt += 1
            print(f'Error publish attempt {attempt}: {e}')
            time.sleep(2 ** attempt)
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--level', type=int, default=1, choices=[1,2,3])
    parser.add_argument('--nombre', default='Test')
    parser.add_argument('--email', default='test@example.com')
    args = parser.parse_args()

    user = {'user_id': str(uuid.uuid4()), 'nombre': args.nombre, 'email': args.email}

    if args.level == 1:
        publish_level1(user)
    elif args.level == 2:
        publish_level2_persistent(user)
    else:
        publish_level3_confirm(user)
