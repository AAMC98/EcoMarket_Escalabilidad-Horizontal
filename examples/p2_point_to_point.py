"""
Ejemplo Paso 2: Colas punto-a-punto (duplicación de publishes)
Uso: python examples/p2_point_to_point.py --nombre "Ana" --email "ana@example.com"
"""
import pika
import json
import argparse


def get_conn():
    return pika.BlockingConnection(pika.ConnectionParameters('localhost'))


def publish_to_queue(queue_name, user_data):
    conn = get_conn()
    ch = conn.channel()
    ch.queue_declare(queue=queue_name, durable=True)
    ch.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(user_data),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--nombre', default='Test User')
    parser.add_argument('--email', default='test@example.com')
    args = parser.parse_args()

    user = {'id': 'tmp-id', 'nombre': args.nombre, 'email': args.email}

    publish_to_queue('email_queue', user)
    publish_to_queue('loyalty_queue', user)

    print('Publicado en email_queue y loyalty_queue')
