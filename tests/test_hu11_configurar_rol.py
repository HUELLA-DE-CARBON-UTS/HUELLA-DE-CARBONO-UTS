"""Pruebas de HU-11: creación de un rol o reemplazo de sus permisos.

Los casos 1 a 5 corresponden a los casos de prueba funcional de la historia.
"""

import pytest
from sqlalchemy.exc import OperationalError

from app.api.dependencies.auth import obtener_sesion
from app.domain.exceptions.errores import DatosNoValidos
from app.services.use_cases.verificar_permiso import SesionUsuario
from app.services.validators import rol_validador
from main import app
from tests.conftest import CABECERA_ADMIN

RUTA = "/api/v1/roles/Analista%20ambiental"
NUEVE = ["FUN-41", "FUN-42", "FUN-49", "FUN-50", "FUN-53", "FUN-54", "FUN-56", "FUN-57", "FUN-61"]
CUERPO = {"descripcion": "Consulta consumo, emisiones, indicadores y reportes", "permisos": NUEVE}


# ---------- Casos de prueba funcional ----------

def test_caso1_crea_rol_nuevo(cliente):
    r = cliente.put(RUTA, json=CUERPO, headers=CABECERA_ADMIN)
    assert r.status_code == 201
    j = r.json()
    assert j["estado"] == "exito"
    assert j["mensaje"] == "Rol configurado correctamente"
    assert j["datos"]["accion"] == "creado"
    assert j["datos"]["estado"] == "activo"
    assert j["datos"]["permisos"] == NUEVE
    assert j["datos"]["idRol"] == "ROL-02"  # ROL-01 es el Administrador inicial


def test_caso2_operacion_inexistente(cliente):
    r = cliente.put(RUTA, json={**CUERPO, "permisos": ["FUN-41", "FUN-99"]}, headers=CABECERA_ADMIN)
    assert r.status_code == 422
    j = r.json()
    assert j["datos"] is None
    assert j["mensaje"] == "La configuración del rol no es válida"
    assert j["errores"] == [{"campo": "permisos", "detalle": "La operación FUN-99 no existe en el sistema"}]


def test_caso3_estructura_estandar(cliente):
    j = cliente.put(RUTA, json=CUERPO, headers=CABECERA_ADMIN).json()
    assert set(j) == {"estado", "codigo", "mensaje", "datos", "errores", "metadatos"}
    assert isinstance(j["estado"], str) and isinstance(j["codigo"], int) and isinstance(j["mensaje"], str)
    assert j["errores"] == []
    assert isinstance(j["metadatos"], dict) and j["metadatos"]["funcionalidad"] == "FUN-11"
    assert set(j["datos"]) == {"idRol", "nombre", "descripcion", "estado", "permisos", "accion"}


def test_caso4_sin_permisos(cliente):
    r = cliente.put(RUTA, json={**CUERPO, "permisos": []}, headers=CABECERA_ADMIN)
    assert r.status_code == 422
    assert {"campo": "permisos", "detalle": "El rol debe tener al menos un permiso"} in r.json()["errores"]


def test_caso5_base_de_datos_no_disponible(cliente, monkeypatch):
    from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy

    def falla(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(RolRepositorioSQLAlchemy, "operaciones_existentes", falla)
    r = cliente.put(RUTA, json=CUERPO, headers=CABECERA_ADMIN)
    assert r.status_code == 503
    assert r.json()["mensaje"] == "No fue posible guardar la configuración del rol"


# ---------- Reglas adicionales de la historia ----------

def test_reemplaza_permisos_de_rol_existente_sin_duplicados(cliente):
    cliente.put(RUTA, json=CUERPO, headers=CABECERA_ADMIN)
    r = cliente.put(RUTA, json={"descripcion": "", "permisos": ["FUN-56", "FUN-57", "FUN-56"]}, headers=CABECERA_ADMIN)
    assert r.status_code == 200
    d = r.json()["datos"]
    assert d["accion"] == "actualizado"
    assert d["idRol"] == "ROL-02"
    assert d["permisos"] == ["FUN-56", "FUN-57"]
    assert d["descripcion"] == CUERPO["descripcion"]  # se conserva si no se envía una nueva


def test_registra_fecha_y_responsable(cliente, db):
    from app.repositories.database.modelos import RolModelo
    cliente.put(RUTA, json=CUERPO, headers=CABECERA_ADMIN)
    with db() as s:
        rol = s.query(RolModelo).filter_by(nombre="Analista ambiental").one()
        assert rol.responsable == "1000000000"
        assert rol.fecha_actualizacion is not None


def test_sin_sesion_responde_401(cliente):
    r = cliente.put(RUTA, json=CUERPO)
    assert r.status_code == 401
    assert r.json()["estado"] == "error"


def test_rol_sin_permiso_fun11_responde_403(cliente):
    cliente.put("/api/v1/roles/Coordinador%20de%20operaciones",
                json={"descripcion": "Opera recorridos", "permisos": ["FUN-36", "FUN-39"]}, headers=CABECERA_ADMIN)
    app.dependency_overrides[obtener_sesion] = lambda: SesionUsuario("91234567", "Coordinador de operaciones")
    r = cliente.put(RUTA, json=CUERPO)
    assert r.status_code == 403
    j = r.json()
    assert j["mensaje"] == "No tiene permiso para configurar roles"
    assert j["errores"][0]["detalle"] == "El rol Coordinador de operaciones no tiene autorizada la operación FUN-11"


# ---------- Pruebas unitarias del validador ----------

def test_normaliza_permisos_quita_espacios_y_duplicados():
    assert rol_validador.normalizar_permisos([" fun-11", "FUN-11", "FUN-12 "]) == ["FUN-11", "FUN-12"]


def test_valida_permisos_contra_operaciones_del_sistema():
    with pytest.raises(DatosNoValidos) as e:
        rol_validador.validar_operaciones(["FUN-11", "FUN-99"], {"FUN-11"})
    assert e.value.errores == [{"campo": "permisos", "detalle": "La operación FUN-99 no existe en el sistema"}]


def test_nombre_vacio_no_es_valido():
    with pytest.raises(DatosNoValidos) as e:
        rol_validador.validar_datos_basicos("   ", ["FUN-11"])
    assert e.value.errores[0]["campo"] == "nombre"


def test_cuerpo_sin_permisos_responde_422_en_espanol(cliente):
    r = cliente.put(RUTA, json={"descripcion": "x"}, headers=CABECERA_ADMIN)
    assert r.status_code == 422
    assert r.json()["errores"] == [{"campo": "permisos", "detalle": "El campo es obligatorio"}]
