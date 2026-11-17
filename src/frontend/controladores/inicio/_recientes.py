"""Seleccion de herramientas recientes para la pagina de inicio."""
from src.frontend.navegacion import Herramienta, herramienta_por_identificador, herramienta_por_ruta, herramientas_visibles

MAXIMO_RECIENTES = 4
IDENTIFICADOR_DESTACADA_PREDETERMINADA = "sistemas"


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


def _herramienta_reciente(identificador: str) -> Herramienta | None:
    try:
        herramienta = herramienta_por_identificador(identificador)
    except KeyError:
        return None
    if herramienta.habilitada:
        return herramienta
    canonica = herramienta_por_ruta(herramienta.ruta)
    if canonica is not None and canonica.identificador != identificador and canonica.habilitada:
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
