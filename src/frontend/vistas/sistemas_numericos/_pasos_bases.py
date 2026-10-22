"""Construcción pura de pasos y grupos didácticos para el conversor de bases."""

from __future__ import annotations

from typing import Any
from functools import partial
from src.backend.resolutores.sistemas_numericos.pasos_didacticos import calcular_subtotal_expansion

from src.frontend.componentes.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)

_NOMBRES_BASE = {2: "Binario", 8: "Octal", 10: "Decimal", 16: "Hexadecimal"}
from ._plantillas_numericas import renderizar_plantilla, renderizar_tabla, renderizar_lectura
from ._cuerpo_numerico import _CuerpoNumerico


def _crear_tabla_expansion(terminos: list[dict], hasta_indice: int, base: int) -> str:
    """Genera la tabla HTML para un paso parcial de expansión posicional."""
    filas = []
    for indice, termino in enumerate(terminos[:hasta_indice + 1]):
        filas.append(renderizar_plantilla("expansion", {
            **termino, "base": base,
            "clase": "numericos-fila-activa" if indice == hasta_indice else "",
        }))
    pie = renderizar_plantilla("subtotal", {"subtotal": calcular_subtotal_expansion(terminos, hasta_indice)})
    return renderizar_tabla(("Dígito", "Valor Int", "Posición", "Peso", "Subtotal"), filas, pie)


def _crear_tabla_division(filas: list[dict], hasta_indice: int) -> str:
    """Genera la tabla HTML para un paso parcial de divisiones sucesivas."""
    contenido = [renderizar_plantilla("division", {
        **fila, "clase": "numericos-residuo-activo" if indice == hasta_indice else "",
    }) for indice, fila in enumerate(filas[:hasta_indice + 1])]
    return renderizar_tabla(("Dividendo", "Divisor", "Cociente", "Residuo"), contenido)


def _crear_paso_resultado_expansion(terminos: list[dict], base: int, valor_total: str, es_negativo: bool, grupo: tuple) -> dict[str, Any]:
    """Crea el paso final de resultado para la expansión posicional."""
    indice_grupo, titulo = grupo
    terminos_ecuacion = [f"({termino['valor']} \\times {base}^{{{termino['potencia']}}})" for termino in terminos]
    ecuacion = " + ".join(terminos_ecuacion)
    if es_negativo:
        ecuacion = f"-\\left[ {ecuacion} \\right]"
    ecuacion += f" = {valor_total}"
    tabla = partial(_crear_tabla_expansion, terminos, len(terminos) - 1, base)
    explicacion = (
        "Sumamos las contribuciones posicionales y aplicamos el signo negativo al total."
        if es_negativo
        else "Sumamos todas las contribuciones posicionales para obtener el valor decimal."
    )
    return {
        "tipo": "resultado", "etiqueta_tipo": "Resultado",
        "descripcion": f"Total expansión posicional: {valor_total}",
        "explicacion": explicacion,
        "cuerpo": _CuerpoNumerico(tabla, ecuacion),
        "indice_grupo": indice_grupo, "titulo_grupo": titulo,
    }


def _generar_pasos_expansion(paso_crudo: dict, titulo: str, indice_grupo: int) -> list[dict[str, Any]]:
    """Genera la lista de pasos para una conversión por expansión posicional."""
    terminos = paso_crudo.get("terminos", [])
    base = paso_crudo.get("base_origen", 10)
    valor_total = paso_crudo.get("total", "0")
    es_negativo = paso_crudo.get("es_negativo", False)

    pasos: list[dict[str, Any]] = []
    for i, termino in enumerate(terminos):
        digito, valor, potencia, peso, producto = termino["digito"], termino["valor"], termino["potencia"], termino["peso"], termino["producto"]
        descripcion = f"Dígito {digito} (valor {valor}) × {base}^{potencia} = {producto}"
        explicacion = f"Posición {potencia} contando desde la derecha; el peso es {base}^{potencia} = {peso} y aporta {producto} al subtotal."
        pasos.append({
            "tipo": "expansion", "etiqueta_tipo": "Expansión",
            "descripcion": descripcion, "explicacion": explicacion,
            "cuerpo": _CuerpoNumerico(partial(_crear_tabla_expansion, terminos, i, base)),
            "indice_grupo": indice_grupo, "titulo_grupo": titulo,
        })

    pasos.append(_crear_paso_resultado_expansion(terminos, base, valor_total, es_negativo, (indice_grupo, titulo)))
    return pasos


