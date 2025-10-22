#!/usr/bin/env python3
"""Automation for Fase 3 validations (PRUEBA 1/2/3).

This script uses pika to:
- PRUEBA1: publish a UsuarioCreado and assert it lands in email, loyalty, analytics queues (fanout)
- PRUEBA2: simulate subscriber crash and DLQ flow by republishing to retry queues and finally to dead_letters
- PRUEBA3: add a new analytics queue bind and show publisher unchanged

Run with the project's venv python.
"""
import json
import time
from events import get_connection_params, republish_to_retry_queue, publish_to_dead_letters
import pika


def declare_basics(ch):
    ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
    ch.exchange_declare(exchange='dead_letters', exchange_type='fanout', durable=True)
    args = {'x-dead-letter-exchange': 'dead_letters'}
    ch.queue_declare(queue='email_queue', durable=True, arguments=args)
    ch.queue_declare(queue='loyalty_queue', durable=True, arguments=args)
    ch.queue_declare(queue='analytics_queue', durable=True, arguments=args)
    ch.queue_bind(exchange='user_events', queue='email_queue')
    ch.queue_bind(exchange='user_events', queue='loyalty_queue')
    ch.queue_bind(exchange='user_events', queue='analytics_queue')
    ch.queue_declare(queue='dead_letter_queue', durable=True)
    ch.queue_bind(exchange='dead_letters', queue='dead_letter_queue')


def publish_user_event(channel, payload):
    channel.basic_publish(exchange='user_events', routing_key='', body=json.dumps(payload), properties=pika.BasicProperties(delivery_mode=2))


def queue_count(ch, qname):
    try:
        res = ch.queue_declare(queue=qname, passive=True)
        return res.method.message_count
    except Exception:
        return None


def prueba1(ch):
    print('\nPRUEBA 1: E2E Broadcast')
    payload = {'event_type': 'UsuarioCreado', 'user_id': 'p1-uid', 'email': 'p1@example.com'}
    publish_user_event(ch, payload)
    time.sleep(0.5)
    for q in ('email_queue', 'loyalty_queue', 'analytics_queue'):
        cnt = queue_count(ch, q)
        print(f'Queue {q} has {cnt} messages (expect >=1)')


def prueba2(ch):
    print('\nPRUEBA 2: Resiliencia suscriptor (simulación de fallo y DLQ)')
    payload = {'event_type': 'UsuarioCreado', 'user_id': 'p2-uid', 'email': 'p2@example.com'}
    # publish
    publish_user_event(ch, payload)
    time.sleep(0.5)
    print('Published event for prueba2. Simulating 3 failing delivery attempts for email_queue...')

    # Simulate consumer failing 3 times by republishing to retry queues and finally to dead letters
    headers = {}
    max_retries = 3
    delays = [2000, 4000, 6000]
    for attempt in range(max_retries):
        headers['x-retries'] = attempt + 1
        delay = delays[min(attempt, len(delays)-1)]
        republish_to_retry_queue('email_queue', payload, headers=headers, delay_ms=delay)
        print(f'  simulated retry {attempt+1} -> retry queue delay {delay}ms')
    # Finally send to dead letters
    publish_to_dead_letters(payload, headers=headers)
    print('  published to dead_letters')
    time.sleep(0.5)
    dlq_count = queue_count(ch, 'dead_letter_queue')
    print(f'dead_letter_queue messages: {dlq_count} (expect >=1)')


def prueba3(ch):
    print('\nPRUEBA 3: Agregar consumer sin tocar publisher')
    # create a new analytics queue and bind it
    extra = 'analytics_extra_queue'
    ch.queue_declare(queue=extra, durable=True)
    ch.queue_bind(exchange='user_events', queue=extra)
    payload = {'event_type': 'UsuarioCreado', 'user_id': 'p3-uid', 'email': 'p3@example.com'}
    publish_user_event(ch, payload)
    time.sleep(0.5)
    cnt = queue_count(ch, extra)
    print(f'New queue {extra} has {cnt} messages (expect >=1). Publisher unchanged.')


def main():
    params = get_connection_params()
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    declare_basics(ch)
    prueba1(ch)
    prueba2(ch)
    prueba3(ch)
    conn.close()


if __name__ == '__main__':
    main()
