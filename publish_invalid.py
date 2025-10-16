# publish_invalid.py
import pika, json, os
params = pika.ConnectionParameters(
    host=os.environ.get('RABBIT_HOST','localhost'),
    port=int(os.environ.get('RABBIT_PORT',5672)),
    credentials=pika.PlainCredentials('ecomarket_user','ecomarket_password')
)
conn = pika.BlockingConnection(params)
ch = conn.channel()
ch.exchange_declare(exchange='user_events', exchange_type='fanout', durable=True)
body = {"id":"test-invalid","nombre":"Inválido","email":"not-an-email","event_type":"UsuarioCreado"}
ch.basic_publish(exchange='user_events', routing_key='', body=json.dumps(body), properties=pika.BasicProperties(delivery_mode=2))
conn.close()
print("Publicado inválido")