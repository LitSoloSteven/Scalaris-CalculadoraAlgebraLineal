"""Seleccion de herramientas recientes para la pagina de inicio."""
from src.frontend.navegacion import Herramienta, herramienta_por_identificador, herramientas_visibles

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
        try:
            herramienta = herramienta_por_identificador(elemento)
        except KeyError:
            continue
        if not herramienta.habilitada or elemento in vistos:
            continue
        herramientas.append(herramienta)
        vistos.add(elemento)
        if len(herramientas) >= MAXIMO_RECIENTES:
            break

    return tuple(herramientas)


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
