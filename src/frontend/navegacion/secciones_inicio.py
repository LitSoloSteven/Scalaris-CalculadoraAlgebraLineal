"""Proyección del catálogo en el orden de lectura del directorio de inicio."""
from dataclasses import dataclass, replace

from src.frontend.navegacion.catalogo import PILARES
from src.frontend.navegacion.consultas import elementos_navegacion, pilar_de
from src.frontend.navegacion.modelo import ElementoNavegacion


@dataclass(frozen=True)
class GrupoInicio:
    """Reúne los accesos consecutivos con un subtítulo opcional."""

    subtitulo: str | None
    accesos: tuple[ElementoNavegacion, ...]


@dataclass(frozen=True)
class SeccionInicio:
    """Identifica una sección del directorio y sus grupos en orden de lectura."""

    identificador: str
    titulo: str
    grupos: tuple[GrupoInicio, ...]


_SECCIONES = (
    ("sistemas-lineales", "Sistemas lineales", ((None, ("sistemas", "leontief")),)),
    ("matrices", "Matrices", ((None, ("matrices", "inversa", "determinantes", "factorizacion_lu")),)),
    ("vectores-geometria", "Vectores y geometría", (
        (None, ("vectores", "transformaciones")),
        (pilar_de("visualizador").nombre, ("vis:rectas-planos", "vis:vectores", "vis:combinacion")),
    )),
    ("metodos-numericos", "Métodos numéricos", (("Raíces de ecuaciones", ("metodos_cerrados", "metodos_abiertos")),)),
    ("sistemas-numeracion", "Sistemas de numeración", ((None, ("bases", "romanos")),)),
)

_ETIQUETAS_INICIO = {
    "matrices": "Operaciones con matrices",
    "transformaciones": "Transformaciones lineales",
}


def secciones_inicio() -> tuple[SeccionInicio, ...]:
    """Devuelve las secciones del directorio con los accesos habilitados del catálogo."""
    elementos = {
        elemento.clave: elemento
        for pilar in PILARES
        for elemento in elementos_navegacion(pilar.identificador)
    }
    for clave, etiqueta in _ETIQUETAS_INICIO.items():
        if clave in elementos:
            elementos[clave] = replace(elementos[clave], etiqueta=etiqueta)

    return tuple(
        SeccionInicio(identificador, titulo, tuple(
            GrupoInicio(subtitulo, tuple(elementos[clave] for clave in claves if clave in elementos))
            for subtitulo, claves in grupos
        ))
        for identificador, titulo, grupos in _SECCIONES
    )
