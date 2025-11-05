# EcoMarket — Escalabilidad Horizontal (Semana 6)

Este repositorio contiene la entrega parcial del Hito 2 (10%) enfocada en escalabilidad horizontal del `users_service` usando Nginx como balanceador y RabbitMQ como broker (cuando aplica). Se ha probado una configuración con 3 réplicas del servicio detrás de Nginx y se generó evidencia (respuestas, logs y un video E2E).

---

## Diagrama de componentes

```mermaid
flowchart LR
  Cliente[Cliente (Browser / Postman)] --> Nginx[Nginx (Load Balancer, least_conn)]
  Nginx --> I1[Instancia 1 - Puerto 8000]
  Nginx --> I2[Instancia 2 - Puerto 8001]
  Nginx --> I3[Instancia 3 - Puerto 8002]
```

---

## Resumen corto (1–2 páginas)

### 1) Objetivo y alcance

- Mostrar que 3 réplicas del `users_service` detrás de Nginx reparten carga (mode: least_conn) y que cada réplica sigue publicando eventos a RabbitMQ.

### 2) Evidencia generada

- Pruebas: flood de 30 requests a través de Nginx; respuestas incluyen `instance`.
- Artefactos (carpeta `./artifacts`):
  - `responses_*.json` — respuestas del flood con el campo `instance`.
  - `logs_*/summary_*.json` — conteo por réplica de líneas relevantes.
  - `logs_*/user-service-*.filtered.log` — líneas filtradas por réplica.

### 3) Mejora y observaciones

- Recomendado: conexiones persistentes a RabbitMQ, instrumentación (Prometheus/Grafana) y externalizar estado (Redis) para producción.

---

# EcoMarket — Escalabilidad Horizontal (Semana 6)

Este repositorio contiene la entrega parcial del Hito 2 enfocada en la práctica de escalabilidad horizontal del `users_service` usando Nginx como balanceador. Se incluyeron scripts y artefactos para reproducir la prueba y recolectar evidencia.

Resumen de cambios y estado:
- Pruebas realizadas con 3 réplicas del `users_service` detrás de Nginx. Evidencia en `./artifacts` (responses y logs).
- Se intentó generar un diagrama SVG desde Mermaid, pero la generación local produjo errores en su entorno. He eliminado los archivos temporales asociados a esa prueba y dejamos el README con la información necesaria para reproducir la práctica.

Nota: el diagrama en Mermaid se ha retirado para evitar confusión; si lo desea, puedo volver a incluirlo como imagen generada y subida al repositorio (requiere ejecutar mermaid-cli o docker localmente).

---

## Resumen corto

### Objetivo y alcance

- Mostrar que 3 réplicas del `users_service` detrás de Nginx reparten carga (mode: least_conn) y que cada réplica publica eventos a RabbitMQ.

### Evidencia generada

- Pruebas: flood de 30 requests a través de Nginx; respuestas incluyen `instance`.
- Artefactos (carpeta `./artifacts`):
  - `responses_*.json` — respuestas del flood con el campo `instance`.
  - `logs_*/summary_*.json` — conteo por réplica de líneas relevantes.
  - `logs_*/user-service-*.filtered.log` — líneas filtradas por réplica.

### Mejora y observaciones

- Recomendado: reusar conexiones a RabbitMQ, instrumentación (Prometheus/Grafana) y externalizar estado (Redis) para producción.

---

## Cómo reproducir (comandos rápidos)

PowerShell (desde la raíz del repo):

```powershell
# Levantar la demo (si usa docker compose)
docker compose -f docker-compose.taller6.yml up --build -d

# Ejecutar flood y guardar respuestas
.\scripts\collect_demo.ps1 -Count 30 -Url http://localhost/users

# Extraer logs filtrados y summary
.\scripts\extract_logs.ps1 -Tail 500 -OutDir .\artifacts

# Crear ZIP con evidencias (opcional)
.\scripts\make_artifacts_zip.ps1 -ArtifactsDir .\artifacts -OutDir .\artifacts
```

Visualización rápida de evidencia:

```powershell
Get-Content .\artifacts\responses_*.json -Raw | ConvertFrom-Json | Group-Object instance
Get-Content .\artifacts\logs_*\summary_*.json -Raw | ConvertFrom-Json
Get-Content .\artifacts\logs_*\user-service-1.filtered.log -Tail 30
```

---
