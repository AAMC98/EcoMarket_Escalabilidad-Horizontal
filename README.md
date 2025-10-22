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

Diagrama del flujo (Mermaid)

```mermaid
flowchart LR
  subgraph Publisher
    USR[UsuarioService (Publisher)]
  end

  subgraph Bus[RabbitMQ (fanout exchange:user_events)]
    EX[Exchange: user_events (fanout)]
  end

  subgraph Subscribers
    NOT[NotificacionesService (Subscriber)]
    EST[EstadisticasService (Subscriber)]
  end

  USR --> EX
  EX --> NOT
  EX --> EST

  classDef service fill:#f9f,stroke:#333,stroke-width:1px;
  class USR,NOT,EST service
```

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

Pruebas de fallos
- Publicar un evento inválido (por ejemplo, sin email) y comprobar que el mensaje es rechazado y enviado a la DLQ.

Consideraciones y mejoras
- Persistencia de contadores en `estadisticas_consumer.py` (usar Redis o SQLite).
- Reintentos con backoff en lugar de nack inmediato para errores transitorios.
- Uso de colas temporales (exclusive) si prefieres que cada instancia de servicio tenga su propia cola.
