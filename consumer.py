
import pika
import json
import logging
from typing import Set

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Para idempotencia (en prod: usar Redis o DB)
processed_messages: Set[str] = set()

# Simulación de inventario central
central_inventory = {
    1: {"name": "Manzanas Organicas", "stock": 100},
    2: {"name": "Pan Integral", "stock": 50},
    3: {"name": "Leche Deslactosada", "stock": 30},
    4: {"name": "Cafe Premium", "stock": 25},
    5: {"name": "Quinoa", "stock": 15}
}

def process_sale_message(ch, method, properties, body):
    try:
        message = json.loads(body)
        message_id = message.get('message_id')
        logger.info(f"📨 Recibido mensaje: {message_id}")

        # Idempotencia
        if message_id in processed_messages:
            logger.info(f"⏭️ Mensaje duplicado ignorado: {message_id}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Validar datos requeridos
        required_fields = ['product_id', 'quantity_sold']
        if not all(field in message for field in required_fields):
            logger.error(f"❌ Mensaje inválido, faltan campos: {message}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        # Procesar lógica de negocio
        product_id = message['product_id']
        quantity = message['quantity_sold']
        if product_id in central_inventory:
            product = central_inventory[product_id]
            old_stock = product['stock']
            product['stock'] = max(0, product['stock'] - quantity)
            processed_messages.add(message_id)
            logger.info(f"📊 Inventario actualizado - {product['name']}: {old_stock} → {product['stock']} (mensaje: {message_id})")
            # Enviar notificación al API central
            try:
                import requests
                notification = {
                    "branch_id": message.get("branch_id", "sucursal-001"),
                    "product_id": product_id,
                    "quantity_sold": quantity,
                    "timestamp": message.get("timestamp"),
                    "sale_price": message.get("sale_price", 0)
                }
                response = requests.post(
                    "http://localhost:8000/sale-notification",
                    json=notification,
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info("✅ Notificación enviada al API central")
                else:
                    logger.warning(f"⚠️ Error al notificar al API central: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error enviando notificación al API central: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            logger.error(f"❌ Producto {product_id} no encontrado")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON inválido: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_consumer():
    params = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=pika.PlainCredentials('ecomarket_user', 'ecomarket_password'),
        heartbeat=600,
        blocked_connection_timeout=300
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(
        queue='sale_notifications',
        durable=True,
        arguments={
            'x-message-ttl': 86400000,
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': 'sale_notifications_dlq'
        }
    )
    channel.queue_declare(
        queue='sale_notifications_dlq',
        durable=True
    )
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='sale_notifications', on_message_callback=process_sale_message)
    logger.info("Esperando mensajes en la cola 'sale_notifications'. Presiona CTRL+C para salir.")
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()
