"""Detalle textual de los fallos reales de regla falsa sin nuevas evaluaciones."""
from src.frontend.controladores.biseccion.presentacion_diagnostico import (
    detalles_diagnostico as _detalles_compartidos,
)

_ETAPAS = {
    "sintaxis": "Análisis de sintaxis", "extremos": "Evaluación de extremos",
    "estructura": "Análisis estructural", "iteracion": "Evaluación de la secante",
    "capacidad": "Capacidad de representación numérica",
}


def detalles_diagnostico(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Expone etapa, abscisa y filas válidas del sobre, incluso cuando la entrada es nula."""
    contexto = respuesta.get("contexto_fallo")
    if contexto is None:
        return (("Código del diagnóstico", respuesta["codigo_diagnostico"]),)
    etapa = contexto["etapa"]
    adaptada = {
        **respuesta,
        "contexto_fallo": {**contexto, "etapa": _ETAPAS.get(etapa, etapa)},
        "iteraciones": tuple({"c": fila["aproximacion"], "f_c": fila["valor_aproximacion"]}
                             for fila in respuesta["iteraciones"]),
    }
    return _detalles_compartidos(adaptada)
