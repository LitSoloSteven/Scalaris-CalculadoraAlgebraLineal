"""Configuración de bisección para la solicitud individual compartida."""
from src.frontend.controladores.calculo_raices import ConfiguracionCalculoRaices, resolver_calculo_raices

_CONFIGURACION = ConfiguracionCalculoRaices(
    mensaje_carga="Calculando la raíz en el intervalo…",
    mensaje_error="No se pudo completar el cálculo. Revisa la función y vuelve a intentarlo.",
    mensaje_registro="No se pudo presentar el cálculo de bisección",
)


async def resolver_calculo(vista, calcular, *, puntero: bool = False) -> None:
    """Admite un trabajador por vista y publica únicamente la captura vigente."""
    await resolver_calculo_raices(vista, calcular, _CONFIGURACION, puntero=puntero)
