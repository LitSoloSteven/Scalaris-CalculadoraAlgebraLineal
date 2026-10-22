"""Modelos de datos para taxonomía y navegación de Scalaris."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Pilar:
    """Representa una categoría superior o pilar conceptual en Scalaris."""

    identificador: str
    nombre: str
    icono: str = ""
    nombre_corto: str = ""
    prefijo: str = ""


@dataclass(frozen=True)
class Herramienta:
    """Representa una herramienta interactiva dentro de la suite."""

    identificador: str
    nombre: str
    descriptor: str
    ruta: str
    identificador_pilar: str
    icono: str
    titulo_pagina: str
    ejemplo_latex: str
    habilitada: bool = True


@dataclass(frozen=True)
class RedireccionHeredada:
    """Define una regla de redirección desde una ruta previa hacia la canónica."""

    ruta: str
    ruta_destino: str
    consulta_fija: tuple[tuple[str, str], ...] = ()
    permanente: bool = True


@dataclass(frozen=True)
class ElementoNavegacion:
    """Elemento interactivo de navegación contextual para pilares y escenas."""

    clave: str
    etiqueta: str
    etiqueta_corta: str
    descriptor: str
    icono: str
    ruta: str
    consulta: tuple[tuple[str, str], ...]
    identificador_herramienta: str
