"""Adaptación del lote de falsa posición con metadatos independientes por identificador."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_lote_regla_falsa import EntradaLoteReglaFalsa
from src.backend.resolutores.raices.limites_resolucion_multiple import MAXIMO_CANDIDATOS_MULTIPLE, MAXIMO_EVALUACIONES_MULTIPLE
from src.backend.resolutores.raices.resolucion_multiple_regla_falsa import resolver_candidatos_regla_falsa
from src.frontend.controladores.candidatos_lote_raices import convertir_candidato
from src.frontend.controladores.captura_real import entero_capturado
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO
from .configuracion_ampliada import preparar_configuracion
from .presentacion_grafica import agregar_grafica

_ERROR_CAPTURA = "Revisa la configuración, el presupuesto y la selección de candidatos; vuelve a explorar si es necesario."
_ERROR_EJECUCION = "No se pudo completar el lote de regla falsa. Revisa los datos y vuelve a resolver."


def resolver_lote(captura: dict) -> dict:
    """Delega una sola solicitud al servicio de regla falsa y devuelve errores públicos controlados."""
    try:
        entrada = _preparar_lote(captura)
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return _error(_ERROR_CAPTURA)
    try:
        lote = resolver_candidatos_regla_falsa(entrada)
        resultados = tuple(_serializar_registro(registro, entrada) for registro in lote.resultados)
        salida = {"estado": "LOTE_PARCIAL" if lote.presupuesto_agotado else "LOTE_COMPLETADO",
                  "mensaje": "Lote parcial: hay candidatos sin ejecutar por presupuesto." if lote.presupuesto_agotado else
                  "Lote completado. Revisa el estado independiente de cada candidato.",
                  "resultados": resultados, "evaluaciones_reservadas": lote.evaluaciones_reservadas,
                  "filas_generadas": lote.filas_generadas, "presupuesto_agotado": lote.presupuesto_agotado,
                  "presupuesto_evaluaciones": entrada.presupuesto_evaluaciones, "advertencias": lote.advertencias}
        json.dumps(salida, allow_nan=False)
        return salida
    except Exception:
        return _error(_ERROR_EJECUCION)


def _preparar_lote(captura: dict) -> EntradaLoteReglaFalsa:
    if not isinstance(captura, dict) or not isinstance(captura.get("configuracion"), dict):
        raise ValueError(_ERROR_CAPTURA)
    registros = captura.get("candidatos")
    if not isinstance(registros, (tuple, list)) or not 1 <= len(registros) <= MAXIMO_CANDIDATOS_MULTIPLE:
        raise ValueError(_ERROR_CAPTURA)
    candidatos = tuple(convertir_candidato(registro) for registro in registros)
    inferior, superior = RANGO_GRAFICA_DEFECTO
    # El servicio sustituye este intervalo de configuración por el propio de cada candidato.
    configuracion = preparar_configuracion({**captura["configuracion"], "extremo_izquierdo": inferior,
                                            "extremo_derecho": superior, "cero_preferido": None})
    presupuesto = entero_capturado(captura.get("presupuesto_evaluaciones", MAXIMO_EVALUACIONES_MULTIPLE), "El presupuesto")
    return EntradaLoteReglaFalsa(configuracion, candidatos, presupuesto)


def _serializar_registro(registro, entrada: EntradaLoteReglaFalsa) -> dict:
    datos = None
    if registro.respuesta is not None:
        ampliado = asdict(registro.respuesta)
        respuesta = ampliado.pop("resultado")
        candidato = next(actual.candidato for actual in entrada.candidatos if actual.identificador == registro.identificador)
        ampliado["configuracion"] = {"entrada": respuesta["entrada"], "criterio": ampliado["criterio"],
                                     "cero_preferido": candidato.abscisa if candidato.tipo == "cero_evaluado" else None}
        datos = agregar_grafica({"resultado": respuesta, "ampliado": ampliado, "sugerencias": ()})
    return {"identificador": registro.identificador, "estado": registro.estado, "mensaje": registro.mensaje,
            "datos": datos, "evaluaciones_reservadas": registro.evaluaciones_reservadas,
            "informe_continuidad": registro.informe_continuidad}


def _error(mensaje: str) -> dict:
    return {"estado": "ERROR", "mensaje": mensaje, "resultados": ()}
