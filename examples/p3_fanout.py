"""
Ejemplo Paso 3: Pub/Sub con Fanout Exchange
Uso: python examples/p3_fanout.py --nombre "Ana" --email "ana@example.com"
"""
import pika
import json
import argparse


def get_conn():
    return pika.BlockingConnection(pika.ConnectionParameters('localhost'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--nombre', default='Test User')
    parser.add_argument('--email', default='test@example.com')
    args = parser.parse_args()

    user = {'id': 'tmp-id', 'nombre': args.nombre, 'email': args.email}

    conn = get_conn()
    ch = conn.channel()

    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)

    ch.basic_publish(
        exchange='user_events',
        routing_key='',
        body=json.dumps(user),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    conn.close()
    print('Publicado al exchange user_events (fanout)')
