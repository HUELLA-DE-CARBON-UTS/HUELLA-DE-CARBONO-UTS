"""Servicio de correo (API-EXT-04) que usan los endpoints."""

from app.repositories.adapters.correo_smtp import obtener_servicio_correo


def get_servicio_correo():
    return obtener_servicio_correo()
