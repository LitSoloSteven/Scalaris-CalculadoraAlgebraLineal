"""Adaptación de los motores de métodos abiertos a la interfaz."""
from dataclasses import asdict
import json
from collections.abc import Mapping

from src.backend.resolutores.raices.metodos_abiertos import (
    EntradaMetodoAbierto, newton, secante, validar_entrada_abierta,
)
from src.frontend.controladores.captura_real import entero_capturado, real_capturado

LONGITUD_MAXIMA_NUMERICA = 64
_ETIQUETAS_NUMERICAS = {
    "x0": "x0", "x1": "x1", "tolerancia": "La tolerancia",
    "limite_iteraciones": "El máximo de iteraciones",
}


def preparar_entrada(captura: Mapping[str, object]) -> EntradaMetodoAbierto:
    """Convierte los valores de los controles y delega las reglas al dominio."""
    metodo = str(captura.get("metodo", ""))
    _validar_longitud_numerica(captura, metodo)
    datos = dict(captura)
    datos["x0"] = real_capturado(captura.get("x0"), "x0")
    if metodo == "secante":
        datos["x1"] = real_capturado(captura.get("x1"), "x1")
    datos["tolerancia"] = real_capturado(captura.get("tolerancia", 1e-6), "La tolerancia")
    datos["limite_iteraciones"] = entero_capturado(captura.get("limite_iteraciones", 100), "El máximo de iteraciones")
    return validar_entrada_abierta(datos)


def _validar_longitud_numerica(captura: Mapping[str, object], metodo: str) -> None:
    campos = ["x0", "tolerancia", "limite_iteraciones"]
    if metodo == "secante":
        campos.append("x1")
    for campo in campos:
        valor = captura.get(campo)
        if isinstance(valor, str) and len(valor) > LONGITUD_MAXIMA_NUMERICA:
            etiqueta = _ETIQUETAS_NUMERICAS[campo]
            raise ValueError(f"{etiqueta} no puede superar {LONGITUD_MAXIMA_NUMERICA} caracteres.")


def resolver_captura(captura: Mapping[str, object]) -> dict:
    """Valida y resuelve una captura devolviendo únicamente datos serializables."""
    metodo = str(captura.get("metodo", "newton"))
    try:
        entrada = preparar_entrada(captura)
        resultado = newton(entrada) if metodo == "newton" else secante(entrada)
        datos = asdict(resultado)
        json.dumps(datos, allow_nan=False)
        return datos
    except (ValueError, TypeError, OverflowError) as error:
        return {"metodo": metodo, "estado": "ERROR", "mensaje": str(error),
                "codigo_diagnostico": "ENTRADA_INVALIDA", "raiz": None,
                "residuo": None, "iteraciones": [], "iteraciones_totales": 0,
                "derivada_expresion": None, "advertencias": [], "contexto_fallo": None,
                "entrada": None}
