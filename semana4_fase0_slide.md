# Fase 0 — Resumen ejecutivo (1 página)

Objetivo: justificar por qué migrar a Pub/Sub (RabbitMQ) para notificaciones tras el registro de usuarios.

---

Puntos clave (rápido)

- Registros por día: 800
- Valor por usuario activado: $50
- Tasa de fallos actual (síncrono a consumidores): 5%
- Suscriptores actuales: 3 (email, loyalty, analytics)

Impacto económico

- Usuarios perdidos por día = 800 × 0.05 = 40
- Pérdida diaria = 40 × $50 = $2,000
- Pérdida mensual ≈ $60,000

Escenario con +2 suscriptores (5 en total)

- Latencia total por registro sube de 0.6s → 1.0s
- Tasa de fallos proyectada ≈ 8.3% → usuarios perdidos/día ≈ 67
- Pérdida mensual proyectada ≈ $100,000

Umbral de inversión (estimado)

- Coste de implementación + infra (amortizado) ≈ $1,500–$2,000/mes
- Si las pérdidas mensuales por acoplamiento > ese umbral, migrar a Pub/Sub es justificable.

Recomendación (acción inmediata)

1. Implementar PoC Pub/Sub (Exchange fanout + 2 consumers) en staging y medir reducción de fallos.
2. Añadir métricas clave: tasa de fallos, DLQ rate, latencia total por registro.
3. Diseñar contrato de eventos (JSON Schema) y plan de versionado.

Resultado esperado

- Reducir dependencia síncrona y latencia por usuario.
- Reducir fallos y recuperar ingresos (el ROI de la migración se recupera en semanas si las pérdidas actuales son del orden calculado).

---

Contacto: si quieres lo convierto en una slide PDF o imagen para compartir con el Product Owner.
