````markdown
# EcoMarket — Escalabilidad Horizontal (Semana 6)

Este repositorio contiene la entrega parcial del Hito 2 (10%) enfocada en escalabilidad horizontal del `users_service` usando Nginx como balanceador y RabbitMQ como broker (cuando aplica). Se ha probado una configuración con 3 réplicas del servicio detrás de Nginx y se generó evidencia (respuestas, logs y un video E2E).

Repositorio de entrega: https://github.com/AAMC98/EcoMarket_Escalabilidad-Horizontal

---

## Informe breve (1–2 páginas) — Resumen para el docente
# EcoMarket — Semana 6: Escalabilidad Horizontal y Balanceo de Carga

Este repositorio contiene la entrega (avance) para la Semana 6 centrada en escalabilidad horizontal del `users_service` mediante Nginx como balanceador. El objetivo de la práctica fue mostrar que varias réplicas del servicio pueden atender tráfico en paralelo y publicar eventos a RabbitMQ sin downtime.

Repositorio de entrega: https://github.com/AAMC98/EcoMarket_Escalabilidad-Horizontal

---

## Diagrama de componentes

```mermaid
flowchart LR
  Cliente[Cliente\n(Browser / Postman)] --> Nginx[Nginx\n(Load Balancer)\n(least_conn)]
  Nginx --> I1[Instancia 1\nPuerto 8000]
  Nginx --> I2[Instancia 2\nPuerto 8001]
  Nginx --> I3[Instancia 3\nPuerto 8002]
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

## Cómo reproducir (comandos rápidos)

PowerShell (desde la raíz del repo):

```powershell
# Levantar la demo (intentar desde una ruta sin espacios si Docker en Windows falla)
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

Notas:

- Si `docker compose up` falla en Windows por la ruta del repo, mueve el proyecto a una ruta simple (ej. `C:\repos\EcoMarket`) o usa la alternativa manual con `docker run`.
- Los scripts en `scripts/` están adaptados para PowerShell y generan la carpeta `./artifacts` con respuestas y logs filtrados.

---

## Artefactos y video

- Artefactos: carpeta `./artifacts` (responses JSON, logs filtrados y summary JSON).
- Video E2E: coloca `docs/video_e2e.mp4` o pega el enlace aquí.

---

