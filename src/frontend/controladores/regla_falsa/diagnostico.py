"""Detalle textual de los fallos reales de regla falsa sin nuevas evaluaciones."""
from src.frontend.controladores.biseccion.presentacion_diagnostico import (
    detalles_diagnostico as _detalles_compartidos,
)


def detalles_diagnostico(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Expone etapa, abscisa y filas válidas del sobre, incluso cuando la entrada es nula."""
    contexto = respuesta.get("contexto_fallo")
    if contexto is None:
        return (("Código del diagnóstico", respuesta["codigo_diagnostico"]),)
    etapa = contexto["etapa"]
    if etapa == "iteracion":
        etapa = "Evaluación de la secante"
    adaptada = {
        **respuesta,
        "contexto_fallo": {**contexto, "etapa": etapa},
        "iteraciones": tuple({"c": fila["aproximacion"], "f_c": fila["valor_aproximacion"]}
                             for fila in respuesta["iteraciones"]),
    }
    return _detalles_compartidos(adaptada)
