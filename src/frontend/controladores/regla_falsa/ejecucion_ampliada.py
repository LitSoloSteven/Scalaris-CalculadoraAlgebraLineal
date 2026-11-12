"""Adaptación serializable de ejecuciones ampliadas separada del sobre clásico."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_regla_falsa import ResultadoReglaFalsa
from src.backend.resolutores.raices.regla_falsa_ampliada import resolver_regla_falsa_configurada
from src.backend.resolutores.raices.sugerencias_regla_falsa import sugerir_acciones_regla_falsa
from .configuracion_ampliada import preparar_configuracion
from .controlador import resolver_captura_tipado
from .serializacion import serializar_resultado


def resolver_presentacion(captura: dict) -> dict:
    """Entrega resultado, criterio y sugerencias independientes; controla errores de adaptación."""
    if not isinstance(captura, dict):
        return _error_publico("Introduce la función y su configuración.")
    if "criterio" not in captura and captura.get("cero_preferido") is None:
        return _resolver_clasica(captura)
    try:
        configuracion = preparar_configuracion(captura)
    except ValueError as error:
        return _error_publico(str(error))
    except (TypeError, OverflowError, RecursionError):
        return _error_publico(_MENSAJE_ADAPTACION)
    try:
        return _ejecutar_configurada(configuracion)
    except (ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError):
        return _error_publico(_MENSAJE_ADAPTACION, "ERROR_ADAPTACION")


_MENSAJE_ADAPTACION = "No se pudo completar el cálculo. Revisa la configuración, el cero elegido y la magnitud de los valores."


def _error_publico(mensaje: str, codigo: str = "ENTRADA_INVALIDA") -> dict:
    respuesta = serializar_resultado(ResultadoReglaFalsa(
        mensaje=mensaje, codigo_diagnostico=codigo, motivo_parada=codigo.lower()))
    return {"resultado": respuesta, "ampliado": None, "sugerencias": ()}


def _ejecutar_configurada(configuracion) -> dict:
    ampliado = resolver_regla_falsa_configurada(configuracion)
    datos = asdict(ampliado)
    datos["configuracion"] = asdict(configuracion)
    respuesta = datos.pop("resultado")
    salida = {"resultado": respuesta, "ampliado": datos,
              "sugerencias": sugerir_acciones_regla_falsa(configuracion.entrada, ampliado.resultado)
              if ampliado.resultado.entrada is not None else ()}
    json.dumps(salida, allow_nan=False)
    return salida


def _resolver_clasica(captura: dict) -> dict:
    try:
        resultado = resolver_captura_tipado(captura)
        sugerencias = sugerir_acciones_regla_falsa(resultado.entrada, resultado) if resultado.entrada else ()
        salida = {"resultado": serializar_resultado(resultado), "ampliado": None, "sugerencias": sugerencias}
        json.dumps(salida, allow_nan=False)
        return salida
    except (ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError):
        return _error_publico(_MENSAJE_ADAPTACION, "ERROR_ADAPTACION")
