from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware.manejo_errores import registrar_manejadores
from app.api.routers import seguridad_router
from app.repositories.config.settings import settings
from app.repositories.database.conexion import SessionLocal, engine
from app.repositories.database.inicializacion import inicializar_base_de_datos


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    with SessionLocal() as sesion:
        inicializar_base_de_datos(engine, sesion)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Web services del sistema de seguimiento de consumo de combustible y emisiones de CO₂.",
    version="0.1.0",
    lifespan=ciclo_de_vida,
)
registrar_manejadores(app)
app.include_router(seguridad_router.router)


@app.get("/", tags=["Estado"])
def root():
    return {"mensaje": "API Activa"}
