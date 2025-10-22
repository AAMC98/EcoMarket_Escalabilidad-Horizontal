# Fase 0 — Análisis del problema real que justifica Pub/Sub

Fecha: 21-10-2025

Resumen rápido
- Contexto operativo: 800 registros de usuarios / día
- Valor por usuario activado: $50
- Tasa de fallos actual (síncrono a múltiples suscriptores): 5%
- Suscriptores actuales: 3 (email, loyalty, analytics)
- Latencia por llamada HTTP: 200 ms

Objetivo: cuantificar el coste del acoplamiento síncrono y justificar, con números, la inversión en un sistema Pub/Sub.

---

## 1) ¿Cuál es el costo mensual de fallos en engagement?

Datos usados:
- Registros por día R = 800
- Tasa de fallos f = 5% = 0.05
- Valor por usuario activado V = $50

Cálculo paso a paso:
- Usuarios perdidos por día = R × f = 800 × 0.05 = 40 usuarios/día
- Pérdida monetaria por día = 40 × $50 = $2,000/día
- Mes (30 días) = $2,000 × 30 = $60,000/mes
- Año (12 meses) = $60,000 × 12 = $720,000/año

Respuesta: El coste aproximado por fallos es $60,000 al mes (≈ $720k/año) bajo las hipótesis dadas.

---

## 2) Si agrego 2 suscriptores, ¿cómo escala el problema?

Situación nueva:
- Suscriptores finales s2 = 5 (3 + 2)
- Latencia por llamada L = 0.2 s (200 ms)
- Latencia total actual (s=3): L_total = 3 × 0.2 = 0.6 s
- Latencia total nueva (s2=5): L_total2 = 5 × 0.2 = 1.0 s

Modelo y suposición para proyectar fallos:
- Suponemos que la tasa de fallos escala aproximadamente con la latencia total (hipótesis razonable cuando la sobrecarga del productor o timeouts de downstream son la causa principal de fallo). Con esto:
  f2 = f × (L_total2 / L_total) = 0.05 × (1.0 / 0.6) ≈ 0.08333 (8.33%)

Cálculo:
- Usuarios perdidos por día (nuevo) = R × f2 = 800 × 0.08333 ≈ 66.67 usuarios/día
- Pérdida por día = 66.67 × $50 ≈ $3,333.33/día
- Pérdida por mes (30d) ≈ $100,000/mes

Impacto incremental:
- Pérdida mensual antes: $60,000
- Pérdida mensual después (+2 subs): ≈ $100,000
- Incremento en pérdida ≈ $40,000/mes

Observaciones adicionales:
- Latencia total pasa a 1s por registro; eso reduce la capacidad de servicio por instancia y aumenta concurrencia pendiente, lo que a su vez puede aumentar fallos por saturación.
- Si la tasa de fallos escalase de forma más agresiva (p. ej. debido a timeouts configurados en 800 ms), el impacto sería incluso peor.

---

## 3) ¿A partir de qué punto el acoplamiento se vuelve crítico? (Umbral financiero / ROI)

Estimación de coste de inversión para migrar a Pub/Sub (orden de magnitud):

Implementación (conservador):
- Trabajo de desarrollo: 1 desarrollador × 4 semanas × 40 h/sem = 160 h
- Coste hora (ejemplo): $40–$60/h → coste dev = $6,400–$9,600 (rango)
- Infra adicional (hosting / HA para broker, monitoring): $50–$400/mes
- Mantenimiento y operación (monitoring, alertas, 4 h/mes): 4 h × $50 = $200/mes

Amortización (ejemplo): amortizar coste de implementación a 6 meses:
- Coste mensual amortizado (bajo) ≈ (6,400 / 6) + 300 ≈ $1,367/mes
- Coste mensual amortizado (alto) ≈ (9,600 / 6) + 400 ≈ $2,000/mes

Umbral práctico:
- Si las pérdidas mensuales por acoplamiento > ~ $1,500–$2,000 (rango conservador), la inversión en Pub/Sub suele estar justificada.

Comparación con nuestro caso:
- Pérdida actual estimada = $60,000/mes → Muy por encima del umbral.

Respuesta: En este ejemplo, el acoplamiento se vuelve crítico desde incluso unos pocos miles de dólares al mes; con $60k/mes de pérdida, la inversión en Pub/Sub es trivialmente rentable (ROI rápido).

---

