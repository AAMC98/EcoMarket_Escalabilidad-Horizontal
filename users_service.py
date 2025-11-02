"""users_service.py
Servicio mínimo que expone un endpoint POST /users para crear usuarios (simulado)
y publicar el evento UsuarioCreado en RabbitMQ usando `events.publish_user_created`.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
import os
from pydantic import BaseModel, ValidationError
import json
from typing import Optional
import uuid
import logging

from events import publish_user_created

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance identifier (set via Docker env INSTANCE_ID to distinguish logs per replica)
INSTANCE_ID = os.getenv('INSTANCE_ID', 'local')

app = FastAPI(title="UsuarioService (Taller4)")


class UserCreate(BaseModel):
    nombre: str
    # Use plain str for email to avoid optional external dependency on email-validator
    email: str


@app.post('/users')
async def create_user(request: Request, background_tasks: BackgroundTasks):
    """Lee el body crudo, lo registra para debugging, valida con Pydantic manualmente
    y publica UsuarioCreado en background. Esto devuelve errores de validación
    detallados para depuración (evita el 400 silencioso de validación automática).
    """
    body_bytes = await request.body()
    # Log a UTF-8-replaced version for debugging (safe to log)
    body_text_safe = body_bytes.decode('utf-8', errors='replace')
    logger.info("[%s] Raw request body: %s", INSTANCE_ID, body_text_safe)

    # First try Starlette/FastAPI JSON parsing (respects charset)
    data = None
    try:
        data = await request.json()
    except Exception:
        # Fallback: try several decodings then json.loads
        for enc in ('utf-8', 'latin-1', 'utf-16le', 'cp1252'):
            try:
                text = body_bytes.decode(enc)
                data = json.loads(text)
                logger.info("Parsed body using encoding %s", enc)
                break
            except Exception:
                continue

    if data is None:
        logger.error("Failed to parse JSON body (encoding/format issue)")
        raise HTTPException(status_code=400, detail="Invalid JSON or unsupported encoding")

    try:
        user = UserCreate(**data)
    except ValidationError as ve:
        logger.error("Validation error parsing UserCreate: %s", ve.errors())
        raise HTTPException(status_code=400, detail=ve.errors())

    # Simular persistencia
    new_id = str(uuid.uuid4())
    new_user = {"id": new_id, "nombre": user.nombre, "email": user.email}
    logger.info("[%s] Usuario creado localmente: %s", INSTANCE_ID, new_user)

    # Publicar evento en background (no bloquear endpoint)
    background_tasks.add_task(publish_user_created, new_user)

    # Devolver también el identificador de instancia para facilitar pruebas de balanceo
    return {"user_id": new_id, "instance": INSTANCE_ID}


@app.get('/health')
async def health():
    """Endpoint de salud usado por Docker HEALTHCHECK y Nginx (pasivo).
    Devuelve 200 con JSON sencillo y el id de instancia.
    """
    return {"status": "healthy", "instance": INSTANCE_ID}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8002)
