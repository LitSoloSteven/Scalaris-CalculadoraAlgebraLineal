"""Captura numérica y delegación acotada al contrato de raíces."""
import math
from dataclasses import asdict

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import validar_entrada, derivar_E

LIMITE_ITERACIONES_INTERFAZ = 500


def entero_capturado(valor, etiqueta: str) -> int:
    """Convierte un campo entero sin truncar decimales; lanza ValueError si es inválido."""
    numero = float(valor)
    if isinstance(valor, bool) or not math.isfinite(numero) or not numero.is_integer():
        raise ValueError(f"{etiqueta} debe ser un entero.")
    return int(numero)


def texto_tolerancia(valor) -> str:
    """Devuelve E en notación decimal a partir del contrato o una guía de validación."""
    try:
        decimales = entero_capturado(valor, "La precisión")
        derivar_E(decimales)
        tolerancia = "1" if decimales == 0 else "0." + "0" * (decimales - 1) + "1"
        return f"E = 10^(-{decimales}) = {tolerancia} · Parada: b − a < E"
    except (ValueError, TypeError, OverflowError):
        return "Introduce un entero de precisión dentro del rango permitido."


def preparar_entrada(captura: dict):
    """Adapta campos de texto al contrato; propaga ValueError con orientación de captura."""
    limite = entero_capturado(captura.get("limite_iteraciones"), "El límite")
    if not 1 <= limite <= LIMITE_ITERACIONES_INTERFAZ:
        raise ValueError(f"Usa de 1 a {LIMITE_ITERACIONES_INTERFAZ} iteraciones en esta interfaz.")
    return validar_entrada({
        "expresion": str(captura.get("expresion", "")).replace("^", "**"),
        "extremo_izquierdo": float(captura.get("extremo_izquierdo")),
        "extremo_derecho": float(captura.get("extremo_derecho")),
        "decimales": entero_capturado(captura.get("decimales"), "La precisión"),
        "limite_iteraciones": limite,
    })


def resolver_captura(captura: dict) -> dict:
    """Devuelve una respuesta serializable; convierte fallos del evaluador en errores visibles."""
    try:
        entrada = preparar_entrada(captura)
        resultado = biseccion(entrada)
        respuesta = asdict(resultado)
        respuesta["error_absoluto"] = str(resultado.error_absoluto)
        respuesta["entrada"] = asdict(entrada)
        respuesta["tolerancia"] = float(entrada.error_absoluto)
        _comprobar_salida(respuesta)
        return respuesta
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error)}
    except (TypeError, OverflowError, ZeroDivisionError, RecursionError):
        return {"estado": "ERROR", "mensaje": "No se pudo evaluar f(x). Revisa la sintaxis, el dominio y la magnitud de los valores."}


def _comprobar_salida(respuesta: dict) -> None:
    if respuesta["aproximacion"] is None:
        return
    valores = [respuesta["aproximacion"], respuesta["cota"], *respuesta["intervalo_final"]]
    valores.append(respuesta["metricas"].get("residuo_final", math.nan))
    if not all(math.isfinite(valor) for valor in valores):
        raise ValueError("El cálculo excede la capacidad numérica. Reduce el intervalo o la magnitud de f(x).")
    if respuesta["motivo_parada"] == "raiz_exacta":
        respuesta["aviso"] = "El motor evaluó f(c) como cero en aritmética aproximada; esto no certifica una raíz exacta simbólica."
    elif respuesta["estado"] == "EXITO":
        inferior, superior = respuesta["intervalo_final"]
        if superior - inferior >= respuesta["tolerancia"]:
            raise ValueError("El motor no alcanzó el ancho solicitado. Prueba con menos decimales.")
