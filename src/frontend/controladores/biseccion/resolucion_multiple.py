"""Adaptación del lote a capturas de interfaz y resultados serializables independientes."""
from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion, EntradaResolucionMultiple
from src.backend.resolutores.raices.limites_resolucion_multiple import MAXIMO_CANDIDATOS_MULTIPLE
from src.backend.resolutores.raices.resolucion_multiple import resolver_candidatos
from .captura_criterio import preparar_entrada
from .controlador import serializar_resultado


def resolver_lote(captura: dict) -> dict:
    """Devuelve el lote con estados individuales o un error de captura sin lanzar errores numéricos."""
    try:
        entrada = _preparar_lote(captura)
        lote = resolver_candidatos(entrada)
        resultados = tuple(_serializar_registro(registro) for registro in lote.resultados)
        return {"estado": "LOTE_PARCIAL" if lote.presupuesto_agotado else "LOTE_COMPLETADO",
                "mensaje": "Resolución múltiple disponible. Revisa el estado de cada candidato.",
                "resultados": resultados, "evaluaciones_reservadas": lote.evaluaciones_reservadas,
                "filas_generadas": lote.filas_generadas, "presupuesto_agotado": lote.presupuesto_agotado,
                "presupuesto_evaluaciones": entrada.presupuesto_evaluaciones,
                "advertencias": lote.advertencias, "unidad_angular": lote.unidad_angular}
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error), "resultados": ()}
    except (TypeError, KeyError, IndexError, OverflowError):
        return {"estado": "ERROR", "mensaje": "No se pudo preparar el lote. Revisa el criterio y su límite, selecciona candidatos aptos o vuelve a explorar.",
                "resultados": ()}


def _preparar_lote(captura: dict) -> EntradaResolucionMultiple:
    if not isinstance(captura, dict) or not isinstance(captura.get("configuracion"), dict):
        raise ValueError("El lote requiere una captura de configuración.")
    registros = captura.get("candidatos")
    if not isinstance(registros, (tuple, list)) or not 1 <= len(registros) <= MAXIMO_CANDIDATOS_MULTIPLE:
        raise ValueError(f"Selecciona entre 1 y {MAXIMO_CANDIDATOS_MULTIPLE} candidatos; reduce la exploración o resuelve uno.")
    candidatos = tuple(_convertir_candidato(registro) for registro in registros)
    inferior, superior = candidatos[0].candidato.intervalo
    configuracion = preparar_entrada({**captura["configuracion"],
                    "extremo_izquierdo": inferior, "extremo_derecho": superior})
    return EntradaResolucionMultiple(configuracion, candidatos, unidad_angular=captura.get("unidad_angular", "radianes"))


def _convertir_candidato(registro: dict) -> CandidatoResolucion:
    if not isinstance(registro, dict) or not isinstance(registro.get("candidato"), dict):
        raise ValueError("El candidato no tiene la forma esperada.")
    datos = registro["candidato"]
    intervalo = datos.get("intervalo")
    if not isinstance(intervalo, (tuple, list)) or len(intervalo) != 2:
        raise ValueError("El candidato requiere dos extremos.")
    candidato = CandidatoExploracion(datos.get("tipo"), tuple(intervalo), datos.get("abscisa"), datos.get("valor"))
    return CandidatoResolucion(registro.get("identificador"), candidato)


def _serializar_registro(registro) -> dict:
    respuesta = None
    if registro.resultado is not None:
        respuesta = serializar_resultado(registro.entrada, registro.resultado)
    return {"identificador": registro.identificador, "estado": registro.estado, "mensaje": registro.mensaje,
            "respuesta": respuesta, "evaluaciones_reservadas": registro.evaluaciones_reservadas}
