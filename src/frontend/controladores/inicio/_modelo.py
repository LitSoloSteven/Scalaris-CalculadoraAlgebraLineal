"""Datos canónicos para el acceso destacado y el ejemplo de la portada."""
from dataclasses import dataclass

from src.frontend.controladores.inicio._recientes import (
    IDENTIFICADOR_DESTACADA_PREDETERMINADA,
    elegir_acceso_destacado,
)
from src.frontend.navegacion import (
    ElementoNavegacion,
    Herramienta,
    enlace_elemento_navegacion,
    herramienta_por_identificador,
)

_TITULOS_PORTADA: dict[str, str] = {
    "vis:vectores": "Vectores del Visualizador",
}


@dataclass(frozen=True)
class EstadoPortada:
    """Estado único que sincroniza título, enlace destacado y ejemplo de portada."""

    clave: str
    titulo: str
    enlace: str
    texto_destacado: str
    hay_historial: bool


def acceso_destacado() -> Herramienta:
    """Devuelve el acceso de Sistemas que comparten el destacado y el ejemplo."""
    return herramienta_por_identificador(IDENTIFICADOR_DESTACADA_PREDETERMINADA)


def titulo_portada(acceso: ElementoNavegacion) -> str:
    """Devuelve el título legible del acceso para el destacado y el ejemplo."""
    return _TITULOS_PORTADA.get(acceso.clave, acceso.etiqueta)


def estado_portada(datos_crudos=None) -> EstadoPortada:
    """Resuelve en un único estado el título, el vínculo de retorno y el ejemplo."""
    acceso, hay_historial = elegir_acceso_destacado(datos_crudos)
    titulo = titulo_portada(acceso)
    if hay_historial:
        texto_destacado = f"Retomar {titulo}"
    elif acceso.clave == IDENTIFICADOR_DESTACADA_PREDETERMINADA:
        texto_destacado = "Resolver un sistema"
    else:
        texto_destacado = f"Abrir {titulo}"
    return EstadoPortada(
        clave=acceso.clave,
        titulo=titulo,
        enlace=enlace_elemento_navegacion(acceso),
        texto_destacado=texto_destacado,
        hay_historial=hay_historial,
    )
