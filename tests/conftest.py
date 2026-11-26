import os

os.environ["DOCUMENTO_ADMIN_INICIAL"] = "1000000000"
os.environ["CORREO_ADMIN_INICIAL"] = "admin@huella-carbono.local"
os.environ["CONTRASENA_ADMIN_INICIAL"] = "Clave-Pruebas-2026"
os.environ["DATABASE_URL"] = "sqlite:///./test_huella.db"
os.environ["SMTP_HOST"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.db import get_db
from app.repositories.database.conexion import Base, crear_motor
from app.repositories.database.inicializacion import inicializar_base_de_datos
from main import app

ADMIN = {"username": "1000000000", "password": "Clave-Pruebas-2026"}


@pytest.fixture()
def db(tmp_path):
    motor = crear_motor(f"sqlite:///{tmp_path / 'prueba.db'}")
    Sesion = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)
    with Sesion() as sesion:
        inicializar_base_de_datos(motor, sesion)
    yield Sesion
    Base.metadata.drop_all(motor)
    motor.dispose()


@pytest.fixture()
def cliente(db):
    def _get_db():
        sesion = db()
        try:
            yield sesion
        finally:
            sesion.close()

    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def admin(cliente):
    respuesta = cliente.post("/api/v1/auth/sesiones", json=ADMIN)
    assert respuesta.status_code == 201, respuesta.text
    cliente.headers["Authorization"] = "Bearer " + respuesta.headers["X-Token-Sesion"]
    return cliente
