"""
Ejemplo Paso 2B: Direct exchange con routing keys
Uso: python examples/p2b_direct_routing.py --nombre "Ana" --email "ana@example.com"
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

    ch.exchange_declare(exchange='user_direct', exchange_type='direct', durable=True)

    # Publica con routing key "user.created.email"
    ch.basic_publish(
        exchange='user_direct',
        routing_key='user.created.email',
        body=json.dumps(user),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    conn.close()
    print('Publicado a exchange user_direct con routing key user.created.email')