def _crear_paso_lectura_division(filas: list[dict], base_destino: int, resultado: str, lectura: str, grupo: tuple) -> dict[str, Any]:
    """Crea el paso final de lectura para las divisiones sucesivas."""
    indice_grupo, titulo = grupo
    html_lectura = partial(_crear_html_lectura, filas, lectura)
    return {
        "tipo": "lectura", "etiqueta_tipo": "Lectura",
        "descripcion": f"Resultado en base {base_destino}: {resultado}",
        "explicacion": "Leemos los residuos de abajo hacia arriba para construir el número final.",
        "cuerpo": _CuerpoNumerico(html_lectura, f"{resultado}_{{{base_destino}}}"),
        "indice_grupo": indice_grupo, "titulo_grupo": titulo,
    }


def _generar_pasos_division(paso_crudo: dict, titulo: str, indice_grupo: int) -> list[dict[str, Any]]:
    """Genera la lista de pasos para una conversión por divisiones sucesivas."""
    filas = paso_crudo.get("filas", [])
    base_destino = paso_crudo.get("base_destino", 10)
    resultado = paso_crudo.get("resultado", "0")
    lectura = paso_crudo.get("lectura", "Se lee de abajo hacia arriba")

    pasos: list[dict[str, Any]] = []
    for i, fila in enumerate(filas):
        dividendo, divisor, cociente, residuo = fila["dividendo"], fila["divisor"], fila["cociente"], fila["residuo"]
        descripcion = f"{dividendo} ÷ {divisor} = {cociente}, residuo {residuo}"
        explicacion = f"Dividimos entre {divisor}; guardamos el residuo {residuo} para formar el número en la base destino."
        pasos.append({
            "tipo": "division", "etiqueta_tipo": "División",
            "descripcion": descripcion, "explicacion": explicacion,
            "cuerpo": _CuerpoNumerico(partial(_crear_tabla_division, filas, i)),
            "indice_grupo": indice_grupo, "titulo_grupo": titulo,
        })

    pasos.append(_crear_paso_lectura_division(filas, base_destino, resultado, lectura, (indice_grupo, titulo)))
    return pasos


def _crear_html_lectura(filas: list[dict], lectura: str) -> str:
    return renderizar_lectura(_crear_tabla_division(filas, len(filas) - 1), lectura)


def _procesar_conversion(paso: dict, indice_conversion: int, indice_grupo: int) -> tuple[str, str, list[dict[str, Any]]]:
    """Determina el título, tipo y pasos de una conversión individual."""
    tipo = paso.get("tipo")
    if tipo == "expansion_posicional":
        nombre = _NOMBRES_BASE.get(paso.get("base_origen"), f"Base {paso.get('base_origen')}")
        titulo = f"{indice_conversion}. Expansión Posicional desde {nombre}"
        return titulo, "expansion", _generar_pasos_expansion(paso, titulo, indice_grupo)
    if tipo == "division_sucesiva":
        nombre = _NOMBRES_BASE.get(paso.get("base_destino"), f"Base {paso.get('base_destino')}")
        titulo = f"{indice_conversion}. Divisiones Sucesivas hacia {nombre}"
        return titulo, "division", _generar_pasos_division(paso, titulo, indice_grupo)
    return "", "", []


def construir_pasos_bases(
    datos_o_pasos: dict | list,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte los pasos del conversor de bases en tuplas de pasos y grupos didácticos."""
    conversiones_crudas = datos_o_pasos.get("pasos", []) if isinstance(datos_o_pasos, dict) else (datos_o_pasos or [])
    if not conversiones_crudas:
        return (), ()

    pasos_crudos: list[dict[str, Any]] = []
    grupos: list[GrupoReproductor] = []

    for indice_conversion, paso in enumerate(conversiones_crudas, start=1):
        titulo, tipo_grupo, pasos_conversion = _procesar_conversion(paso, indice_conversion, len(grupos))
        if not pasos_conversion:
            continue

        indices_grupo = tuple(range(len(pasos_crudos), len(pasos_crudos) + len(pasos_conversion)))
        pasos_crudos.extend(pasos_conversion)
        cantidad_pasos = len(indices_grupo)
        resumen = f"{cantidad_pasos} operaciones" if cantidad_pasos != 1 else "1 operación"
        grupos.append(GrupoReproductor(titulo=titulo, resumen=resumen, tipo=tipo_grupo, indices_pasos=indices_grupo))

    total = len(pasos_crudos)
    pasos = [
        PasoReproductor(
            indice=i, tipo=paso["tipo"], etiqueta_tipo=paso["etiqueta_tipo"],
            descripcion=paso["descripcion"], explicacion=paso["explicacion"],
            indice_grupo=paso["indice_grupo"], cuerpo=paso["cuerpo"],
            meta_explicar={"indice": i + 1, "total": total, "tipo": "otro", "operacion": f"{paso['titulo_grupo']}: {paso['descripcion']}", "filas_antes": {}, "filas_despues": {}, "columnas": None},
        )
        for i, paso in enumerate(pasos_crudos)
    ]
    return tuple(pasos), tuple(grupos)