## 4) ¿Qué costos ocultos estoy ignorando?

Lista de costos ocultos y operacionales a considerar (con breve nota de impacto):

1. Operación y mantenimiento del broker
   - Patching, backups, HA, monitorización, coste/hora de SRE.
   - Estimación: 2–8 h/mes de trabajo SRE según SLA.

2. Versionado y compatibilidad de eventos (schema evolution)
   - Definir y evolucionar contratos (Avro/JSON Schema), migraciones, validadores.

3. Retries, DLQ y manejo de errores
   - Política de reintentos, circuit-breakers, colas muertas, y operaciones de re-proceso.

4. Observabilidad y trazabilidad
   - Instrumentación (trazas distribuidas, métricas por topic/queue), coste de herramientas (e.g., Elastic, Grafana, Jaeger).

5. Testing y entornos (staging que repliquen colas)
   - Pipelines de CI que incluyan tests de integración con broker; mantenimiento de infra de staging.

6. Formación del equipo y cambios en la cultura de desarrollo
   - Cambiar mentalidad síncrona → eventual consistency; escribir consumers idempotentes.

7. Posible duplicación u orden eventual
   - Diseñar para idempotencia y orden donde sea requerido, puede aumentar complejidad del código.

8. Costes de almacenamiento (retención de eventos)
   - Si se retienen mensajes o eventos históricos para replays, hay coste de almacenamiento.

Cada uno de estos items puede añadir horas/mes de trabajo y costes económicos; típicamente suman unas pocas centenas a unos pocos miles de dólares al mes según el SLA y el tamaño del equipo.

---

## 2 limitaciones clave de colas punto-a-punto / llamadas HTTP síncronas (por qué no escalan)

1) Acoplamiento del productor: cada nuevo consumidor añade latencia y carga al productor.
   - El productor tiene que conocer y llamar cada consumidor. Eso multiplica la latencia por número de consumidores y hace que el productor sea un punto único de fallo.

2) Escalado y disponibilidad costosos:
   - Para soportar más consumidores y mayor latencia hay que escalar el productor (más instancias) o aceptar más fallos; diagnosticar y aislar fallos es más difícil (cascade failures).

Breve nota técnica: con Pub/Sub (fanout/exchange) el productor publica una sola vez y el broker se encarga de la entrega, lo que desacopla disponibilidad y permite escalar consumidores independientemente.

---

## Escenarios comparativos (resumen)

- Escenario A — Actual (3 subs):
  - Pérdida ≈ $60,000/mes
  - Latencia total por registro = 0.6 s

- Escenario B — +2 subs (5 subs):
  - Pérdida proyectada ≈ $100,000/mes
  - Latencia total por registro = 1.0 s

Conclusión: el coste incremental esperado por añadir suscriptores es alto y justifica migrar a Pub/Sub urgentemente.

---

## Checkpoint de Fase 0 (requerimientos)

| Criterio | ¿Cumple? | Evidencia / Comentario |
|---|---:|---|
| Calculé costo mensual de acoplamiento | ✅ Sí | $60,000/mes (ver sección 1) |
| Identifiqué umbral para Pub/Sub | ✅ Sí | Umbral estimado ≈ $1,500–$2,000/mes (capex + opex amortizado) |
| Entiendo por qué colas punto-a-punto no escalan | ✅ Sí | Dos limitaciones clave listadas arriba |
| Conecté con proyecto previo (ventas/lealtad) | ✅ Sí | Valor por usuario usado ($50) y ejemplos de pérdidas por lealtad no activada |

---

## Recomendaciones prácticas (siguientes pasos rápidos)

1. Implementar un PoC Pub/Sub mínimo: una exchange fanout y dos consumidores adicionales. Medir caída de fallos en staging.
2. Añadir métricas y alertas: tasa de fallos por endpoint, latencia total por registro, mensajes en DLQ.
3. Diseñar contrato de evento y estrategia de versionado (JSON Schema o Avro).
4. Amortizar y comparar coste real vs pérdida actual para preparar business case y pedir presupuesto.

---

Si quieres, hago lo siguiente ahora:
- Generar una slide / imagen con los números clave para entregar al PO.
- Añadir un pequeño PoC en el repo que muestre el cálculo y algunos scripts para simular carga y fallos.

Dime qué prefieres y lo hago (p. ej. slides PDF, gráfico PNG, o scripts de simulación simples en Python).
