"""
setup_queues.py
Declaración de exchanges y colas necesarias para la demo: user_events (fanout), dead_letters, email_queue, loyalty_queue, analytics_queue y retry queues.
Uso: python setup_queues.py
"""
import pika
from events import get_connection_params


def main():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Exchanges
    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
    ch.exchange_declare(exchange='dead_letters', exchange_type='fanout', durable=True)

    # Queues principales con DLX
    args = {'x-dead-letter-exchange': 'dead_letters'}
    ch.queue_declare(queue='email_queue', durable=True, arguments=args)
    ch.queue_declare(queue='loyalty_queue', durable=True, arguments=args)
    ch.queue_declare(queue='analytics_queue', durable=True, arguments=args)

    # Bind queues al exchange fanout
    ch.queue_bind(exchange='user_events', queue='email_queue')
    ch.queue_bind(exchange='user_events', queue='loyalty_queue')
    ch.queue_bind(exchange='user_events', queue='analytics_queue')

    # DLQ
    ch.queue_declare(queue='dead_letter_queue', durable=True)
    ch.queue_bind(exchange='dead_letters', queue='dead_letter_queue')

    print('Queues and exchanges declared')
    conn.close()


if __name__ == '__main__':
    main()
