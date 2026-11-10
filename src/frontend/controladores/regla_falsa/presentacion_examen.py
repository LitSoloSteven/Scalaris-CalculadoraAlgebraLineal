"""Razonamiento didáctico obtenido exclusivamente de la fila original de regla falsa."""
from src.frontend.controladores.formato_numerico_raices import texto_intervalo
from .tabla import ACCIONES, valor_columna

_EXTREMOS = {"reemplazar_a": "Se reemplaza a por c.", "reemplazar_b": "Se reemplaza b por c.",
             "raiz": "Ambos extremos pasan a c, un cero evaluado.",
             "sin_cambio": "No se reemplaza ningún extremo."}
_PARADAS = {
    "tolerancia_residuo": "Residuo menor que la tolerancia.",
    "raiz_en_aproximacion": "Cero evaluado en la aproximación de la secante.",
    "limite_iteraciones": "Límite de iteraciones alcanzado.",
    "estancamiento_numerico": "Estancamiento numérico.",
}


def datos_examen(fila: dict) -> tuple[tuple[str, str], ...]:
    """Describe signo, reemplazo, intervalo y parada sin recalcular ni modificar la traza."""
    motivo = fila["motivo_parada"]
    return (
        ("Signo de f(a)·f(c)", valor_columna(fila, "signo_producto")),
        ("Acción del motor", ACCIONES[fila["accion"]]),
        ("Extremo reemplazado", _EXTREMOS[fila["accion"]]),
        ("Intervalo siguiente", texto_intervalo(fila["intervalo_siguiente"])),
        ("Motivo de parada", _PARADAS.get(motivo, motivo) if motivo else "Continúa la siguiente iteración."),
    )


def texto_filas_examen(filas: tuple) -> str:
    """Devuelve las filas originales como texto completo, incluso si la traza está vacía."""
    bloques = ["Modo examen: razonamiento por iteración"]
    for fila in filas:
        bloques.append(f"Iteración {fila['i']}")
        bloques.extend(f"{etiqueta}: {valor}" for etiqueta, valor in datos_examen(fila))
    if not filas:
        bloques.append("No hay iteraciones registradas.")
    return "\n".join(bloques)
