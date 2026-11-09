"""Conversión léxica de la captura y consulta de condiciones al dominio."""
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion, validar_entrada, validar_precision
from src.backend.resolutores.raices.criterios_biseccion import validar_criterio
from src.backend.resolutores.raices.estimacion_biseccion import estimar_iteraciones
from src.frontend.controladores.captura_real import entero_capturado, real_capturado
from .catalogo_criterios import CRITERIOS, DECIMALES_PRESENTACION_DEFECTO, condicion_criterio


def preparar_entrada(captura: dict) -> EntradaBiseccion:
    """Convierte los campos activos y delega su validez matemática; propaga ValueError orientativo."""
    return validar_entrada({
        "expresion": captura.get("expresion", ""),
        "extremo_izquierdo": real_capturado(captura.get("extremo_izquierdo"), "El extremo inferior a"),
        "extremo_derecho": real_capturado(captura.get("extremo_derecho"), "El extremo superior b"),
        "decimales": entero_capturado(captura.get("decimales"), "La precisión"),
        "limite_iteraciones": entero_capturado(captura.get("limite_iteraciones"), "El límite"),
        "criterio": _criterio_capturado(captura.get("criterio")),
        "unidad_angular": captura.get("unidad_angular", "radianes"),
    })


def precision_presentacion(valor) -> int:
    """Valida una preferencia visual sin cambiar la configuración matemática; lanza ValueError."""
    return validar_precision(entero_capturado(valor, "Los decimales de presentación"))


def texto_condicion(captura: dict, *, mostrar_error: bool = True) -> str:
    """Describe el criterio activo aun sin intervalo; devuelve orientación si su parámetro es inválido."""
    try:
        precision = captura.get("decimales", DECIMALES_PRESENTACION_DEFECTO)
        limite = entero_capturado(captura.get("limite_iteraciones"), "El límite")
        criterio = validar_criterio(_criterio_capturado(captura.get("criterio")), precision, limite)
        return condicion_criterio(criterio.tipo, criterio.parametro)
    except ValueError as error:
        return str(error) if mostrar_error else ""


def texto_estimacion(captura: dict, *, mostrar_error: bool = True) -> str:
    """Consulta la estimación acotada del dominio y devuelve sus hipótesis o una guía de entrada."""
    try:
        estimacion = estimar_iteraciones(preparar_entrada(captura))
    except ValueError as error:
        return f"Para estimar las filas: {error}" if mostrar_error else ""
    filas = estimacion.filas_previstas
    descripcion = "Sin estimación general." if filas is None else f"Filas previstas: {filas}."
    return descripcion + " " + " ".join(estimacion.advertencias)


def _criterio_capturado(valor):
    if not isinstance(valor, dict) or set(valor) != {"tipo", "parametro"}:
        return valor
    tipo, parametro = valor["tipo"], valor["parametro"]
    if tipo in ("decimales", "iteraciones"):
        parametro = entero_capturado(parametro, CRITERIOS[tipo][1])
    elif tipo in ("relativo", "ancho", "residuo"):
        parametro = real_capturado(parametro, CRITERIOS[tipo][1])
    return {"tipo": tipo, "parametro": parametro}
