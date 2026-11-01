# normalizador-leads-meta

CLI en Python que limpia exportaciones CSV de Meta Lead Ads: teléfonos peruanos en formato +51, emails, nombres y duplicados.

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green)
![CI](https://github.com/angel-cm-dev/normalizador-leads-meta/actions/workflows/ci.yml/badge.svg)

## Características

- **Teléfonos peruanos a E.164**: acepta `p:+51987654321`, `0051 987-654-321`, `987 654 321`, `(01) 234-5678`, `044 123456`… y los convierte a `+51…`, distinguiendo móvil y fijo (Lima y códigos de área de provincia).
- **Emails**: minúsculas, sin espacios, validación por patrón y corrección de dominios mal escritos (`gmial.com`, `gmail.con`, `hotmial.com`…).
- **Nombres**: elimina emojis y números, colapsa espacios y aplica mayúsculas tipo título respetando partículas (`María López de la Cruz`).
- **Deduplicación** por teléfono o email, conservando el lead más antiguo e indicando de cuál es duplicado.
- **Estados** por lead: `valido`, `duplicado` o `invalido` (sin teléfono ni email utilizable), con observaciones.
- Lee CSV en **UTF-8 o UTF-16 con tabulaciones** (formato real de descarga de Meta) y columnas en inglés o español.
- Exporta CSV limpio (UTF-8 con BOM, listo para Excel) y un resumen en consola o JSON.
- Sin dependencias externas: solo biblioteca estándar.

## Requisitos

- Python 3.10 o superior
- `pytest` (solo para ejecutar las pruebas)

## Instalación y uso

```bash
git clone https://github.com/angel-cm-dev/normalizador-leads-meta.git
cd normalizador-leads-meta

# Ejecutar directamente como módulo
python -m normalizador_leads ejemplos/leads_meta.csv -o leads_limpios.csv -r resumen.json

# O instalarlo como comando
pip install .
normalizar-leads ejemplos/leads_meta.csv --solo-validos
```

Opciones:

| Opción | Descripción |
| --- | --- |
| `-o, --salida` | Ruta del CSV limpio (por defecto `<entrada>_limpio.csv`) |
| `-r, --resumen` | Guarda el resumen en JSON |
| `--solo-validos` | Exporta solo los leads con estado `valido` |

## Ejemplo de uso

```text
$ python -m normalizador_leads ejemplos/leads_meta.csv -o leads_limpios.csv
Resumen de leads
--------------------------------
Total                          9
Validos                        6
Invalidos                      1
Duplicados                     2
Emails corregidos              2
Teléfonos válidos     fijo: 2, movil: 4
Por plataforma        fb: 4, ig: 2

CSV limpio: leads_limpios.csv (9 filas)
```

Entrada → salida (extracto):

| Original | Normalizado |
| --- | --- |
| `  maria   lopez DE la cruz ` / `p:+51987654321` | `Maria Lopez de la Cruz` / `+51987654321` (movil) |
| `juan.perez@gmial.com` | `juan.perez@gmail.com` (dominio corregido) |
| `(01) 234-5678` | `+5112345678` (fijo) |
| `51987654321` + mismo email | `duplicado de l:1001` |

## Estructura del proyecto

```text
normalizador-leads-meta/
├── normalizador_leads/
│   ├── __init__.py
│   ├── __main__.py        # permite `python -m normalizador_leads`
│   ├── cli.py             # argumentos, resumen y escritura
│   └── normalizar.py      # reglas de teléfono, email, nombre y deduplicación
├── ejemplos/
│   └── leads_meta.csv     # datos ficticios
├── tests/
├── .github/workflows/ci.yml
├── pyproject.toml
└── requirements.txt
```

## Pruebas

```bash
pip install -r requirements.txt
python -m pytest -v
```

## Roadmap

- [ ] Envío directo de leads válidos a un webhook (n8n / CRM).
- [ ] Detección de nombres sospechosos (`test`, `prueba`, `asdf`).
- [ ] Soporte para otros países de LATAM.

## Licencia y autor

Distribuido bajo licencia [MIT](LICENSE).

Desarrollado por **Angel Castañeda Meza** — Ingeniero de Sistemas, Lima, Perú · [github.com/angel-cm-dev](https://github.com/angel-cm-dev)
