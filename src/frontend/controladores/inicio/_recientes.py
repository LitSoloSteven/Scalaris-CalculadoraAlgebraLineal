"""Selección de herramientas y escenas recientes para la portada."""
from src.frontend.navegacion import (
    ElementoNavegacion,
    Herramienta,
    elementos_navegacion,
    herramienta_por_identificador,
    herramienta_por_ruta,
    herramientas_visibles,
    predeterminado_elemento_clave,
)
from src.frontend.navegacion.secciones_inicio import secciones_inicio

MAXIMO_RECIENTES = 4
MAXIMO_ELEMENTOS_CRUDOS = 16
MAXIMO_LONGITUD_CLAVE = 64
IDENTIFICADOR_DESTACADA_PREDETERMINADA = "sistemas"
_CLAVES_ESCENAS = frozenset(elemento.clave for elemento in elementos_navegacion("visualizador"))


def _clave_entrada_valida(elemento) -> bool:
    return (
        isinstance(elemento, str)
        and len(elemento) <= MAXIMO_LONGITUD_CLAVE
        and bool(elemento.strip())
    )


def _recopilar_recientes(datos_crudos, resolver, clave_de) -> tuple:
    if not isinstance(datos_crudos, list):
        return ()

    seleccionados = []
    vistos = set()
    for elemento in datos_crudos[:MAXIMO_ELEMENTOS_CRUDOS]:
        if not _clave_entrada_valida(elemento):
            continue
        resuelto = resolver(elemento)
        clave = None if resuelto is None else clave_de(resuelto)
        if resuelto is None or clave in vistos:
            continue
        seleccionados.append(resuelto)
        vistos.add(clave)
        if len(seleccionados) >= MAXIMO_RECIENTES:
            break

    return tuple(seleccionados)


def normalizar_recientes(datos_crudos) -> tuple[Herramienta, ...]:
    """Normaliza la lista de ejercicios recientes conservando los registros válidos."""
    return _recopilar_recientes(
        datos_crudos,
        _herramienta_reciente,
        lambda herramienta: herramienta.identificador,
    )


def _herramienta_habilitada(identificador: str) -> bool:
    """Comprueba si la herramienta existe y sigue habilitada en el catálogo."""
    try:
        return herramienta_por_identificador(identificador).habilitada
    except KeyError:
        return False


def _herramienta_reciente(identificador: str) -> Herramienta | None:
    """Resuelve identificadores actuales o heredados hacia una herramienta activa."""
    consulta = "visualizador" if identificador in _CLAVES_ESCENAS else identificador
    try:
        herramienta = herramienta_por_identificador(consulta)
    except KeyError:
        return None
    if herramienta.habilitada:
        return herramienta
    canonica = herramienta_por_ruta(herramienta.ruta)
    if (
        canonica is not None
        and canonica.identificador != consulta
        and _herramienta_habilitada(canonica.identificador)
    ):
        return canonica
    return None


def elegir_destacada(datos_crudos) -> tuple[Herramienta, bool]:
    """Devuelve (herramienta, hay_historial) o la primera herramienta habilitada sin historial.
    Prioriza sistemas cuando no hay datos válidos; sin herramientas habilitadas lanza IndexError."""
    herramientas = normalizar_recientes(datos_crudos)
    if herramientas:
        return herramientas[0], True
    try:
        predeterminada = herramienta_por_identificador(IDENTIFICADOR_DESTACADA_PREDETERMINADA)
        if predeterminada.habilitada:
            return predeterminada, False
    except KeyError:
        pass
    return herramientas_visibles()[0], False


def _accesos_por_clave() -> dict[str, ElementoNavegacion]:
    """Reúne los accesos de portada habilitados indexados por su clave pública."""
    return {
        acceso.clave: acceso
        for seccion in secciones_inicio()
        for grupo in seccion.grupos
        for acceso in grupo.accesos
        if _herramienta_habilitada(acceso.identificador_herramienta)
    }


def _resolver_acceso_reciente(
    elemento: str, accesos: dict[str, ElementoNavegacion]
) -> ElementoNavegacion | None:
    """Convierte una clave directa, escena o alias heredado en un acceso habilitado."""
    if elemento in accesos:
        return accesos[elemento]
    herramienta = _herramienta_reciente(elemento)
    if herramienta is None:
        return None
    if herramienta.identificador == "visualizador":
        return accesos.get(predeterminado_elemento_clave(herramienta.ruta) or "")
    return accesos.get(herramienta.identificador)


def normalizar_accesos_recientes(datos_crudos) -> tuple[ElementoNavegacion, ...]:
    """Filtra y deduplica el historial del cliente conservando escenas concretas."""
    accesos = _accesos_por_clave()
    return _recopilar_recientes(
        datos_crudos,
        lambda elemento: _resolver_acceso_reciente(elemento, accesos),
        lambda acceso: acceso.clave,
    )


def elegir_acceso_destacado(datos_crudos) -> tuple[ElementoNavegacion, bool]:
    """Devuelve (acceso, hay_historial) o el respaldo de Sistemas si no hay historial.
    Lanza IndexError si el catálogo no tiene ningún acceso de portada habilitado."""
    recientes = normalizar_accesos_recientes(datos_crudos)
    if recientes:
        return recientes[0], True
    accesos = _accesos_por_clave()
    predeterminado = accesos.get(IDENTIFICADOR_DESTACADA_PREDETERMINADA)
    if predeterminado is not None:
        return predeterminado, False
    return tuple(accesos.values())[0], False
