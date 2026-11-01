import csv
import json
from pathlib import Path

from normalizador_leads.cli import main

EJEMPLO = Path(__file__).resolve().parent.parent / "ejemplos" / "leads_meta.csv"


def _leer(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_cli_con_csv_de_ejemplo(tmp_path, capsys):
    salida = tmp_path / "limpio.csv"
    resumen = tmp_path / "resumen.json"
    codigo = main([str(EJEMPLO), "-o", str(salida), "-r", str(resumen)])

    assert codigo == 0
    filas = _leer(salida)
    assert len(filas) == 9
    estados = {f["id"]: f["estado"] for f in filas}
    assert estados["l:1004"] == "duplicado"  # mismo teléfono y email que l:1001
    assert estados["l:1008"] == "duplicado"  # mismo teléfono que l:1002
    assert estados["l:1006"] == "invalido"

    datos = json.loads(resumen.read_text(encoding="utf-8"))
    assert datos == {
        "total": 9, "validos": 6, "invalidos": 1, "duplicados": 2, "emails_corregidos": 2,
        "telefonos": {"movil": 4, "fijo": 2},
        "por_plataforma": {"fb": 4, "ig": 2},
        "por_campania": {"Campaña Octubre": 6},
    }
    assert "CSV limpio" in capsys.readouterr().out


def test_cli_solo_validos(tmp_path):
    salida = tmp_path / "validos.csv"
    assert main([str(EJEMPLO), "-o", str(salida), "--solo-validos"]) == 0
    assert {f["estado"] for f in _leer(salida)} == {"valido"}


def test_cli_lee_utf16_con_tabulaciones(tmp_path):
    entrada = tmp_path / "meta_utf16.csv"
    contenido = "id\tcreated_time\tfull_name\temail\tphone_number\n" \
                "l:1\t2026-10-01T09:00:00-0500\tJosé Ñañez\tjose@gmail.com\tp:+51955444333\n"
    entrada.write_text(contenido, encoding="utf-16")
    salida = tmp_path / "out.csv"
    assert main([str(entrada), "-o", str(salida)]) == 0
    fila = _leer(salida)[0]
    assert fila["nombre"] == "José Ñañez"
    assert fila["telefono"] == "+51955444333"


def test_cli_archivo_inexistente(tmp_path, capsys):
    assert main([str(tmp_path / "no_existe.csv")]) == 1
    assert "no existe" in capsys.readouterr().err
