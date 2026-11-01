import pytest

from normalizador_leads import (
    normalizar_email,
    normalizar_nombre,
    normalizar_telefono,
    procesar_leads,
)
from normalizador_leads.normalizar import normalizar_fecha


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("p:+51987654321", ("+51987654321", "movil")),
        ("987 654 321", ("+51987654321", "movil")),
        ("0051 912-345-678", ("+51912345678", "movil")),
        ("51987654321", ("+51987654321", "movil")),
        ("(01) 234-5678", ("+5112345678", "fijo")),
        ("+51 044 123456", ("+5144123456", "fijo")),
        ("051 123456", ("+5151123456", "fijo")),
        ("12345", (None, None)),
        ("887654321", (None, None)),
        ("", (None, None)),
        (None, (None, None)),
    ],
)
def test_normalizar_telefono(entrada, esperado):
    assert normalizar_telefono(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Maria.Lopez@GMAIL.com", ("maria.lopez@gmail.com", False)),
        (" ana@outlook.com ", ("ana@outlook.com", False)),
        ("juan@gmial.com", ("juan@gmail.com", True)),
        ("pedro@gmail.con", ("pedro@gmail.com", True)),
        ("rosa@hotmail", (None, False)),
        ("sin-arroba.com", (None, False)),
        ("a@@b.com", (None, False)),
        ("", (None, False)),
    ],
)
def test_normalizar_email(entrada, esperado):
    assert normalizar_email(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("  maria   lopez DE la cruz ", "Maria Lopez de la Cruz"),
        ("JUAN PEREZ", "Juan Perez"),
        ("Rosa Quispe 😊", "Rosa Quispe"),
        ("ana sofía ramírez", "Ana Sofía Ramírez"),
        ("jean-pierre 123", "Jean-Pierre"),
        ("De la Torre", "De la Torre"),
        ("", ""),
    ],
)
def test_normalizar_nombre(entrada, esperado):
    assert normalizar_nombre(entrada) == esperado


def test_normalizar_fecha_meta():
    assert normalizar_fecha("2026-10-01T09:15:22-0500") == "2026-10-01 09:15:22"
    assert normalizar_fecha("no es fecha") == "no es fecha"


def _fila(id_, fecha, nombre, email, telefono, plataforma="fb"):
    return {
        "id": id_, "created_time": fecha, "full_name": nombre, "email": email,
        "phone_number": telefono, "campaign_name": "Camp", "ad_name": "Ad",
        "form_name": "Form", "platform": plataforma,
    }


def test_procesar_deduplica_por_telefono_y_email():
    filas = [
        _fila("l:2", "2026-10-02T10:00:00-0500", "Ana", "ana@gmail.com", "999111222"),
        _fila("l:1", "2026-10-01T10:00:00-0500", "Ana R", "ana@gmail.com", ""),
        _fila("l:3", "2026-10-03T10:00:00-0500", "Otra", "otra@gmail.com", "+51 999 111 222"),
    ]
    salida, resumen = procesar_leads(filas)
    # Se ordena por fecha y se conserva el más antiguo
    assert [l["id"] for l in salida] == ["l:1", "l:2", "l:3"]
    assert [l["estado"] for l in salida] == ["valido", "duplicado", "duplicado"]
    assert "duplicado de l:1" in salida[1]["observaciones"]
    assert resumen.validos == 1 and resumen.duplicados == 2


def test_procesar_marca_invalidos():
    salida, resumen = procesar_leads([_fila("l:9", "2026-10-01T10:00:00-0500", "test", "test@test", "12345")])
    assert salida[0]["estado"] == "invalido"
    assert "telefono invalido" in salida[0]["observaciones"]
    assert "email invalido" in salida[0]["observaciones"]
    assert resumen.invalidos == 1


def test_procesar_acepta_columnas_en_espanol():
    filas = [{
        "id": "x1", "fecha_de_creación": "2026-10-01", "nombre_completo": "luis díaz",
        "correo_electrónico": "luis@yahoo.com", "número_de_teléfono": "912345678",
    }]
    salida, _ = procesar_leads(filas)
    assert salida[0]["nombre"] == "Luis Díaz"
    assert salida[0]["telefono"] == "+51912345678"
    assert salida[0]["email"] == "luis@yahoo.com"
