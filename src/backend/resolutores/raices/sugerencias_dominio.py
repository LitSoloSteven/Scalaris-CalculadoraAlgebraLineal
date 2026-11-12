"""Propuestas conservadoras de dominio y criterio que nunca cambian el cálculo solicitado."""
import ast
import math
from dataclasses import asdict
from fractions import Fraction

from .aritmetica_biseccion import ancho_intervalo, cota_intervalo
from .contrato_biseccion import EntradaBiseccion, ResultadoBiseccion, SugerenciaBiseccion, validar_entrada
from .dominio_intervalo import argumento_afin, comprobar_dominio_intervalo
from .evaluador_funcion import compilar, evaluar
from .gramatica_funcion import analizar_expresion
from .unidades_angulares import opciones_unidad


def sugerir_acciones(entrada: EntradaBiseccion, resultado: ResultadoBiseccion) -> tuple[SugerenciaBiseccion, ...]:
    """Devuelve propuestas verificadas sin modificar entrada, estado, criterio ni traza."""
    if resultado.codigo_diagnostico == "DOMINIO_INVALIDO":
        intervalo = sugerir_intervalo_dominio(entrada)
        if intervalo is not None:
            return ({"tipo": "intervalo_dominio", "intervalo": intervalo,
                     "mensaje": "Puedes cargar un intervalo recortado al dominio de sqrt. Se comprobaron sus extremos y las restricciones reconocidas; no certifica continuidad ni cambio de signo."},)
    if _ofrecer_ancho(entrada, resultado):
        return ({"tipo": "criterio_absoluto",
                 "mensaje": "El intervalo final contiene cero. El error relativo divide por c y puede ser indefinido o poco útil cerca de cero. Puedes elegir ancho absoluto y revisar su tolerancia antes de calcular."},)
    return ()


def sugerir_intervalo_dominio(entrada: EntradaBiseccion) -> tuple[float, float] | None:
    """Recorta restricciones afines sqrt y verifica la propuesta; devuelve None si no es segura."""
    try:
        entrada = validar_entrada(asdict(entrada))
        original = (entrada.extremo_izquierdo, entrada.extremo_derecho)
        intervalo = sugerir_recorte_dominio(entrada.expresion, original, entrada.unidad_angular)
        if intervalo is not None:
            cota_intervalo(*intervalo)
        return intervalo
    except (ValueError, OverflowError):
        return None


def sugerir_recorte_dominio(
    expresion: str, original: tuple[float, float], unidad: str,
) -> tuple[float, float] | None:
    """Recorta sqrt sobre datos canónicos sin aplicar cotas ni criterios de un método."""
    try:
        intervalo = _recortar_raices(expresion, original)
        if intervalo is None or intervalo == original or intervalo[0] >= intervalo[1]:
            return None
        ancho_intervalo(*intervalo)
        funcion = compilar(expresion, **opciones_unidad(unidad))
        evaluar(funcion, intervalo[0])
        evaluar(funcion, intervalo[1])
        comprobar_dominio_intervalo(expresion, intervalo, unidad_angular=unidad)
        return intervalo
    except (ValueError, OverflowError):
        return None


def _recortar_raices(expresion: str, intervalo: tuple[float, float]) -> tuple[float, float] | None:
    limites = Fraction(intervalo[0]), Fraction(intervalo[1])
    arbol = analizar_expresion(expresion)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and nodo.func.id == "sqrt":
            afin = argumento_afin(nodo.args[0])
            if afin is None:
                return None
            limites = _restringir_limites(limites, afin)
            if limites is None:
                return None
    return _redondear_interior(limites[0], True), _redondear_interior(limites[1], False)


def _restringir_limites(limites: tuple[Fraction, Fraction], afin: tuple[Fraction, Fraction]) -> tuple[Fraction, Fraction] | None:
    pendiente, ordenada = afin
    inferior, superior = limites
    if pendiente == 0:
        return limites if ordenada >= 0 else None
    frontera = -ordenada / pendiente
    if pendiente > 0:
        inferior = max(inferior, frontera)
    else:
        superior = min(superior, frontera)
    return (inferior, superior) if inferior < superior else None


def _redondear_interior(limite: Fraction, es_inferior: bool) -> float:
    numero = float(limite)
    fuera = Fraction(numero) < limite if es_inferior else Fraction(numero) > limite
    if fuera:
        numero = math.nextafter(numero, math.inf if es_inferior else -math.inf)
    return numero


def _ofrecer_ancho(entrada: EntradaBiseccion, resultado: ResultadoBiseccion) -> bool:
    if entrada.criterio_activo.tipo != "relativo" or resultado.estado != "PRECISION_NO_ALCANZADA":
        return False
    intervalo = resultado.intervalo_final
    return intervalo is not None and intervalo[0] <= 0 <= intervalo[1]
