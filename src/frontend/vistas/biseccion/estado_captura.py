"""Restauración agrupada de datos de captura y limpieza de rangos."""
from contextlib import contextmanager

from src.frontend.controladores.biseccion.exploracion import PASO_EXPLORACION_DEFECTO
from src.frontend.controladores.biseccion.vista_previa import RANGO_GRAFICA_DEFECTO
from .selector_unidad import restaurar_unidad

_EXTREMOS = ("extremo_izquierdo", "extremo_derecho")
_CLAVES_CERO = ("expresion", *_EXTREMOS, "unidad_angular", "cero_preferido")


def hay_rangos_editados(vista) -> bool:
    """Indica si limpiar retiraría un rango o un paso distinto de los iniciales."""
    exploracion = vista.exploracion
    previa = vista.vista_previa
    return (bool(exploracion.minimo.value or exploracion.maximo.value)
            or exploracion.paso.value != PASO_EXPLORACION_DEFECTO
            or (previa.minimo.value, previa.maximo.value) != tuple(map(str, RANGO_GRAFICA_DEFECTO)))


@contextmanager
def transaccion(vista):
    """Pospone los efectos de edición hasta completar la escritura de campos."""
    anterior = vista._cargando_captura
    vista._cargando_captura = True
    try:
        yield
    finally:
        vista._cargando_captura = anterior


def restaurar_captura(vista, captura: dict) -> None:
    """Restaura campos presentes y admite recientes de precisión decimal antigua."""
    with transaccion(vista):
        restaurar_unidad(vista, captura)
        campos = {"expresion": vista.expresion, _EXTREMOS[0]: vista.inferior,
                  _EXTREMOS[1]: vista.superior, "limite_iteraciones": vista.limite}
        for clave, campo in campos.items():
            if clave in captura:
                campo.set_value(captura[clave])
        criterio = captura.get("criterio")
        if criterio is not None:
            vista.criterio.set_value(criterio["tipo"])
            vista.parametros_criterio[criterio["tipo"]].set_value(criterio["parametro"])
        elif "decimales" in captura:
            vista.criterio.set_value("decimales")
            vista.decimales.set_value(captura["decimales"])
        if any(clave in captura for clave in _CLAVES_CERO):
            vista._cero_preferido = captura.get("cero_preferido")


def vaciar_captura(vista) -> None:
    """Vacía el ejercicio y reinicia los rangos de esta captura."""
    with transaccion(vista):
        for campo in (vista.expresion, vista.inferior, vista.superior,
                      vista.exploracion.minimo, vista.exploracion.maximo):
            campo.set_value("")
        vista.exploracion.paso.set_value(PASO_EXPLORACION_DEFECTO)
        for campo, valor in zip((vista.vista_previa.minimo, vista.vista_previa.maximo), RANGO_GRAFICA_DEFECTO):
            campo.set_value(str(valor))
        vista._cero_preferido = None
