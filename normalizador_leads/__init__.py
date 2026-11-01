"""Normalizador de leads exportados desde Meta Lead Ads."""

from .normalizar import (
    normalizar_email,
    normalizar_nombre,
    normalizar_telefono,
    procesar_leads,
)

__all__ = [
    "normalizar_email",
    "normalizar_nombre",
    "normalizar_telefono",
    "procesar_leads",
]
__version__ = "1.0.0"
