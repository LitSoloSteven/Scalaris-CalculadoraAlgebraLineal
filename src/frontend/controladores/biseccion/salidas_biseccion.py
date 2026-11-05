"""Formato compartido para el signo y la acción registrados en el modo examen."""
from src.backend.resolutores.raices.contrato_biseccion import ESTADO_DISCONTINUIDAD
from .presentacion import MOTIVOS

COLUMNAS_EXAMEN = (("signo_examen", "Signo de f(a)·f(c)"), ("accion_examen", "Acción ejecutada"))
_SIGNOS = {-1: "Negativo (−)", 0: "Cero (0)", 1: "Positivo (+)"}
_REEMPLAZOS = {"reemplazar_a": "a = c", "reemplazar_b": "b = c"}
_SIN_DATO = "No disponible"


def datos_examen(fila: dict, estado: str) -> dict[str, str]:
    """Presenta el signo y la acción del motor, incluso si faltan en una fila anterior."""
    signo = _SIGNOS.get(fila.get("signo_producto"), _SIN_DATO)
    accion = fila.get("accion")
    if accion == "detener":
        motivo = MOTIVOS.get(fila.get("motivo_parada"), fila.get("explicacion") or _SIN_DATO)
        texto = f"Detener. {motivo.rstrip('.')}."
        if estado == ESTADO_DISCONTINUIDAD:
            texto += " Punto medio provisional."
    else:
        texto = _REEMPLAZOS.get(accion, _SIN_DATO)
    return {"signo_examen": signo, "accion_examen": texto}


def texto_traza_examen(respuesta: dict) -> str:
    """Devuelve el detalle copiable de las filas válidas en orden de ejecución."""
    encabezado = "\t".join(("Iteración", *(etiqueta for _, etiqueta in COLUMNAS_EXAMEN)))
    lineas = ["Modo examen", encabezado]
    for fila in respuesta["iteraciones"]:
        detalle = datos_examen(fila, respuesta["estado"])
        lineas.append("\t".join((str(fila["i"]), *(detalle[clave] for clave, _ in COLUMNAS_EXAMEN))))
    return "\n".join(lineas)
