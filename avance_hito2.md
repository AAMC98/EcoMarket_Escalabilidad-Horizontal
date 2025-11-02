# Avance Hito 2 — Escalabilidad Horizontal y Balanceo de Carga

Fecha: 2025-11-01

Resumen breve

Este documento resume la entrega parcial (10%) del Hito 2: demostrar escalabilidad horizontal del `users_service` usando Nginx como balanceador y RabbitMQ como broker de eventos. El repositorio contiene la configuración ejemplo para levantar 3 réplicas del servicio (`docker-compose.taller6.yml`), un Nginx con `upstream` y scripts para generar carga y recopilar evidencia.

Diagrama de componentes (Mermaid)

```mermaid
flowchart LR
  Cliente[Cliente\n(Browser / Postman)] --> Nginx[Nginx\n(Load Balancer)\n(least_conn)]
  Nginx --> I1[Instancia 1\nPuerto 8000]
  Nginx --> I2[Instancia 2\nPuerto 8001]
  Nginx --> I3[Instancia 3\nPuerto 8002]
```

Justificación de escalabilidad (breve)

  - Throughput: añadir réplicas aumenta la capacidad de servicio concurrente cuando la carga sube.
  - Resiliencia: fallos de una réplica no detienen el servicio si el balanceador redirige el tráfico a réplicas sanas.
  - Mantenibilidad: despliegues rolling o actualizaciones por réplica reducen downtime.

  - Estado compartido: sesiones en memoria requieren sticky sessions o una capa de estado centralizada (Redis, DB).
  - Observabilidad y métricas: coordinar métricas por instancia (Prometheus/Grafana) para escalado automático.
  - Consistencia en deploys: coordinación para migraciones de esquema o cambios no compatibles.

Distribución lograda (evidencia)

  - `./artifacts/responses_*.json` — respuestas del flood con el campo `instance`.
  - `./artifacts/logs_*/summary_*.json` — conteo por réplica de las entradas relevantes. Ejemplo: 19/19/19 en una ejecución.
  - `./artifacts/logs_*/user-service-*.filtered.log` — líneas filtradas con `Usuario creado localmente` y `Evento UsuarioCreado publicado` por réplica.

Comandos principales (para reproducir)

PowerShell (desde la raíz del repo):

```powershell
# Levantar stack (si docker compose falla en Windows por ruta, usa la alternativa manual con docker run)
docker compose -f docker-compose.taller6.yml up --build -d

# Enviar flood de 30 requests
.\scripts\collect_demo.ps1 -Count 30 -Url http://localhost/users

# Extraer logs filtrados y summary
.\scripts\extract_logs.ps1 -Tail 500 -OutDir .\artifacts

# Crear ZIP de evidencias (opcional)
.\scripts\make_artifacts_zip.ps1 -ArtifactsDir .\artifacts -OutDir .\artifacts
```

Notas sobre ejecución en Windows

  - Reiniciar Docker Desktop y reintentar.
  - Mover el repo a una ruta sin espacios o caracteres especiales (por ejemplo `C:\repos\EcoMarket`) y volver a intentar.
  - Levantar contenedores manualmente con `docker run` (scripts y comandos alternativos incluidos en `README.md`).

Mejoras futuras (priorizadas)

1. Reusar conexión a RabbitMQ (pool/long-lived) para reducir overhead de conexión por petición.
2. Integrar métricas y alertas (Prometheus + Grafana) y configurar autoscaling horizontal.
3. Mover estado compartido a Redis para evitar dependencia de sticky sessions.
4. Pruebas de carga más robustas (wrk, vegeta) y validación de latencia tail.

Preguntas de reflexión (post-taller)


Entrega

Subir este repositorio a GitHub y acompañarlo con:

Repositorio público (destino de entrega):
https://github.com/AAMC98/EcoMarket_Escalabilidad-Horizontal
