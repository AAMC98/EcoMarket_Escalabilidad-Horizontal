# Fase 2 — Implementando Pub/Sub con propósito

Fecha: 21-10-2025

Objetivo: Implementar y validar un Fanout Exchange (`user_events`) que permita publicar un evento UsuarioCreado y que múltiples consumidores lo procesen de forma independiente.

Demo rápida (5 minutos)

1) Asegúrate de tener RabbitMQ corriendo (docker-compose up -d o docker run rabbitmq:3-management).
2) En terminal A, ejecuta:

```powershell
python .\email_consumer_simple.py
```

3) En terminal B, ejecuta:

```powershell
python .\loyalty_consumer_simple.py
```

4) En terminal C, publica un evento (nivel 1):

```powershell
python .\events_publisher_levels.py --level 1 --nombre "Juan" --email "juan@eco.com"
```

Observa que ambos consumers imprimen su log: email enviado y lealtad activada.

Implementación (archivos añadidos)

- `events_publisher_levels.py` — publisher en niveles 1/2/3.
- `email_consumer_simple.py`, `loyalty_consumer_simple.py` — consumers simples binded a `user_events` (fanout).

Checklist de Fase 2

- [x] Exchange `user_events` (fanout) declarado por publisher y consumers.
- [x] Publisher puede publicar en 3 niveles (simple, persistente, confirmaciones).
- [x] Consumers independientes con ACK manual.
- [x] Demo rápida verificada localmente.

Pruebas recomendadas (siguientes pasos)

1. Nivel 2: publicar con persistencia, reiniciar RabbitMQ y comprobar que los mensajes persisten si hay consumidores durables/queues declaradas (requiere usar queues nombradas en lugar de exclusivas).
2. Nivel 3: forzar desconexión del broker y comprobar reintentos/backoff.
3. Implementar DLQ y reintentos en consumers para errores transitorios.

Demo de reintentos y DLQ

1) Ejecuta setup_queues.py para crear las queues durables y DLQ:

```powershell
python .\setup_queues.py
```

2) Inicia el dead-letter consumer (para inspección):

```powershell
python .\dead_letter_consumer.py
```

3) Inicia los consumers:

```powershell
python .\email_consumer_simple.py
python .\loyalty_consumer_simple.py
python .\analytics_consumer.py
```

4) Publica mensajes que forcen fallo y activa el flujo de retry:

```powershell
python .\simulate_fail_publisher.py --count 3
```

Observa: los mensajes serán reencolados a retry-queues con delays (5s, 30s, 120s). Si exceden retries, aparecerán en la `dead_letter_queue` y `dead_letter_consumer.py` los mostrará.
