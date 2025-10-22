# Fase 1 — Evolución natural hacia eventos

Fecha: 21-10-2025

Objetivo
- Mostrar, con ejemplos prácticos y decisiones, cómo evolucionar desde llamadas HTTP síncronas a colas punto-a-punto y finalmente a Pub/Sub (fanout exchange).  
- Proveer scripts sencillos en Python para probar cada paso.

Resumen del journey

- Paso 1 — HTTP síncrono a múltiples servicios: simple pero no escala (latencia acumulada, acoplamiento).  
- Paso 2 — Cola punto-a-punto (duplicación de queues & publishers): reduce latencia del productor pero duplica código y acoplamiento en routing.  
- Paso 2B — Mejora con Direct Exchange + routing keys: centraliza publish con routing, pero requiere diseño de claves y conocimiento de bindings.  
- Paso 3 — Pub/Sub Fanout Exchange: una publicación → N consumidores; desacopla producers y consumers.

Archivos añadidos
- `examples/p2_point_to_point.py` — publica a queue `email_queue` y `loyalty_queue` (duplicación de llamadas).  
- `examples/p2b_direct_routing.py` — publica a `user_direct` (direct exchange) con routing keys.  
- `examples/p3_fanout.py` — publica al exchange `user_events` (fanout).

Cómo usar (rápido)

1) Asegúrate de tener RabbitMQ corriendo en localhost:5672.
2) Ejecuta un consumer para una queue concreta (puedes usar `notificaciones_consumer.py` o crear un consumer simple con `pika`).
3) Ejecuta los scripts de ejemplo para ver diferencias en comportamiento.

Ejemplos y pruebas propuestas

- Prueba A (Paso 2): Ejecuta `examples/p2_point_to_point.py` y observa que el servicio Registro debe realizar dos publishes (duplicación). Si añades un 4º suscriptor, añade otro publish => código duplicado.  
- Prueba B (Paso 2B): Ejecuta `examples/p2b_direct_routing.py`. Aquí solo publicas una vez con una routing key. Los consumers se deben bindear con la routing key correcta.  
- Prueba C (Paso 3): Ejecuta `examples/p3_fanout.py`. Publicas una vez al exchange fanout; cada subscriber que tenga su queue binded recibirá el mensaje.

Matriz de decisión (resumen)

| Solución | Complejidad | Funciona hasta | Falla cuando | Coste |
|---|---:|---:|---|---|
| HTTP Múltiples | Muy baja | 2 suscriptores, bajo volumen | 3+ suscriptores | Bajo |
| Colas punto-a-punto | Baja | 3 suscriptores fijos | Agregar dinámicamente | Bajo |
| Pub/Sub Fanout | Media | 10+ suscriptores | Routing selectivo complejo | Medio |
| Topic Exchange | Alta | Eventos filtrados por tipo | Sobreingeniería para simples | Alto |

Recomendación práctica para EcoMarket

- Si el número de suscriptores es estático y pequeño (≤3) y el equipo no quiere operar un broker, usar colas punto-a-punto está bien a corto plazo.  
- Si esperas crecimiento (>3 suscriptores), dinámicas de suscripción o broadcasting repetido → mover a Pub/Sub (fanout) y diseñar contratos de eventos.

Checkpoint de Fase 1 (criterios)

- Implementé ejemplos para Paso 2, Paso 2B y Paso 3 ✅
- Entiendo límites de cada paso y puntos de ruptura ✅
- Propuesta de cuándo migrar a Pub/Sub (si >3 suscriptores o crecimiento) ✅
