"""Adaptación serializable de ejecuciones ampliadas separada del sobre clásico."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_regla_falsa import ResultadoReglaFalsa
from src.backend.resolutores.raices.regla_falsa_ampliada import resolver_regla_falsa_configurada
from src.backend.resolutores.raices.sugerencias_regla_falsa import sugerir_acciones_regla_falsa
from .configuracion_ampliada import preparar_configuracion
from .controlador import resolver_captura
from .serializacion import serializar_resultado
from .captura import preparar_entrada


def resolver_presentacion(captura: dict) -> dict:
    """Entrega resultado, criterio y sugerencias independientes; controla errores de adaptación."""
    try:
        if "criterio" not in captura and captura.get("cero_preferido") is None:
            respuesta = resolver_captura(captura)
            sugerencias = _sugerencias_clasicas(captura, respuesta)
            return {"resultado": respuesta, "ampliado": None, "sugerencias": sugerencias}
        configuracion = preparar_configuracion(captura)
        ampliado = resolver_regla_falsa_configurada(configuracion)
        datos = asdict(ampliado)
        datos["configuracion"] = asdict(configuracion)
        respuesta = datos.pop("resultado")
        salida = {"resultado": respuesta, "ampliado": datos,
                  "sugerencias": sugerir_acciones_regla_falsa(configuracion.entrada, ampliado.resultado)
                  if ampliado.resultado.entrada is not None else ()}
        json.dumps(salida, allow_nan=False)
        return salida
    except ValueError as error:
        mensaje = str(error)
    except (TypeError, OverflowError, RecursionError):
        mensaje = "No se pudo adaptar la configuración. Revisa los campos y su magnitud."
    respuesta = serializar_resultado(ResultadoReglaFalsa(
        mensaje=mensaje, codigo_diagnostico="ENTRADA_INVALIDA", motivo_parada="entrada_invalida"))
    return {"resultado": respuesta, "ampliado": None, "sugerencias": ()}


def _sugerencias_clasicas(captura: dict, respuesta: dict) -> tuple:
    if respuesta["codigo_diagnostico"] != "DOMINIO_INVALIDO":
        return ()
    entrada = preparar_entrada(captura)
    # El servicio requiere un resultado tipado; el sobre conserva sus estructuras anidadas.
    resultado = ResultadoReglaFalsa(**{clave: valor for clave, valor in respuesta.items() if clave != "metodo"})
    return sugerir_acciones_regla_falsa(entrada, resultado)
