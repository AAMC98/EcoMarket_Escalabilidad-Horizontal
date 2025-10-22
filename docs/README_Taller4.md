# Taller 4 — Pub/Sub con RabbitMQ (Python)

Este README contiene los pasos mínimos para demostrar el flujo UsuarioCreado → RabbitMQ (fanout) → NotificacionesService + EstadísticasService.

Requisitos
- Docker (opcional, para RabbitMQ)
- Python 3.8+
- Dependencias: las del proyecto ya incluyen `pika` en `requirements.txt`.

Arrancar RabbitMQ y servicios con Docker Compose (recomendado)

PowerShell:

```powershell
# Levanta RabbitMQ + users_service + consumers (usa el Dockerfile del repo)
docker-compose up --build
```

Si prefieres levantar solo RabbitMQ (sin construir imágenes del repo), usa:

```powershell
# Levanta solo RabbitMQ (management UI: http://localhost:15672)
docker run -d --rm --name ecomarket-rabbit \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=ecomarket_user \
  -e RABBITMQ_DEFAULT_PASS=ecomarket_password \
  rabbitmq:3-management
```

Archivos principales
- `user_publisher.py` — publica eventos `UsuarioCreado` al exchange `user_events` (fanout).
- `notificaciones_consumer.py` — suscriptor que valida evento y simula envío de email; usa DLQ `notificaciones_user_dlq`.
- `estadisticas_consumer.py` — suscriptor opcional que cuenta usuarios nuevos en memoria; usa DLQ `estadisticas_user_dlq`.

Cómo probar (flujo E2E)

1) Levanta RabbitMQ (ver arriba)

2) En una terminal, arranca el consumidor de notificaciones:

```powershell
python .\notificaciones_consumer.py
```

3) En otra terminal, arranca el consumidor de estadísticas (opcional):

```powershell
python .\estadisticas_consumer.py
```

Prueba completa (E2E)

1) Levanta todo con `docker-compose up --build`.

2) Llama al endpoint de creación de usuarios (esto crea el usuario y publica `UsuarioCreado`):

```powershell
curl -X POST http://localhost:8002/users -H "Content-Type: application/json" -d '{"nombre":"Ana Perez","email":"ana@example.com"}'
```

3) Alternativamente, si no usas `users_service`, publica manualmente con el script:

```powershell
python .\user_publisher.py --nombre "Ana Perez" --email "ana@example.com"
```

4) Observa logs en las consolas de los containers o en tu terminal donde ejecutaste los consumidores: deberías ver el email simulado y el contador incrementando.

5) Observa las salidas en las consolas de los consumidores. El consumer de notificaciones mostrará la línea simulando el envío de email; el consumer de estadísticas incrementará su contador.

Demo rápido (acelerar retries para la entrega y DLQ)
-----------------------------------------------

Si quieres demostrar el flujo completo retry → re-entrega → DLQ en segundos (útil para grabar un video), usa la variable de entorno `FAST_RETRY=1` al arrancar los consumidores. Esto no cambia la lógica de producción; solo reduce los TTL de retry para la demo.

PowerShell — abre 3 terminales separadas:

Terminal A — Email consumer (rápido)
```powershell
$env:FAST_RETRY = '1'
.\.venv311\Scripts\python.exe .\email_consumer_simple.py
```

Terminal B — Loyalty consumer (rápido)
```powershell
$env:FAST_RETRY = '1'
.\.venv311\Scripts\python.exe .\loyalty_consumer_simple.py
```

Terminal C — Analytics consumer
```powershell
.\.venv311\Scripts\python.exe .\analytics_consumer.py
```

Publica mensajes que simulan fallo (desde otra terminal):

```powershell
.\.venv311\Scripts\python.exe .\simulate_fail_publisher.py --count 3
```

Observa en las consolas de los consumidores las re-publicaciones a retry queues y, tras agotar `MAX_RETRIES`, el envío a `dead_letters`.

Inspección rápida de colas (docker):

```powershell
docker ps
docker exec -it ecomarket-rabbit rabbitmqctl list_queues name messages
```

UI management: http://localhost:15672 (user: `ecomarket_user`, pass: `ecomarket_password`) → pestaña Queues → revisa `email_queue`, `loyalty_queue`, `analytics_queue`, `dead_letter_queue` y las retry queues (`*.retry.*`).

Forzar DLQ inmediatamente (opcional):

```powershell
.\.venv311\Scripts\python.exe -c "from events import get_connection_params; import pika, json; p=get_connection_params(); c=pika.BlockingConnection(p); ch=c.channel(); ch.exchange_declare(exchange='dead_letters',exchange_type='fanout',durable=True); ch.basic_publish(exchange='dead_letters',routing_key='',body=json.dumps({'force':'dlq_test'}),properties=pika.BasicProperties(delivery_mode=2)); c.close()"
```

Limpiar variable FAST_RETRY en PowerShell (opcional):

```powershell
# Quitar variable de entorno
Remove-Item Env:FAST_RETRY
# o
$env:FAST_RETRY = $null
```

Pruebas de fallos
- Publicar un evento inválido (por ejemplo, sin email) y comprobar que el mensaje es rechazado y enviado a la DLQ.

Auto-validación y script de demo rápida
--------------------------------------

Incluimos un script automatizado de validación para Fase 3 (`tests/fase3_runner.py`) que realiza las pruebas E2E descritas arriba. Para ejecutarlo manualmente:

```powershell
$env:PYTHONPATH = '.'; .\.venv311\Scripts\python.exe .\tests\fase3_runner.py
```

También hay un helper PowerShell `demo_quick.ps1` que arranca los 3 consumidores en nuevas ventanas (con `FAST_RETRY=1`) y ejecuta el test automatizado. Uso recomendado para grabar el video (desde la raíz del repo):

```powershell
# Ejecuta demo_quick y abre el management UI al final
.\demo_quick.ps1 -OpenManagementUI
# o solo
.\demo_quick.ps1
```

El script es solo para facilitar la demo; no cambia código de producción.

Cómo validar rápidamente (script)
--------------------------------

Resumen de pasos (copiar/pegar en PowerShell desde la raíz del repo):

1) Levantar RabbitMQ (si no está ya corriendo con puertos expuestos):

```powershell
docker run -d --rm --name ecomarket-rabbit \
  -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=ecomarket_user \
  -e RABBITMQ_DEFAULT_PASS=ecomarket_password \
  rabbitmq:3-management
```

2) Usar el helper para demo (arranca consumidores en nuevas ventanas y ejecuta las pruebas):

```powershell
# desde la raíz del repo
.\scripts\demo_quick.ps1 -OpenManagementUI
```

3) Ejecutar manualmente el test automatizado (si prefieres no abrir ventanas):

```powershell
$env:PYTHONPATH = '.'; .\.venv311\Scripts\python.exe .\tests\fase3_runner.py
```

Notas:
- `FAST_RETRY` se aplica en `demo_quick.ps1` para acelerar retries durante la demo; no usar en producción.
- Abre http://localhost:15672 para ver el management UI (user: `ecomarket_user`, pass: `ecomarket_password`).
- Si quieres repetir la demo limpias las queues desde la UI o con `rabbitmqctl purge_queue <queue>`.

Consideraciones y mejoras
- Persistencia de contadores en `estadisticas_consumer.py` (usar Redis o SQLite).
- Reintentos con backoff en lugar de nack inmediato para errores transitorios.
- Uso de colas temporales (exclusive) si prefieres que cada instancia de servicio tenga su propia cola.
