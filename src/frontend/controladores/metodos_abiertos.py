"""Adaptador de captura para métodos abiertos."""
from dataclasses import asdict

from src.backend.resolutores.raices.metodos_abiertos import newton_raphson, secante
from src.frontend.controladores.captura_real import entero_capturado, real_capturado


def calcular(captura: dict) -> dict:
    """Convierte texto y devuelve un contrato serializable."""
    try:
        metodo = captura.get("metodo", "newton")
        expresion = captura.get("expresion", "")
        tolerancia = real_capturado(captura.get("tolerancia"), "La tolerancia")
        limite = entero_capturado(captura.get("limite_iteraciones"), "El límite")
        unidad = captura.get("unidad_angular", "radianes")
        x0 = real_capturado(captura.get("x0"), "x0")

        if metodo == "secante":
            x1 = real_capturado(captura.get("x1"), "x1")
            resultado = secante(expresion, x0, x1, tolerancia=tolerancia,
                                limite_iteraciones=limite, unidad_angular=unidad)
        else:
            resultado = newton_raphson(expresion, x0, tolerancia=tolerancia,
                                       limite_iteraciones=limite, unidad_angular=unidad)

        return {
            "estado": resultado.estado,
            "metodo": resultado.metodo,
            "mensaje": resultado.mensaje,
            "raiz": resultado.raiz,
            "motivo": resultado.motivo,
            "iteraciones": [asdict(fila) for fila in resultado.iteraciones],
        }
    except ValueError as error:
        return {"estado": "ERROR", "mensaje": str(error), "iteraciones": []}