"""Construcción pura de pasos y grupos didácticos para la Calculadora de Números Romanos."""

from __future__ import annotations

from typing import Any
from functools import partial
from ._cuerpo_numerico import _CuerpoNumerico


from src.frontend.componentes.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)

from src.backend.resolutores.sistemas_numericos import calculadora_romana
from src.backend.resolutores.sistemas_numericos.pasos_didacticos import desglosar_sumas_sucesivas
from ._plantillas_numericas import renderizar_plantilla, renderizar_tabla


def _crear_tarjeta_operando(etiqueta: str, romano: str, decimal: int) -> str:
    """Genera la tarjeta HTML de decodificación de un operando."""
    return renderizar_plantilla("operando", {"etiqueta": etiqueta, "romano": romano, "decimal": decimal})


def _crear_pasos_decodificacion(operando_a: str, decimal_a: int, operando_b: str, decimal_b: int, indice_grupo: int) -> list[dict[str, Any]]:
    """Crea los 2 pasos iniciales de decodificación de operandos a decimal."""
    titulo_paso = "Decodificación de operandos a decimal"
    return [
        {
            "tipo": "decodificacion", "etiqueta_tipo": "Decodificación",
            "descripcion": f"Operando A: {operando_a} = {decimal_a}",
            "explicacion": f"Decodificamos el numeral romano {operando_a} a su valor decimal {decimal_a} aplicando reglas aditivas y sustractivas.",
            "cuerpo": _CuerpoNumerico(_crear_tarjeta_operando("Operando A", operando_a, decimal_a)),
            "indice_grupo": indice_grupo, "titulo_grupo": titulo_paso,
        },
        {
            "tipo": "decodificacion", "etiqueta_tipo": "Decodificación",
            "descripcion": f"Operando B: {operando_b} = {decimal_b}",
            "explicacion": f"Decodificamos el numeral romano {operando_b} a su valor decimal {decimal_b} aplicando reglas aditivas y sustractivas.",
            "cuerpo": _CuerpoNumerico(_crear_tarjeta_operando("Operando B", operando_b, decimal_b)),
            "indice_grupo": indice_grupo, "titulo_grupo": titulo_paso,
        },
    ]


def _crear_tabla_iteraciones(operando_a: str, decimal_a: int, hasta_iteracion: int, total_iteraciones: int, resultado_romano: str) -> str:
    """Genera la tabla HTML de sumas sucesivas hasta la iteración actual."""
    filas = []
    for iteracion in desglosar_sumas_sucesivas(decimal_a, total_iteraciones)[:hasta_iteracion]:
        i, acumulado = iteracion["indice"], iteracion["acumulado"]
        filas.append(renderizar_plantilla("iteracion", {
            "clase": "numericos-fila-activa" if i == hasta_iteracion else "", "indice": i,
            "romano": operando_a, "decimal": decimal_a, "acumulado": acumulado,
            "parcial": resultado_romano if i == total_iteraciones else acumulado,
        }))
    return renderizar_tabla(("Iteración", "Operando Sumado", "Acumulado (Dec)", "Valor Parcial"), filas)


def _crear_pasos_multiplicacion(operando_a: tuple, operando_b: tuple, resultado: tuple, indice_grupo: int, titulo: str) -> list[dict[str, Any]]:
    """Construye la secuencia de pasos para multiplicación romana por sumas sucesivas."""
    operando_a, decimal_a = operando_a
    operando_b, decimal_b = operando_b
    resultado_romano, resultado_decimal = resultado
    pasos: list[dict[str, Any]] = []
    html_definicion = renderizar_plantilla("definicion", {"romano_a": operando_a, "romano_b": operando_b,
                                                "decimal_a": decimal_a, "decimal_b": decimal_b})
    pasos.append({
        "tipo": "definicion", "etiqueta_tipo": "Definición",
        "descripcion": f"Definición: sumar {decimal_a}, {decimal_b} veces",
        "explicacion": f"La multiplicación romana se realiza sumando sucesivamente {operando_a} ({decimal_a}) un total de {decimal_b} veces.",
        "cuerpo": _CuerpoNumerico(html_definicion), "indice_grupo": indice_grupo, "titulo_grupo": titulo,
    })

    for iteracion in desglosar_sumas_sucesivas(decimal_a, decimal_b):
        i, acumulado_parcial = iteracion["indice"], iteracion["acumulado"]
        pasos.append({
            "tipo": "iteracion", "etiqueta_tipo": "Iteración",
            "descripcion": f"Paso {i}: acumulado = {acumulado_parcial}",
            "explicacion": f"Iteración {i} de {decimal_b}: sumamos {decimal_a} al acumulado previo, alcanzando {acumulado_parcial}.",
            "cuerpo": _CuerpoNumerico(partial(_crear_tabla_iteraciones, operando_a, decimal_a, i, decimal_b, resultado_romano)),
            "indice_grupo": indice_grupo, "titulo_grupo": titulo,
        })

    html_producto = renderizar_plantilla("producto", {"decimal_a": decimal_a, "decimal_b": decimal_b, "resultado": resultado_decimal})
    pasos.append({
        "tipo": "producto", "etiqueta_tipo": "Producto",
        "descripcion": f"Producto total: {decimal_a} × {decimal_b} = {resultado_decimal}",
        "explicacion": f"Completadas las {decimal_b} sumas sucesivas, el producto decimal final es {resultado_decimal}.",
        "cuerpo": _CuerpoNumerico(html_producto), "indice_grupo": indice_grupo, "titulo_grupo": titulo,
    })
    return pasos


