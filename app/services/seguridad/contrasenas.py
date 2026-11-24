import hashlib
import hmac
import os
import secrets
import string

ITERACIONES = int(os.getenv("HASH_ITERACIONES", "210000"))
_ALFABETO = string.ascii_letters + string.digits


def generar_hash(contrasena: str) -> str:
    sal = secrets.token_hex(16)
    calculado = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal}${calculado.hex()}"


def verificar(contrasena: str, hash_guardado: str) -> bool:
    try:
        _, iteraciones, sal, esperado = hash_guardado.split("$")
        calculado = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), int(iteraciones))
    except ValueError:
        return False
    return hmac.compare_digest(calculado.hex(), esperado)


HASH_REFERENCIA = generar_hash(secrets.token_hex(8))


def generar_temporal(longitud: int = 12) -> str:
    while True:
        valor = "".join(secrets.choice(_ALFABETO) for _ in range(longitud))
        if any(c.isdigit() for c in valor) and any(c.isalpha() for c in valor):
            return valor


def generar_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def enmascarar_correo(correo: str) -> str:
    usuario, _, dominio = correo.partition("@")
    if len(usuario) <= 2:
        return f"{usuario[:1]}***@{dominio}"
    return f"{usuario[0]}***{usuario[-1]}@{dominio}"
