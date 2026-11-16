"""Manejo de contraseñas, credenciales temporales y tokens de sesión.

Las contraseñas se guardan con PBKDF2-SHA256 y sal aleatoria; nunca en texto plano.
"""

import hashlib
import os
import secrets
import string

# Se puede ajustar con la variable HASH_ITERACIONES (por ejemplo, para pruebas).
ITERACIONES = int(os.getenv("HASH_ITERACIONES", "210000"))
_ALFABETO = string.ascii_letters + string.digits


def generar_hash(contrasena: str) -> str:
    sal = secrets.token_hex(16)
    calculado = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal}${calculado.hex()}"


def generar_temporal(longitud: int = 12) -> str:
    """Credencial temporal con letras y dígitos."""
    while True:
        valor = "".join(secrets.choice(_ALFABETO) for _ in range(longitud))
        if any(c.isdigit() for c in valor) and any(c.isalpha() for c in valor):
            return valor
