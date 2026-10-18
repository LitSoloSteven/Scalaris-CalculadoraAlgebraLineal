"""Funciones de consulta e introspección sobre el catálogo de navegación."""
import urllib.parse

from src.frontend.navegacion.catalogo import (
    PILARES,
    HERRAMIENTAS,
    ESCENAS_VISUALIZADOR,
    _PILARES_POR_IDENTIFICADOR,
    _ETIQUETAS_CORTAS,
    _HERRAMIENTAS_POR_IDENTIFICADOR,
)
from src.frontend.navegacion.modelo import ElementoNavegacion, Pilar, Herramienta


def herramienta_por_identificador(identificador_herramienta: str) -> Herramienta:
    """Devuelve la herramienta del identificador; lanza KeyError si no existe en el catálogo."""
    if identificador_herramienta not in _HERRAMIENTAS_POR_IDENTIFICADOR:
        raise KeyError(f"Herramienta no encontrada en el registro: '{identificador_herramienta}'")
    return _HERRAMIENTAS_POR_IDENTIFICADOR[identificador_herramienta]


def ruta_de(identificador_herramienta: str) -> str:
    """Devuelve la ruta canónica asociada a la herramienta."""
    return herramienta_por_identificador(identificador_herramienta).ruta


def herramienta_por_ruta(ruta: str) -> Herramienta | None:
    """Busca y devuelve la herramienta activa asociada a la ruta dada."""
    ruta_limpia = _normalizar_ruta(ruta)
    for herramienta in HERRAMIENTAS:
        if herramienta.ruta.rstrip("/") == ruta_limpia:
            return herramienta
    return None


def pilar_de(identificador_herramienta: str) -> Pilar:
    """Devuelve el pilar al que pertenece la herramienta."""
    herramienta = herramienta_por_identificador(identificador_herramienta)
    return _PILARES_POR_IDENTIFICADOR[herramienta.identificador_pilar]


def herramientas_visibles(identificador_pilar: str | None = None) -> tuple[Herramienta, ...]:
    """Devuelve las herramientas habilitadas en orden de catálogo."""
    if identificador_pilar is None:
        return tuple(herramienta for herramienta in HERRAMIENTAS if herramienta.habilitada)
    return tuple(herramienta for herramienta in HERRAMIENTAS if herramienta.habilitada and herramienta.identificador_pilar == identificador_pilar)


def grupos_navegacion() -> tuple[tuple[Pilar, tuple[Herramienta, ...]], ...]:
    """Devuelve los pilares con al menos una herramienta habilitada."""
    grupos = []
    for pilar in PILARES:
        herramientas = herramientas_visibles(pilar.identificador)
        if herramientas:
            grupos.append((pilar, herramientas))
    return tuple(grupos)


def pilar_por_ruta(ruta: str) -> Pilar | None:
    """Determina el pilar al que pertenece una ruta base."""
    ruta_limpia = _normalizar_ruta(ruta)
    for pilar in PILARES:
        if ruta_limpia == pilar.prefijo or ruta_limpia.startswith(pilar.prefijo + "/"):
            return pilar
    return None


def _normalizar_ruta(ruta: str) -> str:
    """Elimina la consulta y la barra final, preservando la raíz como una barra."""
    return ruta.split("?")[0].rstrip("/") or "/"


def ruta_navegacion(ruta: str) -> tuple[tuple[str, str | None], ...]:
    """Genera la estructura de migas de pan para una ruta canónica."""
    herramienta = herramienta_por_ruta(ruta)
    if herramienta is None:
        return ()
    pilar = _PILARES_POR_IDENTIFICADOR[herramienta.identificador_pilar]
    return ((pilar.nombre, None), (herramienta.nombre, herramienta.ruta))


def _crear_elementos_herramientas(identificadores: tuple[str, ...]) -> tuple[ElementoNavegacion, ...]:
    """Construye los enlaces de las herramientas en el orden de sus identificadores."""
    elementos = []
    for identificador in identificadores:
        herramienta = herramienta_por_identificador(identificador)
        elementos.append(
            ElementoNavegacion(
                clave=herramienta.identificador,
                etiqueta=herramienta.nombre,
                etiqueta_corta=_ETIQUETAS_CORTAS[herramienta.identificador],
                descriptor=herramienta.descriptor,
                icono=herramienta.icono,
                ruta=herramienta.ruta,
                consulta=(),
                identificador_herramienta=herramienta.identificador,
            )
        )
    return tuple(elementos)


def _crear_elementos_visualizador() -> tuple[ElementoNavegacion, ...]:
    """Construye los elementos de navegación contextual para el visualizador."""
    elementos = []
    for escena, etiqueta, etiqueta_corta, descriptor, icono in ESCENAS_VISUALIZADOR:
        elementos.append(
            ElementoNavegacion(
                clave=f"vis:{escena}",
                etiqueta=etiqueta,
                etiqueta_corta=etiqueta_corta,
                descriptor=descriptor,
                icono=icono,
                ruta="/visualizador",
                consulta=(("escena", escena),),
                identificador_herramienta="visualizador",
            )
        )
    return tuple(elementos)


def elementos_navegacion(identificador_pilar: str) -> tuple[ElementoNavegacion, ...]:
    """Devuelve los elementos de navegación contextual asociados a un pilar."""
    if identificador_pilar == "algebra":
        return _crear_elementos_herramientas(("sistemas", "vectores", "matrices", "inversa"))
    if identificador_pilar == "visualizador":
        return _crear_elementos_visualizador()
    if identificador_pilar == "utilidades":
        return _crear_elementos_herramientas(("bases", "romanos"))
    return ()


def enlace_elemento_navegacion(elemento: ElementoNavegacion) -> str:
    """Devuelve la URL del elemento con sus parámetros de consulta codificados."""
    if elemento.consulta:
        return f"{elemento.ruta}?{urllib.parse.urlencode(elemento.consulta)}"
    return elemento.ruta


def predeterminado_elemento_clave(ruta: str) -> str | None:
    """Obtiene la clave del elemento de navegación predeterminado para una ruta."""
    herramienta = herramienta_por_ruta(ruta)
    if herramienta is None:
        return None
    if herramienta.identificador == "visualizador":
        return "vis:rectas-planos"
    return herramienta.identificador
