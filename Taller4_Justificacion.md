# Taller 4 — Justificación Pub/Sub y mejoras

Este documento resume la justificación del patrón Pub/Sub utilizado en el Taller 4 (UsuarioCreado), qué se logró en la entrega y propuestas de mejora para un entorno productivo.

---

## 1. ¿Por qué Pub/Sub (RabbitMQ) para este taller?

Elegimos Pub/Sub con RabbitMQ por las siguientes razones:

- Desacoplamiento: los productores (UsuarioService) publican eventos sin conocer a los consumidores (NotificacionesService, EstadísticasService). Esto permite desarrollar, desplegar y escalar servicios de forma independiente.
- Escalabilidad y flexibilidad: con un broker como RabbitMQ es sencillo añadir más consumidores o réplicas de consumidores para manejar mayor carga sin cambiar al publisher.
- Persistencia y entrega confiable: RabbitMQ proporciona colas durables, confirmaciones y DLQs, útiles para garantizar entrega en presencia de fallos.
- Facilidad de despliegue para aprendizaje: RabbitMQ es sencillo de configurar (imagen Docker `rabbitmq:3-management`), tiene buena documentación y es ideal para aprender patrones de mensajería.

Comparación rápida con otras alternativas:
- Kafka: mejor en casos de *very high throughput* y retención a largo plazo, pero más complejo de operar. No necesario para este taller.
- Azure Service Bus: buena opción en entornos Azure, integración nativa con .NET.
- Redis Pub/Sub: simple y rápido, pero sin persistencia/ack/nack; menos apropiado donde la fiabilidad importa.

---

## 2. Contrato de evento

En Python usamos un dict equivalente a la clase `UsuarioCreadoEvent` definida en el enunciado. La estructura mínima publicada es:

- id: string (UUID) — identificador único del usuario
- nombre: string — nombre del usuario
- email: string — email del usuario
- event_type: "UsuarioCreado" — campo auxiliar para identificación del tipo de evento

Ejemplo de payload publicado por `users_service`:

```json
{
  "id": "...",
  "nombre": "Ana López",
  "email": "ana.lopez@example.com",
  "event_type": "UsuarioCreado"
}
```

---

## 3. Desacoplamiento logrado

- El publisher (`users_service`) publica eventos en el exchange `user_events` de tipo `fanout`.
- Los consumidores (`notificaciones_consumer`, `estadisticas_consumer`) declaran sus propias colas y las enlazan al exchange usando `queue_bind`.
- Resultado: agregar un nuevo suscriptor no requiere modificar ni volver a desplegar el publisher; basta con declarar una nueva cola y enlazarla al exchange.

Este desacoplamiento mejora la mantenibilidad y posibilita evoluciones independientes en cada servicio.

---

## 4. Manejo de fallos implementado

- Publisher: reintentos simples con backoff en `events.publish_user_created`.
- Consumidores:
  - Validación del payload (campos obligatorios y formato de email en `notificaciones_consumer`).
  - En caso de mensaje inválido o JSON corrupto, los consumidores hacen `basic_nack(..., requeue=False)`.
  - Las colas principales se declararon con argumentos `x-dead-letter-exchange` y `x-dead-letter-routing-key` apuntando a colas DLQ (`*_dlq`), por lo que los mensajes inválidos se mueven a la DLQ.

Esto cubre el requisito mínimo de manejo de fallos mediante DLQ y reintentos en el publisher.

---

## 5. Limitaciones y retos (consistencia eventual)

- Mientras el Publisher escribe el evento y los consumidores procesan de forma asíncrona, los datos estarán finalmente consistentes. Esto significa que puede existir una ventana en la que el usuario creado aún no figure en las estadísticas o no haya recibido la notificación.
- Para casos donde se requiere **consistencia fuerte**, habría que implementar confirmaciones adicionales, transacciones distribuidas o peticiones sincrónicas (lo cual sacrificaría el desacoplamiento y la escalabilidad).

---

## 6. Mejoras futuras (sugeridas)

1. Más eventos y versionado de contratos
   - Introducir eventos secundarios (p. ej. `UsuarioActualizado`, `UsuarioEliminado`).
   - Versionado del esquema de eventos (e.g., `event_type` + `schema_version`) para permitir evoluciones sin romper consumidores existentes.

2. Persistencia y métricas
   - Persistir contadores de `estadisticas` en Redis o base de datos para tolerancia a reinicios.
   - Añadir métricas y monitoreo (Prometheus + Grafana) para latencias de consumo, tasas de mensajes, tamaño de DLQ, etc.

3. Observabilidad y tracing
   - Añadir trazabilidad distribuida (OpenTelemetry) y logs estructurados con correlación por `event_id` para depuración E2E.

4. Robustez operativa
   - Implementar reconexión automática con backoff en consumidores y publisher confirms para el publisher.
   - Políticas de reintento más elaboradas y manejo de poison messages (p. ej. mover a DLQ tras N reintentos).

5. Tests automáticos
   - Añadir pruebas unitarias e integración (por ejemplo usando containerized RabbitMQ en CI) que verifiquen el flujo end-to-end.

---

## 7. Cómo entregar

Incluye en tu repositorio:
- Código fuente de los servicios.
- `README.md` con pasos para ejecutar el demo (docker run de RabbitMQ, arrancar consumers y el servicio de usuarios). 
- Este archivo (`Taller4_Justificacion.md`) y, opcionalmente, una captura o diagrama Mermaid del flujo pub/sub.

---

Archivo preparado para adjuntar al repositorio como `Taller4_Justificacion.md`.
