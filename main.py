import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware.manejo_errores import registrar_manejadores
from app.api.routers import (
    catalogo_router, parametrizacion_router, recorridos_router, seguridad_router, usuarios_router,
    vehiculos_router)
from app.api.schemas.ejemplos_openapi import conservar_nulos_en_ejemplos
from app.repositories.config.settings import settings
from app.repositories.database.conexion import SessionLocal, engine
from app.repositories.database.inicializacion import inicializar_base_de_datos

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    with SessionLocal() as sesion:
        inicializar_base_de_datos(engine, sesion)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Web services del sistema de seguimiento de consumo de combustible y emisiones de CO₂.",
    version="0.2.0",
    lifespan=ciclo_de_vida,
)
registrar_manejadores(app)
app.include_router(usuarios_router.router)
app.include_router(seguridad_router.router)
app.include_router(parametrizacion_router.router)
app.include_router(catalogo_router.router)
app.include_router(vehiculos_router.router)
app.include_router(recorridos_router.router)
conservar_nulos_en_ejemplos(app)


@app.get("/", tags=["Estado"])
def root():
    return {"message": "API Activa"}
