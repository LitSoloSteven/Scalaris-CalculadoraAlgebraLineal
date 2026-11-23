"""Proyección del catálogo en el orden de lectura del directorio de inicio."""
from dataclasses import dataclass, replace
from functools import cached_property

from src.frontend.navegacion.catalogo import PILARES
from src.frontend.navegacion.consultas import elementos_navegacion, herramientas_visibles, pilar_de
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

    @property
    def icono(self) -> str:
        """Identifica el símbolo que comparten la portada y la barra."""
        return f"seccion-{self.identificador}"

    @cached_property
    def accesos(self) -> tuple[ElementoNavegacion, ...]:
        """Devuelve los accesos en orden, incluidos los subgrupos."""
        return tuple(acceso for grupo in self.grupos for acceso in grupo.accesos)


_GruposPorClave = tuple[tuple[str | None, tuple[str, ...]], ...]
_DefinicionSeccion = tuple[str, str, _GruposPorClave]

_SECCIONES: tuple[_DefinicionSeccion, ...] = (
    ("sistemas-lineales", "Sistemas lineales", ((None, ("sistemas", "metodos_iterativos", "leontief")),)),
    ("matrices", "Matrices", ((None, ("matrices", "inversa", "determinantes", "factorizacion_lu")),)),
    ("vectores-geometria", "Vectores y geometría", (
        (None, ("vectores", "transformaciones")),
        (pilar_de("visualizador").nombre, ("vis:rectas-planos", "vis:vectores", "vis:combinacion")),
    )),
    ("metodos-numericos", "Métodos numéricos", (("Raíces de ecuaciones", ("metodos_cerrados", "metodos_abiertos")),)),
    ("sistemas-numeracion", "Sistemas de numeración", ((None, ("bases", "romanos")),)),
)

_SECCIONES_POR_CLAVE = {
    clave: (identificador, titulo, grupos)
    for identificador, titulo, grupos in _SECCIONES
    for _, claves in grupos for clave in claves
}

_ETIQUETAS_INICIO = {
    "matrices": "Operaciones con matrices",
    "transformaciones": "Transformaciones lineales",
}


def _resolver_grupos(
    grupos: _GruposPorClave, elementos: dict[str, ElementoNavegacion]
) -> tuple[GrupoInicio, ...]:
    resultado = []
    for subtitulo, claves in grupos:
        accesos = tuple(elementos[clave] for clave in claves if clave in elementos)
        if accesos:
            resultado.append(GrupoInicio(subtitulo, accesos))
    return tuple(resultado)


def _elementos_habilitados() -> dict[str, ElementoNavegacion]:
    """Recupera los accesos vigentes con las etiquetas del directorio."""
    habilitadas = {herramienta.identificador for herramienta in herramientas_visibles()}
    elementos = {
        elemento.clave: elemento
        for pilar in PILARES
        for elemento in elementos_navegacion(pilar.identificador)
        if elemento.identificador_herramienta in habilitadas
    }
    for clave, etiqueta in _ETIQUETAS_INICIO.items():
        if clave in elementos:
            elementos[clave] = replace(elementos[clave], etiqueta=etiqueta)
    return elementos


def _resolver_seccion(
    definicion: _DefinicionSeccion, elementos: dict[str, ElementoNavegacion]
) -> SeccionInicio | None:
    """Proyecta una sección si conserva algún acceso habilitado."""
    identificador, titulo, grupos = definicion
    grupos_resueltos = _resolver_grupos(grupos, elementos)
    return SeccionInicio(identificador, titulo, grupos_resueltos) if grupos_resueltos else None


def secciones_inicio() -> tuple[SeccionInicio, ...]:
    """Devuelve las secciones del directorio con los accesos habilitados del catálogo."""
    elementos = _elementos_habilitados()
    return tuple(seccion for definicion in _SECCIONES
                 if (seccion := _resolver_seccion(definicion, elementos)) is not None)


def seccion_por_clave(clave: str | None) -> SeccionInicio | None:
    """Resuelve la sección de un acceso habilitado por su clave de herramienta o escena."""
    definicion = _SECCIONES_POR_CLAVE.get(clave) if clave is not None else None
    if definicion is None:
        return None
    elementos = _elementos_habilitados()
    return _resolver_seccion(definicion, elementos) if clave in elementos else None
