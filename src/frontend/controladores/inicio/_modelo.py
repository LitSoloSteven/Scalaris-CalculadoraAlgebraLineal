"""Datos de presentacion de las tarjetas de inicio."""
from __future__ import annotations

from dataclasses import dataclass

from src.frontend.navegacion import (
    PILARES,
    predeterminado_elemento_clave,
    enlace_elemento_navegacion,
    elementos_navegacion,
    pilar_de,
)
from ._recientes import elegir_destacada


@dataclass(frozen=True)
class ModeloTarjeta:
    """Datos inmutables de una tarjeta de herramienta o escena."""
    clave: str
    identificador_herramienta: str
    nombre: str
    descripcion: str
    icono: str
    enlace: str


@dataclass(frozen=True)
class ModeloPilar:
    """Datos inmutables de un area y sus tarjetas."""
    identificador: str
    nombre_corto: str
    tarjetas: tuple[ModeloTarjeta, ...]
    icono: str = ""
    descripcion: str = ""
    unidad_singular: str = "herramienta"
    unidad_plural: str = "herramientas"


@dataclass(frozen=True)
class SeleccionInicial:
    """Estado de seleccion focal inicial deducido de historial o estado vacio."""
    identificador_pilar: str
    clave_tarjeta: str
    hay_historial: bool


METADATOS_PILARES: dict[str, dict[str, str]] = {
    "algebra": {
        "descripcion": "Sistemas, vectores, matrices, inversa y determinantes, con cada paso a la vista.",
        "unidad_singular": "herramienta",
        "unidad_plural": "herramientas",
    },
    "visualizador": {
        "descripcion": "Mira rectas, planos y vectores en 2D y 3D.",
        "unidad_singular": "escena",
        "unidad_plural": "escenas",
    },
    "utilidades": {
        "descripcion": "Convierte bases y opera con números romanos.",
        "unidad_singular": "herramienta",
        "unidad_plural": "herramientas",
    },
}


def formatear_cantidad_elementos(cantidad: int, singular: str = "herramienta", plural: str = "herramientas") -> str:
    """Devuelve el conteo con el plural correcto (probada con 0, 1 y N)."""
    unidad = singular if cantidad == 1 else plural
    return f"{cantidad} {unidad}"


def pilares_inicio() -> tuple[ModeloPilar, ...]:
    """Prepara las areas y tarjetas siguiendo el catalogo de navegacion."""
    pilares = []
    for pilar in PILARES:
        elementos = elementos_navegacion(pilar.identificador)
        tarjetas = tuple(
            ModeloTarjeta(
                clave=elemento.clave,
                identificador_herramienta=elemento.identificador_herramienta,
                nombre=elemento.etiqueta,
                descripcion=elemento.descriptor,
                icono=elemento.icono,
                enlace=enlace_elemento_navegacion(elemento),
            )
            for elemento in elementos
        )
        meta = METADATOS_PILARES.get(pilar.identificador, {})
        pilares.append(
            ModeloPilar(
                identificador=pilar.identificador,
                nombre_corto=pilar.nombre_corto,
                tarjetas=tarjetas,
                icono=pilar.icono,
                descripcion=meta.get("descripcion", ""),
                unidad_singular=meta.get("unidad_singular", "herramienta"),
                unidad_plural=meta.get("unidad_plural", "herramientas"),
            )
        )
    return tuple(pilares)


def seleccion_inicial(datos_crudos) -> SeleccionInicial:
    """Prepara la seleccion inicial o el estado orientativo cuando no hay historial."""
    try:
        herramienta, hay_historial = elegir_destacada(datos_crudos)
        identificador_pilar = pilar_de(herramienta.identificador).identificador
        clave_tarjeta = predeterminado_elemento_clave(herramienta.ruta)
        if clave_tarjeta is None:
            clave_tarjeta = "sistemas"
        return SeleccionInicial(identificador_pilar=identificador_pilar, clave_tarjeta=clave_tarjeta, hay_historial=hay_historial)
    except Exception:
        return SeleccionInicial(identificador_pilar="algebra", clave_tarjeta="sistemas", hay_historial=False)
