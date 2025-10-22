"""
simulate_fail_publisher.py
Publica mensajes con el flag simulate_fail=True para forzar que los consumers fallen y se active el flujo de reintentos y DLQ.
Uso: python simulate_fail_publisher.py --count 5 --level 2
"""
import argparse
import uuid
from events_publisher_levels import publish_level2_persistent

parser = argparse.ArgumentParser()
parser.add_argument('--count', type=int, default=5)
parser.add_argument('--nombre', default='UserFail')
parser.add_argument('--email', default='fail@example.com')
args = parser.parse_args()

for i in range(args.count):
    user = {'user_id': str(uuid.uuid4()), 'nombre': f"{args.nombre}_{i}", 'email': args.email, 'simulate_fail': True}
    publish_level2_persistent(user)
    print('Publicado con simulate_fail:', user['user_id'])
