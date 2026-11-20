"""Selección de herramientas y escenas recientes para la portada."""
from src.frontend.navegacion import (
    ESCENAS_VISUALIZADOR,
    ElementoNavegacion,
    Herramienta,
    herramienta_por_identificador,
    herramienta_por_ruta,
    herramientas_visibles,
)
from src.frontend.navegacion.secciones_inicio import secciones_inicio

MAXIMO_RECIENTES = 4
IDENTIFICADOR_DESTACADA_PREDETERMINADA = "sistemas"
_CLAVES_ESCENAS = frozenset(f"vis:{escena}" for escena, *_ in ESCENAS_VISUALIZADOR)


def normalizar_recientes(datos_crudos) -> tuple[Herramienta, ...]:
    """Normaliza la lista de ejercicios recientes conservando los registros válidos."""
    if not isinstance(datos_crudos, list):
        return ()

    herramientas = []
    vistos = set()
    for elemento in datos_crudos:
        if not isinstance(elemento, str):
            continue
        herramienta = _herramienta_reciente(elemento)
        if herramienta is None or herramienta.identificador in vistos:
            continue
        herramientas.append(herramienta)
        vistos.add(herramienta.identificador)
        if len(herramientas) >= MAXIMO_RECIENTES:
            break

    return tuple(herramientas)


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
    if elemento == "visualizador":
        return accesos.get("vis:rectas-planos")
    herramienta = _herramienta_reciente(elemento)
    if herramienta is None:
        return None
    clave = "vis:rectas-planos" if herramienta.identificador == "visualizador" else herramienta.identificador
    return accesos.get(clave)


def normalizar_accesos_recientes(datos_crudos) -> tuple[ElementoNavegacion, ...]:
    """Filtra y deduplica el historial del cliente conservando escenas concretas."""
    if not isinstance(datos_crudos, list):
        return ()

    accesos = _accesos_por_clave()
    recientes = []
    vistos = set()
    for elemento in datos_crudos:
        if not isinstance(elemento, str):
            continue
        acceso = _resolver_acceso_reciente(elemento, accesos)
        if acceso is None or acceso.clave in vistos:
            continue
        recientes.append(acceso)
        vistos.add(acceso.clave)
        if len(recientes) >= MAXIMO_RECIENTES:
            break

    return tuple(recientes)


def elegir_acceso_destacado(datos_crudos) -> tuple[ElementoNavegacion, bool]:
    """Devuelve el último acceso visitado o el respaldo de portada cuando falta historial."""
    recientes = normalizar_accesos_recientes(datos_crudos)
    if recientes:
        return recientes[0], True
    accesos = _accesos_por_clave()
    predeterminado = accesos.get(IDENTIFICADOR_DESTACADA_PREDETERMINADA)
    if predeterminado is not None:
        return predeterminado, False
    return tuple(accesos.values())[0], False
