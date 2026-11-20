"""Proyección del catálogo en el orden de lectura del directorio de inicio."""
from dataclasses import dataclass, replace

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

    @property
    def accesos(self) -> tuple[ElementoNavegacion, ...]:
        """Devuelve los accesos en orden, incluidos los subgrupos."""
        return tuple(acceso for grupo in self.grupos for acceso in grupo.accesos)


_GruposPorClave = tuple[tuple[str | None, tuple[str, ...]], ...]

_SECCIONES: tuple[tuple[str, str, _GruposPorClave], ...] = (
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


def _resolver_grupos(
    grupos: _GruposPorClave, elementos: dict[str, ElementoNavegacion]
) -> tuple[GrupoInicio, ...]:
    resultado = []
    for subtitulo, claves in grupos:
        accesos = tuple(elementos[clave] for clave in claves if clave in elementos)
        if accesos:
            resultado.append(GrupoInicio(subtitulo, accesos))
    return tuple(resultado)


def secciones_inicio() -> tuple[SeccionInicio, ...]:
    """Devuelve las secciones del directorio con los accesos habilitados del catálogo."""
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

    secciones = []
    for identificador, titulo, grupos in _SECCIONES:
        grupos_resueltos = _resolver_grupos(grupos, elementos)
        if grupos_resueltos:
            secciones.append(SeccionInicio(identificador, titulo, grupos_resueltos))
    return tuple(secciones)


def seccion_por_clave(clave: str | None) -> SeccionInicio | None:
    """Resuelve la sección de un acceso habilitado por su clave de herramienta o escena."""
    if clave is None:
        return None
    return next((seccion for seccion in secciones_inicio()
                 if any(acceso.clave == clave for acceso in seccion.accesos)), None)
