# HUELLA-DE-CARBONO-UTS
Proyecto de WebService

## Ejecutar

1. Copiar `.env.example` como `.env` y definir `TOKEN_ADMIN_INICIAL`.
2. `pip install -r requirements.txt`
3. `uvicorn main:app --reload` y abrir http://127.0.0.1:8000/docs

Al iniciar se crean las tablas, el catálogo de operaciones FUN-01 a FUN-65 y el rol
"Administrador" (ROL-01). Mientras no exista el inicio de sesión (HU-06), las
solicitudes se autentican con `Authorization: Bearer <TOKEN_ADMIN_INICIAL>`.

## Pruebas

`python -m pytest -v`
