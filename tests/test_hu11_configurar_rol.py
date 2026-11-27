import pytest
from sqlalchemy.exc import OperationalError

from app.domain.exceptions.errores import DatosNoValidos
from app.services.validators import rol_validador

RUTA = "/api/v1/roles/Analista%20ambiental"
NUEVE = ["FUN-41", "FUN-42", "FUN-49", "FUN-50", "FUN-53", "FUN-54", "FUN-56", "FUN-57", "FUN-61"]
CUERPO = {"description": "Consulta consumo, emisiones, indicadores y reportes", "permissions": NUEVE}


def test_caso1_crea_rol_nuevo(admin):
    r = admin.put(RUTA, json=CUERPO)
    assert r.status_code == 201
    j = r.json()
    assert j["success"] is True
    assert j["message"] == "Rol configurado correctamente"
    assert j["data"]["action"] == "created"
    assert j["data"]["status"] == "active"
    assert j["data"]["permissions"] == NUEVE
    assert j["data"]["roleId"] == "ROL-02"


def test_caso2_operacion_inexistente(admin):
    r = admin.put(RUTA, json={**CUERPO, "permissions": ["FUN-41", "FUN-99"]})
    assert r.status_code == 422
    j = r.json()
    assert j["success"] is False
    assert j["data"] is None
    assert j["message"] == "La configuración del rol no es válida"
    assert j["errors"] == [{"field": "permissions", "detail": "La operación FUN-99 no existe en el sistema"}]


def test_caso3_estructura_estandar(admin):
    j = admin.put(RUTA, json=CUERPO).json()
    assert set(j) == {"success", "status", "message", "data", "errors", "metadata"}
    assert isinstance(j["success"], bool) and isinstance(j["status"], int) and isinstance(j["message"], str)
    assert j["errors"] == []
    assert j["metadata"]["feature"] == "FUN-11"
    assert "timestamp" in j["metadata"]
    assert set(j["data"]) == {"roleId", "name", "description", "status", "permissions", "action"}


def test_caso4_sin_permisos(admin):
    r = admin.put(RUTA, json={**CUERPO, "permissions": []})
    assert r.status_code == 422
    assert {"field": "permissions", "detail": "El rol debe tener al menos un permiso"} in r.json()["errors"]


def test_caso5_base_de_datos_no_disponible(admin, monkeypatch):
    from app.repositories.adapters.rol_repositorio_sqlalchemy import RolRepositorioSQLAlchemy

    def falla(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(RolRepositorioSQLAlchemy, "operaciones_existentes", falla)
    r = admin.put(RUTA, json=CUERPO)
    assert r.status_code == 503
    assert r.json()["success"] is False
    assert r.json()["message"] == "No fue posible guardar la configuración del rol"


def test_reemplaza_permisos_de_rol_existente_sin_duplicados(admin):
    admin.put(RUTA, json=CUERPO)
    r = admin.put(RUTA, json={"description": "", "permissions": ["FUN-56", "FUN-57", "FUN-56"]})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["action"] == "updated"
    assert d["roleId"] == "ROL-02"
    assert d["permissions"] == ["FUN-56", "FUN-57"]
    assert d["description"] == CUERPO["description"]


def test_registra_fecha_y_responsable(admin, db):
    from app.repositories.database.modelos import RolModelo
    admin.put(RUTA, json=CUERPO)
    with db() as s:
        rol = s.query(RolModelo).filter_by(nombre="Analista ambiental").one()
        assert rol.responsable == "1000000000"
        assert rol.fecha_actualizacion is not None


def test_sin_sesion_responde_401(cliente):
    r = cliente.put(RUTA, json=CUERPO)
    assert r.status_code == 401
    assert r.json()["success"] is False


def test_rol_sin_permiso_fun11_responde_403(admin, db):
    from app.repositories.database import modelos
    from app.domain.value_objects.fecha import ahora
    from app.services.seguridad.contrasenas import generar_hash
    admin.put("/api/v1/roles/Coordinador%20de%20operaciones",
              json={"description": "Opera recorridos", "permissions": ["FUN-36", "FUN-39"]})
    with db() as s:
        rol = s.query(modelos.RolModelo).filter_by(nombre="Coordinador de operaciones").one()
        s.add(modelos.UsuarioModelo(id_usuario="USR-0002", documento="91234567", nombres="Jorge Pabón",
                                    correo="jpabon@empresa.co", telefono="", id_sede=None, estado="activo",
                                    fecha_creacion=ahora(), responsable="1000000000"))
        s.flush()
        s.add(modelos.CredencialModelo(documento="91234567", hash_contrasena=generar_hash("Clave-Coordinador-1"),
                                       temporal=False, usada=False, id_rol=rol.id_rol, fecha_actualizacion=ahora()))
        s.commit()
    del admin.headers["Authorization"]
    ingreso = admin.post("/api/v1/auth/sesiones", json={"username": "91234567", "password": "Clave-Coordinador-1"})
    admin.headers["Authorization"] = "Bearer " + ingreso.headers["X-Token-Sesion"]
    r = admin.put(RUTA, json=CUERPO)
    assert r.status_code == 403
    j = r.json()
    assert j["success"] is False
    assert j["message"] == "No tiene permiso para configurar roles"
    assert "FUN-11" in j["errors"][0]["detail"]


def test_normaliza_permisos_quita_espacios_y_duplicados():
    assert rol_validador.normalizar_permisos([" fun-11", "FUN-11", "FUN-12 "]) == ["FUN-11", "FUN-12"]


def test_valida_permisos_contra_operaciones_del_sistema():
    with pytest.raises(DatosNoValidos) as e:
        rol_validador.validar_operaciones(["FUN-11", "FUN-99"], {"FUN-11"})
    assert e.value.errores == [{"field": "permissions", "detail": "La operación FUN-99 no existe en el sistema"}]


def test_nombre_vacio_no_es_valido():
    with pytest.raises(DatosNoValidos) as e:
        rol_validador.validar_datos_basicos("   ", ["FUN-11"])
    assert e.value.errores[0]["field"] == "name"


def test_cuerpo_sin_permisos_responde_422(admin):
    r = admin.put(RUTA, json={"description": "x"})
    assert r.status_code == 422
    assert r.json()["success"] is False
    assert r.json()["errors"][0]["field"] == "permissions"
