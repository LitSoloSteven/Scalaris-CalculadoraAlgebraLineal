"""Contexto del ejercicio romano y señales para sugerencias de Glosa."""

from typing import Any

from src.ai.contexto import ContextoIA, EstadoContexto, sanear_cadena_usuario
from src.ai.huellas import esta_desactualizado
from src.frontend.controladores.captura_contexto import capturar_romanos

from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    ErrorNumeroRomano, romano_a_entero, ERROR_CERO_NO_REPRESENTABLE,
    ERROR_NEGATIVO_NO_REPRESENTABLE, ERROR_SINTAXIS_INVALIDA,
    ERROR_NO_CANONICO, ERROR_ENTRADA_VACIA,
)


def _leer_operandos(vista: Any) -> tuple[str, str, str]:
    operando_a = vista.entrada_a.value if vista.entrada_a else ""
    operando_b = vista.entrada_b.value if vista.entrada_b else ""
    operacion = getattr(vista.pestanas_operacion, "value", "suma") if vista.pestanas_operacion else "suma"
    return operando_a, operando_b, operacion


def _describir_operandos(operando_a: str, operando_b: str, operacion: str) -> dict:
    return {
        "operando_a": sanear_cadena_usuario(operando_a, 32) if operando_a else "",
        "operando_b": sanear_cadena_usuario(operando_b, 32) if operando_b else "",
        "operacion": operacion,
    }


def _resultado_contexto(vista: Any, desactualizado: bool) -> dict | None:
    if desactualizado:
        return None
    if getattr(vista, "ultimo_resultado", None):
        return {
            "estado": "EXITO",
            "resultado_romano": vista.ultimo_resultado.resultado_romano,
            "resultado_decimal": vista.ultimo_resultado.resultado_decimal,
        }
    if vista.etiqueta_error and vista.etiqueta_error.text:
        return {"estado": "ERROR", "mensaje": vista.etiqueta_error.text}
    return None


def _primera_entrada_invalida(operando_a: str, operando_b: str):
    from src.frontend.sugerencias import CeldaInvalida
    for nombre, valor in (("Operando A", operando_a), ("Operando B", operando_b)):
        if valor:
            try:
                romano_a_entero(valor)
            except ErrorNumeroRomano:
                return CeldaInvalida(etiqueta=nombre)
    return None


def _estado_y_banderas(vista: Any) -> tuple[str, set[str]]:
    estado, banderas = "sin_resultado", set()
    if not getattr(vista.obtener_contexto_ia(), "desactualizado", False):
        if getattr(vista, "ultimo_resultado", None):
            estado = "exito"
        elif getattr(vista, "ultimo_error", None):
            estado = "error"
            bandera = vista.clasificar_error_romano(vista.ultimo_error)
            if bandera:
                banderas.add(bandera)
    if getattr(vista.pestanas_operacion, "value", None) == "multiplicacion":
        banderas.add("operacion_multiplicacion")
    return estado, banderas


class MixinContextoRomano:
    """Describe operandos, resultado y errores de la calculadora para Glosa."""

    @staticmethod
    def clasificar_error_romano(error: Exception) -> str | None:
        """Devuelve la sugerencia correspondiente al código o mensaje del error."""
        sugerencias_por_codigo = {
            ERROR_CERO_NO_REPRESENTABLE: "error_resta_cero",
            ERROR_NEGATIVO_NO_REPRESENTABLE: "error_resta_negativa",
            ERROR_SINTAXIS_INVALIDA: "error_sintaxis",
            ERROR_NO_CANONICO: "error_sintaxis",
            ERROR_ENTRADA_VACIA: "error_sintaxis",
        }
        codigo = getattr(error, "codigo", None)
        if codigo in sugerencias_por_codigo:
            return sugerencias_por_codigo[codigo]
        mensaje = str(error).lower()
        if "no existe el número cero" in mensaje:
            return "error_resta_cero"
        if "no existen los números negativos" in mensaje:
            return "error_resta_negativa"
        if "sintaxis válida" in mensaje or "canónica" in mensaje:
            return "error_sintaxis"
        return None

    def obtener_contexto_ia(self) -> ContextoIA:
        """Describe el ejercicio y conserva la detección de resultados desactualizados."""
        operando_a, operando_b, operacion = _leer_operandos(self)
        if not operando_a and not operando_b:
            return ContextoIA("romanos", "Números romanos", "Calculadora Romana", {},
                              estado=EstadoContexto(vacio=True))
        contexto = ContextoIA(
            "romanos", "Números romanos", f"Operación: {operacion}",
            _describir_operandos(operando_a, operando_b, operacion),
        )
        entrada_actual = capturar_romanos(operando_a, operando_b, operacion)
        contexto.desactualizado = esta_desactualizado(entrada_actual, getattr(self, "_huella_resultado", None))
        contexto.resultado = _resultado_contexto(self, contexto.desactualizado)
        return contexto

    def obtener_senales_ia(self) -> Any:
        """Combina el estado del cálculo con la primera entrada inválida para Glosa."""
        from src.frontend.sugerencias import Senales
        try:
            operando_a, operando_b, _ = _leer_operandos(self)
            celda_invalida = _primera_entrada_invalida(
                (operando_a or "").strip().upper(), (operando_b or "").strip().upper(),
            )
            estado, banderas = _estado_y_banderas(self)
            return Senales(herramienta="romanos", estado=estado, banderas=frozenset(banderas), invalida=celda_invalida)
        except Exception:
            return None