def _crear_paso_validacion_resta(decimal_a: int, decimal_b: int, indice_grupo: int, titulo: str) -> dict[str, Any]:
    """Crea el paso de validación A > B para la resta romana."""
    html_validacion = renderizar_plantilla("validacion", {"decimal_a": decimal_a, "decimal_b": decimal_b})
    return {
        "tipo": "validacion", "etiqueta_tipo": "Validación",
        "descripcion": f"Validación: {decimal_a} > {decimal_b}",
        "explicacion": "Los números romanos no contemplan el cero ni valores negativos. El minuendo debe superar al sustraendo.",
        "cuerpo": _CuerpoNumerico(html_validacion), "indice_grupo": indice_grupo, "titulo_grupo": titulo,
    }


def _crear_pasos_operacion(operacion: str, operando_a: tuple, operando_b: tuple, resultado: tuple, indice_grupo: int) -> tuple[str, str, list[dict[str, Any]]]:
    """Genera los pasos de la operación aritmética según su tipo."""
    operando_a, decimal_a = operando_a
    operando_b, decimal_b = operando_b
    resultado_romano, resultado_decimal = resultado
    if operacion == "multiplicacion":
        titulo = "Multiplicación mediante sumas sucesivas"
        return titulo, "multiplicacion", _crear_pasos_multiplicacion((operando_a, decimal_a), (operando_b, decimal_b), (resultado_romano, resultado_decimal), indice_grupo, titulo)

    nombre = "Suma" if operacion == "suma" else "Resta"
    titulo, simbolo = f"Ejecución aritmética de la {nombre.lower()}", "+" if operacion == "suma" else "−"
    pasos: list[dict[str, Any]] = []
    if operacion == "resta":
        pasos.append(_crear_paso_validacion_resta(decimal_a, decimal_b, indice_grupo, titulo))

    html_operacion = renderizar_plantilla("operacion", {"decimal_a": decimal_a, "decimal_b": decimal_b,
                                              "simbolo": simbolo, "resultado": resultado_decimal})
    explicacion_operacion = "Sumamos directamente los valores decimales de ambos operandos." if operacion == "suma" else f"Restamos {decimal_b} de {decimal_a} obteniendo {resultado_decimal}."
    pasos.append({
        "tipo": "operacion", "etiqueta_tipo": "Operación",
        "descripcion": f"{decimal_a} {simbolo} {decimal_b} = {resultado_decimal}", "explicacion": explicacion_operacion,
        "cuerpo": _CuerpoNumerico(html_operacion), "indice_grupo": indice_grupo, "titulo_grupo": titulo,
    })
    return titulo, "operacion", pasos


def _crear_tabla_construccion(pasos_canonicos: list[dict], hasta_indice: int) -> str:
    """Genera la tabla HTML de sustracciones voraces hasta la fila actual."""
    filas = []
    for indice, paso in enumerate(pasos_canonicos[:hasta_indice + 1]):
        filas.append(renderizar_plantilla("construccion", {
            **paso, "valor": paso["valor_restado"],
            "clase": "numericos-fila-activa" if indice == hasta_indice else "",
        }))
    return renderizar_tabla(("Sustracción", "Glifo Asignado", "Residuo"), filas)


