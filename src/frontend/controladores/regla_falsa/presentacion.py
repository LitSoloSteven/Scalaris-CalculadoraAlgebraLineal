"""Textos y métricas publicados por el motor de regla falsa."""
from src.frontend.controladores.biseccion.captura_criterio import precision_presentacion
from src.frontend.controladores.biseccion.presentacion import numero
from src.frontend.controladores.biseccion.presentacion_diagnostico import texto_intervalo

_TITULOS = {
    "SIN_CAMBIO_DE_SIGNO": "Sin cambio de signo",
    "ESTANCAMIENTO": "Estancamiento numérico; tolerancia no alcanzada",
    "LIMITE_ITERACIONES": "Límite de iteraciones; tolerancia no alcanzada",
    "ERROR": "Error de entrada o evaluación",
}
_CIERRES_EXITO = {
    "raiz_en_extremo": "Cero evaluado en un extremo, sin iteraciones",
    "raiz_en_aproximacion": "Cero evaluado en la aproximación de la secante",
    "tolerancia_residuo": "Convergió por tolerancia de residuo",
}


def titulo_estado(respuesta: dict) -> str:
    """Describe el estado efectivo del sobre sin deducir convergencia de sus métricas."""
    estado = respuesta["estado"]
    if estado == "EXITO":
        return _CIERRES_EXITO.get(respuesta.get("motivo_parada"), "Cálculo completado")
    return _TITULOS.get(estado, _TITULOS["ERROR"])


def etiqueta_aproximacion(respuesta: dict) -> str:
    """Rotula el valor del motor como raíz, provisional o no disponible según su estado."""
    if respuesta.get("aproximacion") is None:
        return "Aproximación no disponible"
    return "Aproximación de la raíz" if respuesta["estado"] == "EXITO" else "Aproximación provisional"


def aproximacion_presentada(respuesta: dict, decimales: int) -> str:
    """Formatea el valor sin modificarlo; lanza ValueError si la precisión visual es inválida."""
    precision = precision_presentacion(decimales)
    valor = respuesta.get("aproximacion")
    return "No disponible" if valor is None else f"x ≈ {valor:.{precision}f}"


def metricas_principales(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Devuelve iteraciones, intervalo y residuo con las cifras internas del resultado."""
    intervalo = respuesta.get("intervalo_final")
    return (
        ("Iteraciones", str(respuesta["iteraciones_totales"])),
        ("Intervalo final [a, b]", texto_intervalo(intervalo) if intervalo is not None else "No disponible"),
        ("Residuo |f(c)|", numero(respuesta.get("residuo"), True)),
    )


def metricas_resumen(respuesta: dict) -> tuple[tuple[str, str], ...]:
    """Añade configuración y continuidad disponibles sin estimar cotas de error en x."""
    entrada = respuesta.get("entrada")
    datos = ()
    if entrada is not None:
        datos = (
            ("Unidad trigonométrica", entrada["unidad_angular"]),
            ("Tolerancia de residuo", numero(entrada["tolerancia"], True)),
            ("Límite de iteraciones", str(entrada["limite_iteraciones"])),
        )
    informe = respuesta.get("informe_continuidad")
    if informe is not None:
        datos += (("Continuidad", informe["estado"]),)
    return datos + metricas_principales(respuesta)


def avisos_resumen(respuesta: dict) -> tuple[str, ...]:
    """Conserva advertencias y continuidad no confirmada sin repetir mensajes iguales."""
    avisos = tuple(respuesta.get("advertencias", ()))
    informe = respuesta.get("informe_continuidad")
    if informe is not None and informe["estado"] != "CONFIRMADA":
        avisos += (informe["mensaje"],)
    return tuple(dict.fromkeys(avisos))
