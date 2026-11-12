"""Guardas numéricas y evaluación segura compartidas por los métodos abiertos."""
import math
from collections.abc import Callable

from src.backend.excepciones import ErrorDominio, ErrorNoFinito

from ..evaluador_funcion import evaluar
from .contrato_abiertos import AVISO_CAMBIO_SIN_RESIDUO, CriterioParada

UMBRAL_DERIVADA = 1e-12
UMBRAL_DENOMINADOR_RELATIVO = 1e-14
LIMITE_MAGNITUD = 1e12


def derivada_utilizable(derivada: float, abscisa: float) -> bool:
    """Comprueba que la derivada no sea despreciable frente a la escala de la abscisa."""
    return abs(derivada) > UMBRAL_DERIVADA * max(1.0, abs(abscisa))


def denominador_utilizable(f_actual: float, f_anterior: float) -> bool:
    """Comprueba que la diferencia de residuos no sea despreciable en su escala."""
    escala = max(1.0, abs(f_actual), abs(f_anterior))
    return abs(f_actual - f_anterior) > UMBRAL_DENOMINADOR_RELATIVO * escala


def paso_representable(abscisa: float) -> bool:
    """Indica si la aproximación es finita y no excede el límite de magnitud."""
    return math.isfinite(abscisa) and abs(abscisa) <= LIMITE_MAGNITUD


def error_relativo_porcentual(x_nuevo: float, x_actual: float) -> float | None:
    """Devuelve el error relativo porcentual o None cuando la referencia es cero."""
    if x_nuevo == 0:
        return None
    return abs((x_nuevo - x_actual) / x_nuevo) * 100.0


def criterio_parada(residuo: float, error: float, tolerancia: float) -> CriterioParada:
    """Devuelve el criterio cumplido, priorizando el residuo sobre el cambio."""
    if abs(residuo) < tolerancia:
        return "residuo"
    if error < tolerancia:
        return "cambio"
    return ""


def advertencias_por_cambio(
    f_siguiente: float, tolerancia: float, criterio: CriterioParada
) -> tuple[str, ...]:
    """Avisa cuando el cambio cumple tolerancia pero el residuo todavía no."""
    if criterio == "cambio" and abs(f_siguiente) >= tolerancia:
        return (AVISO_CAMBIO_SIN_RESIDUO,)
    return ()


def evaluar_con_guarda(
    funcion: Callable[[float], float], abscisa: float
) -> tuple[float | None, str | None]:
    """Devuelve (f(x), None) o (None, detalle) sin propagar errores de evaluación."""
    try:
        return evaluar(funcion, abscisa), None
    except (ErrorDominio, ErrorNoFinito, ValueError, ZeroDivisionError, OverflowError) as error:
        return None, str(error) or type(error).__name__
