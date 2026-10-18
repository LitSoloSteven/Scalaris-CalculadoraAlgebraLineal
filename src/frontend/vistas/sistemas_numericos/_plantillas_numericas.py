"""Renderizado de plantillas numéricas con escape de todos los valores de texto."""

from functools import lru_cache
from html import escape
from pathlib import Path
from string import Template
from typing import Any

_RUTA_PLANTILLAS = Path(__file__).resolve().parents[2] / "recursos" / "plantillas"


@lru_cache(maxsize=None)
def _leer_plantilla(nombre: str) -> Template:
    return Template((_RUTA_PLANTILLAS / f"numericos_{nombre}.html").read_text(encoding="utf-8"))


def renderizar_plantilla(nombre: str, valores: dict[str, Any]) -> str:
    """Sustituye valores de texto escapados en una plantilla interna existente."""
    return _leer_plantilla(nombre).substitute({
        clave: escape(str(valor)) for clave, valor in valores.items()
    })


def renderizar_tabla(encabezados: tuple[str, ...], filas: list[str], pie: str = "") -> str:
    """Compone filas y pie ya renderizados; escapa cada título de columna."""
    titulos = "".join(f"<th scope='col'>{escape(titulo)}</th>" for titulo in encabezados)
    return _leer_plantilla("tabla").substitute(encabezados=titulos, filas="".join(filas), pie=pie)


def renderizar_lectura(tabla: str, lectura: str) -> str:
    """Compone una tabla interna renderizada y una orientación de lectura escapada."""
    return _leer_plantilla("lectura").substitute(tabla=tabla, lectura=escape(str(lectura)))
