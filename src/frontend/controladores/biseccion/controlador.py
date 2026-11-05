"""Captura numérica y delegación acotada al contrato de raíces."""
import math
from dataclasses import asdict

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion, ResultadoBiseccion, derivar_E, LIMITE_ITERACIONES_MAXIMO
from src.backend.resolutores.raices.parada_biseccion import comprobar_cierre_criterio
from .captura_criterio import entero_capturado, preparar_entrada
from .muestreo import muestrear_funcion

LIMITE_ITERACIONES_INTERFAZ = LIMITE_ITERACIONES_MAXIMO


def calcular_presentacion(captura: dict) -> dict:
    """Resuelve y prepara un muestreo orientativo sin bloquear el hilo de interfaz."""
    respuesta = resolver_captura(captura)
    if respuesta["estado"] != "ERROR":
        respuesta["muestra"] = muestrear_funcion(respuesta["entrada"])
        if respuesta["muestra"]["huecos"]:
            respuesta["aviso_grafica"] = "La gráfica contiene huecos por evaluaciones inválidas o saltos pronunciados. El muestreo es orientativo; revisa la continuidad."
    return respuesta


def texto_tolerancia(valor) -> str:
    """Devuelve E en notación decimal a partir del contrato o una guía de validación."""
    try:
        decimales = entero_capturado(valor, "La precisión")
        derivar_E(decimales)
        tolerancia = "1" if decimales == 0 else "0." + "0" * (decimales - 1) + "1"
        return f"E = 10^(-{decimales}) = {tolerancia} · Parada: b − a < E"
    except (ValueError, TypeError, OverflowError):
        return "Introduce un entero de precisión dentro del rango permitido."


def resolver_captura(captura: dict) -> dict:
    """Devuelve una respuesta serializable; convierte fallos del evaluador en errores visibles."""
    try:
        entrada = preparar_entrada(captura)
        resultado = biseccion(entrada)
        return serializar_resultado(entrada, resultado)
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error)}
    except (TypeError, OverflowError, ZeroDivisionError, RecursionError):
        return {"estado": "ERROR", "mensaje": "No se pudo evaluar f(x). Revisa la sintaxis, el dominio y la magnitud de los valores."}


def serializar_resultado(entrada: EntradaBiseccion, resultado: ResultadoBiseccion) -> dict:
    """Adapta un resultado del motor a datos finitos compartidos; lanza ValueError ante incoherencia."""
    respuesta = asdict(resultado)
    respuesta["error_absoluto"] = str(resultado.error_absoluto)
    respuesta["entrada"] = asdict(entrada)
    respuesta["tolerancia"] = float(entrada.error_absoluto)
    _comprobar_salida(respuesta, resultado)
    return respuesta


def _comprobar_salida(respuesta: dict, resultado: ResultadoBiseccion) -> None:
    comprobar_cierre_criterio(resultado)
    if respuesta["aproximacion"] is None:
        return
    valores = [respuesta["aproximacion"], respuesta["cota"], *respuesta["intervalo_final"]]
    valores.append(respuesta["metricas"].get("residuo_final", math.nan))
    if not all(math.isfinite(valor) for valor in valores):
        raise ValueError("El cálculo excede la capacidad numérica. Reduce el intervalo o la magnitud de f(x).")
    if respuesta["motivo_parada"] == "raiz_exacta":
        respuesta["aviso"] = respuesta["mensaje"]
