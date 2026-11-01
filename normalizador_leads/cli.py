"""Interfaz de línea de comandos del normalizador de leads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .normalizar import escribir_csv, leer_csv, procesar_leads


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="normalizar-leads",
        description="Limpia exportaciones CSV de Meta Lead Ads: teléfonos +51, emails, nombres y duplicados.",
    )
    parser.add_argument("entrada", type=Path, help="CSV exportado desde Meta (UTF-8 o UTF-16)")
    parser.add_argument("-o", "--salida", type=Path, help="CSV limpio (por defecto: <entrada>_limpio.csv)")
    parser.add_argument("-r", "--resumen", type=Path, help="Guarda el resumen en JSON")
    parser.add_argument("--solo-validos", action="store_true", help="Exporta solo leads válidos")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def imprimir_resumen(resumen: dict) -> None:
    print("Resumen de leads")
    print("-" * 32)
    for clave in ("total", "validos", "invalidos", "duplicados", "emails_corregidos"):
        print(f"{clave.replace('_', ' ').capitalize():<22}{resumen[clave]:>10}")
    if resumen["telefonos"]:
        tipos = ", ".join(f"{k}: {v}" for k, v in sorted(resumen["telefonos"].items()))
        print(f"{'Teléfonos válidos':<22}{tipos:>10}")
    if resumen["por_plataforma"]:
        plataformas = ", ".join(f"{k}: {v}" for k, v in sorted(resumen["por_plataforma"].items()))
        print(f"{'Por plataforma':<22}{plataformas:>10}")


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    if not args.entrada.is_file():
        print(f"Error: no existe el archivo {args.entrada}", file=sys.stderr)
        return 1

    filas = leer_csv(args.entrada)
    if not filas:
        print("Error: el CSV no contiene filas", file=sys.stderr)
        return 1

    limpios, resumen = procesar_leads(filas)
    if args.solo_validos:
        limpios = [l for l in limpios if l["estado"] == "valido"]

    salida = args.salida or args.entrada.with_name(f"{args.entrada.stem}_limpio.csv")
    escribir_csv(salida, limpios)

    datos_resumen = resumen.como_dict()
    imprimir_resumen(datos_resumen)
    print(f"\nCSV limpio: {salida} ({len(limpios)} filas)")
    if args.resumen:
        args.resumen.write_text(json.dumps(datos_resumen, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Resumen JSON: {args.resumen}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