def _crear_pasos_construccion(operando_a: str, operando_b: str, simbolo_operacion: str, resultado: tuple, indice_grupo: int) -> list[dict[str, Any]]:
    """Genera los pasos de notación y construcción canónica romana."""
    resultado_romano, resultado_decimal = resultado
    titulo_grupo = "Notación y construcción canónica romana"
    pasos_canonicos = calculadora_romana.desglosar_pasos_canonicos(resultado_decimal)
    pasos: list[dict[str, Any]] = []

    for i, paso in enumerate(pasos_canonicos):
        descripcion = f"Sustracción: {paso['anterior']} − {paso['valor_restado']} = {paso['restante']} (glifo {paso['simbolo']})"
        explicacion = f"Restamos el valor {paso['valor_restado']}, asignamos el glifo {paso['simbolo']} y queda un residuo de {paso['restante']}."
        pasos.append({
            "tipo": "construccion", "etiqueta_tipo": "Construcción",
            "descripcion": descripcion, "explicacion": explicacion,
            "cuerpo": _CuerpoNumerico(partial(_crear_tabla_construccion, pasos_canonicos, i)),
            "indice_grupo": indice_grupo, "titulo_grupo": titulo_grupo,
        })

    html_final = renderizar_plantilla("resultado", {"romano_a": operando_a, "romano_b": operando_b,
                                                 "simbolo": simbolo_operacion, "romano": resultado_romano, "decimal": resultado_decimal})
    pasos.append({
        "tipo": "resultado", "etiqueta_tipo": "Resultado",
        "descripcion": f"{operando_a} {simbolo_operacion} {operando_b} = {resultado_romano} ({resultado_decimal})",
        "explicacion": "Ensamblamos todos los glifos canónicos para formar el numeral romano definitivo.",
        "cuerpo": _CuerpoNumerico(html_final), "indice_grupo": indice_grupo, "titulo_grupo": titulo_grupo,
    })
    return pasos


def _convertir_a_pasos_reproductor(pasos_crudos: list[dict[str, Any]]) -> tuple[PasoReproductor, ...]:
    """Convierte los diccionarios de pasos en instancias inmutables de PasoReproductor."""
    total = len(pasos_crudos)
    return tuple(
        PasoReproductor(
            indice=i, tipo=paso["tipo"], etiqueta_tipo=paso["etiqueta_tipo"],
            descripcion=paso["descripcion"], explicacion=paso["explicacion"],
            indice_grupo=paso["indice_grupo"], cuerpo=paso["cuerpo"],
            meta_explicar={"indice": i + 1, "total": total, "tipo": "otro", "operacion": f"{paso['titulo_grupo']}: {paso['descripcion']}", "filas_antes": {}, "filas_despues": {}, "columnas": None},
        )
        for i, paso in enumerate(pasos_crudos)
    )


def construir_pasos_romanos(
    resultado: Any, operacion: str
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos didácticos para una operación romana."""
    if not resultado:
        return (), ()

    operando_a, operando_b = getattr(resultado, "operando_a_romano", ""), getattr(resultado, "operando_b_romano", "")
    decimal_a, decimal_b = getattr(resultado, "operando_a_decimal", 0), getattr(resultado, "operando_b_decimal", 0)
    resultado_romano, resultado_decimal = getattr(resultado, "resultado_romano", ""), getattr(resultado, "resultado_decimal", 0)
    simbolo_operacion = {"suma": "+", "resta": "−", "multiplicacion": "×"}.get(operacion, "+")

    pasos_crudos: list[dict[str, Any]] = []
    grupos: list[GrupoReproductor] = []

    pasos_decodificacion = _crear_pasos_decodificacion(operando_a, decimal_a, operando_b, decimal_b, len(grupos))
    indices_decodificacion = tuple(range(len(pasos_crudos), len(pasos_crudos) + len(pasos_decodificacion)))
    pasos_crudos.extend(pasos_decodificacion)
    grupos.append(GrupoReproductor(titulo="Decodificación de operandos a decimal", resumen=f"{len(indices_decodificacion)} operaciones", tipo="decodificacion", indices_pasos=indices_decodificacion))

    titulo_operacion, tipo_operacion, pasos_operacion = _crear_pasos_operacion(operacion, (operando_a, decimal_a), (operando_b, decimal_b), (resultado_romano, resultado_decimal), len(grupos))
    indices_operacion = tuple(range(len(pasos_crudos), len(pasos_crudos) + len(pasos_operacion)))
    pasos_crudos.extend(pasos_operacion)
    grupos.append(GrupoReproductor(titulo=titulo_operacion, resumen=f"{len(indices_operacion)} operaciones", tipo=tipo_operacion, indices_pasos=indices_operacion))

    pasos_construccion = _crear_pasos_construccion(operando_a, operando_b, simbolo_operacion, (resultado_romano, resultado_decimal), len(grupos))
    indices_construccion = tuple(range(len(pasos_crudos), len(pasos_crudos) + len(pasos_construccion)))
    pasos_crudos.extend(pasos_construccion)
    grupos.append(GrupoReproductor(titulo="Notación y construcción canónica romana", resumen=f"{len(indices_construccion)} operaciones", tipo="construccion", indices_pasos=indices_construccion))

    return _convertir_a_pasos_reproductor(pasos_crudos), tuple(grupos)
