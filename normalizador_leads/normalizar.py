"""Reglas de normalización para leads de Meta Lead Ads (Perú)."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Códigos de área de telefonía fija en Perú (sin el 0 de larga distancia).
# Lima es "1"; provincias usan dos dígitos.
CODIGOS_AREA_PROVINCIA = {
    "41", "42", "43", "44", "51", "52", "53", "54", "56", "61", "62", "63",
    "64", "65", "66", "67", "72", "73", "74", "76", "82", "83", "84",
}

# Errores de tipeo frecuentes en dominios de correo.
DOMINIOS_CORREGIDOS = {
    "gmial.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gmail.con": "gmail.com",
    "gmail.co": "gmail.com",
    "gmail.cm": "gmail.com",
    "hotmial.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "hotmal.com": "hotmail.com",
    "outlok.com": "outlook.com",
    "outlook.con": "outlook.com",
    "yahooo.com": "yahoo.com",
    "yahoo.con": "yahoo.com",
}

PARTICULAS = {"de", "del", "la", "las", "los", "y", "da", "van", "von"}

PATRON_EMAIL = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$")

# Alias de columnas: Meta exporta en inglés o en español según el idioma de la cuenta.
ALIAS_COLUMNAS = {
    "id": ("id",),
    "fecha": ("created_time", "fecha_de_creacion", "fecha"),
    "nombre": ("full_name", "nombre_completo", "nombre"),
    "email": ("email", "correo_electronico", "correo"),
    "telefono": ("phone_number", "numero_de_telefono", "telefono", "celular"),
    "campania": ("campaign_name", "nombre_de_la_campana", "campania"),
    "anuncio": ("ad_name", "nombre_del_anuncio"),
    "formulario": ("form_name", "nombre_del_formulario"),
    "plataforma": ("platform", "plataforma"),
}

COLUMNAS_SALIDA = [
    "id", "fecha", "nombre", "email", "telefono", "tipo_telefono",
    "campania", "anuncio", "formulario", "plataforma", "estado", "observaciones",
]


def _sin_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _clave_columna(nombre: str) -> str:
    return re.sub(r"\W+", "_", _sin_tildes(nombre).strip().lower()).strip("_")


def normalizar_telefono(valor: str | None) -> tuple[str | None, str | None]:
    """Devuelve (telefono_E164, tipo) con tipo 'movil' o 'fijo'; (None, None) si es inválido.

    Acepta formatos como 'p:+51987654321', '0051 987-654-321', '(01) 234-5678' o '044 123456'.
    """
    if not valor:
        return None, None
    digitos = re.sub(r"\D", "", valor)
    if digitos.startswith("00"):
        digitos = digitos[2:]
    # El código de país solo se retira si el número es lo bastante largo
    # (evita confundirlo con el código de área 51 de Puno).
    if digitos.startswith("51") and len(digitos) >= 10:
        digitos = digitos[2:]
    if digitos.startswith("0"):
        digitos = digitos[1:]

    if len(digitos) == 9 and digitos.startswith("9"):
        return f"+51{digitos}", "movil"
    if len(digitos) == 8 and digitos.startswith("1"):
        return f"+51{digitos}", "fijo"
    if len(digitos) == 8 and digitos[:2] in CODIGOS_AREA_PROVINCIA:
        return f"+51{digitos}", "fijo"
    return None, None


def normalizar_email(valor: str | None) -> tuple[str | None, bool]:
    """Devuelve (email_normalizado, fue_corregido). El email es None si no es válido."""
    if not valor:
        return None, False
    email = re.sub(r"\s+", "", valor).lower()
    if email.count("@") != 1:
        return None, False
    usuario, dominio = email.split("@")
    corregido = dominio in DOMINIOS_CORREGIDOS
    dominio = DOMINIOS_CORREGIDOS.get(dominio, dominio)
    email = f"{usuario}@{dominio}"
    if not PATRON_EMAIL.match(email):
        return None, False
    return email, corregido


def normalizar_nombre(valor: str | None) -> str:
    """Limpia emojis, números y espacios; aplica mayúsculas tipo título respetando partículas."""
    if not valor:
        return ""
    limpio = "".join(
        c if (c.isalpha() or c in " '-") else " " for c in unicodedata.normalize("NFC", valor)
    )
    palabras = limpio.split()
    resultado = []
    for i, palabra in enumerate(palabras):
        minuscula = palabra.lower()
        if i > 0 and minuscula in PARTICULAS:
            resultado.append(minuscula)
        else:
            resultado.append("-".join(p.capitalize() for p in minuscula.split("-")))
    return " ".join(resultado)


def normalizar_fecha(valor: str | None) -> str:
    """Convierte '2026-10-01T09:15:22-0500' en '2026-10-01 09:15:22'. Si no se reconoce, la deja igual."""
    if not valor:
        return ""
    for formato in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(valor.strip(), formato).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return valor.strip()


@dataclass
class Resumen:
    total: int = 0
    validos: int = 0
    invalidos: int = 0
    duplicados: int = 0
    emails_corregidos: int = 0
    telefonos: Counter = field(default_factory=Counter)
    por_plataforma: Counter = field(default_factory=Counter)
    por_campania: Counter = field(default_factory=Counter)

    def como_dict(self) -> dict:
        return {
            "total": self.total,
            "validos": self.validos,
            "invalidos": self.invalidos,
            "duplicados": self.duplicados,
            "emails_corregidos": self.emails_corregidos,
            "telefonos": dict(self.telefonos),
            "por_plataforma": dict(self.por_plataforma),
            "por_campania": dict(self.por_campania),
        }


def leer_csv(ruta: str | Path) -> list[dict[str, str]]:
    """Lee el CSV detectando codificación (UTF-8 o UTF-16, como exporta Meta) y delimitador."""
    datos = Path(ruta).read_bytes()
    if datos.startswith((b"\xff\xfe", b"\xfe\xff")):
        texto = datos.decode("utf-16")
    else:
        texto = datos.decode("utf-8-sig")
    try:
        dialecto = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;\t")
        delimitador = dialecto.delimiter
    except (csv.Error, IndexError):
        delimitador = ","
    return list(csv.DictReader(io.StringIO(texto), delimiter=delimitador))


def _mapear_columnas(fila: dict[str, str]) -> dict[str, str]:
    por_clave = {_clave_columna(k): (v or "") for k, v in fila.items() if k is not None}
    mapeada = {}
    for destino, alias in ALIAS_COLUMNAS.items():
        mapeada[destino] = next((por_clave[a] for a in alias if a in por_clave), "")
    return mapeada


def procesar_leads(filas: list[dict[str, str]]) -> tuple[list[dict[str, str]], Resumen]:
    """Normaliza, valida y deduplica. Conserva el lead más antiguo de cada grupo duplicado."""
    resumen = Resumen()
    leads = [_mapear_columnas(f) for f in filas]
    for lead in leads:
        lead["fecha"] = normalizar_fecha(lead["fecha"])
    leads.sort(key=lambda l: l["fecha"])

    vistos: dict[str, str] = {}
    salida = []
    for lead in leads:
        resumen.total += 1
        observaciones = []
        telefono, tipo = normalizar_telefono(lead["telefono"])
        email, corregido = normalizar_email(lead["email"])
        nombre = normalizar_nombre(lead["nombre"])

        if lead["telefono"] and not telefono:
            observaciones.append("telefono invalido")
        if lead["email"] and not email:
            observaciones.append("email invalido")
        if corregido:
            observaciones.append("dominio de email corregido")
            resumen.emails_corregidos += 1
        if not nombre:
            observaciones.append("sin nombre")

        claves = [c for c in (telefono, email) if c]
        original = next((vistos[c] for c in claves if c in vistos), None)
        if not claves:
            estado = "invalido"
            resumen.invalidos += 1
        elif original:
            estado = "duplicado"
            observaciones.append(f"duplicado de {original}")
            resumen.duplicados += 1
            # Registra los datos nuevos del duplicado para detectar coincidencias encadenadas.
            for clave in claves:
                vistos.setdefault(clave, original)
        else:
            estado = "valido"
            resumen.validos += 1
            for clave in claves:
                vistos[clave] = lead["id"]
            if tipo:
                resumen.telefonos[tipo] += 1
            resumen.por_plataforma[lead["plataforma"] or "desconocida"] += 1
            resumen.por_campania[lead["campania"] or "sin campaña"] += 1

        salida.append({
            "id": lead["id"],
            "fecha": lead["fecha"],
            "nombre": nombre,
            "email": email or "",
            "telefono": telefono or "",
            "tipo_telefono": tipo or "",
            "campania": lead["campania"].strip(),
            "anuncio": lead["anuncio"].strip(),
            "formulario": lead["formulario"].strip(),
            "plataforma": lead["plataforma"].strip(),
            "estado": estado,
            "observaciones": "; ".join(observaciones),
        })
    return salida, resumen


def escribir_csv(ruta: str | Path, filas: list[dict[str, str]]) -> None:
    """Escribe en UTF-8 con BOM para que Excel muestre bien las tildes."""
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_SALIDA)
        escritor.writeheader()
        escritor.writerows(filas)
