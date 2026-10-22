"""Recortes progresivos del contexto de IA que priorizan la captura y el foco actuales."""

import copy
import dataclasses
import json
from typing import Any

from src.ai.constantes import (
    LONGITUD_ETIQUETA_RESERVA,
    LONGITUD_TEXTO_CORTO,
    MAXIMO_CARACTERES_CONTEXTO,
)


def _valor_json_predeterminado(objeto: Any) -> Any:
    """Serializador por defecto para fracciones y objetos estructurados."""
    from fractions import Fraction
    if isinstance(objeto, Fraction):
        return str(objeto)
    return str(objeto)[:LONGITUD_TEXTO_CORTO]


def construir_contexto_minimo(
    herramienta: str, vista: str, maximo_caracteres: int
) -> str:
    """Acota el bloque completo; lanza ValueError si el límite no admite el esquema mínimo."""
    nombre_herramienta = str(herramienta or "")[:LONGITUD_ETIQUETA_RESERVA]
    nombre_vista = str(vista or "")[:LONGITUD_ETIQUETA_RESERVA]
    datos = {"version": 1, "herramienta": nombre_herramienta, "vista": nombre_vista,
             "metadatos": {"truncado": True}}
    base = dict(datos, herramienta="", vista="")
    longitud_base = len(_formatear_bloque_contexto(base))
    if maximo_caracteres < longitud_base:
        raise ValueError("El límite de contexto no admite el bloque mínimo de datos.")
    bloque = _formatear_bloque_contexto(datos)
    if len(bloque) > maximo_caracteres:
        disponible = maximo_caracteres - longitud_base
        longitud_herramienta = min(len(nombre_herramienta), disponible // 2)
        longitud_vista = min(len(nombre_vista), disponible - longitud_herramienta)
        datos["herramienta"] = nombre_herramienta[:longitud_herramienta]
        datos["vista"] = nombre_vista[:longitud_vista]
        bloque = _formatear_bloque_contexto(datos)
    while len(bloque) > maximo_caracteres:
        campo = "herramienta" if len(datos["herramienta"]) > len(datos["vista"]) else "vista"
        datos[campo] = datos[campo][:-1]
        bloque = _formatear_bloque_contexto(datos)
    return bloque


def _recorte_eliminar_detalle_foco(contexto: Any) -> None:
    """Elimina el detalle opcional del paso enfocado."""
    if contexto.foco and contexto.foco.captura.detalle:
        captura = dataclasses.replace(contexto.foco.captura, detalle=None)
        contexto.foco = dataclasses.replace(contexto.foco, captura=captura)


def _recorte_eliminar_extras_resultado(contexto: Any) -> None:
    """Elimina pasos y matrices intermedias del resultado."""
    if contexto.resultado:
        for clave in ("inversa", "pasos", "pasos_segmento"):
            contexto.resultado.pop(clave, None)


def _reducir_matriz_en_diccionario(matriz: dict, ancho_objetivo: int) -> None:
    """Reduce la ventana visible de una matriz en el diccionario de entrada."""
    if not isinstance(matriz, dict) or "datos" not in matriz:
        return
    if "ventana" not in matriz:
        total_filas = len(matriz["datos"])
        total_columnas = len(matriz["datos"][0]) if total_filas else 0
        matriz["ventana"] = [total_filas, total_columnas]

    filas_visibles, columnas_visibles = matriz["ventana"]
    nuevas_filas = min(filas_visibles, ancho_objetivo)
    nuevas_columnas = min(columnas_visibles, ancho_objetivo)
    if nuevas_filas == 0:
        matriz.pop("datos", None)
        matriz["ventana"] = [0, 0]
        return

    matriz["datos"] = [fila[:nuevas_columnas] for fila in matriz["datos"][:nuevas_filas]]
    matriz["ventana"] = [nuevas_filas, nuevas_columnas]


def _reducir_vector_en_diccionario(vector: dict, ancho_objetivo: int) -> None:
    """Reduce el vector en diccionario si su longitud excede el objetivo."""
    if len(vector.get("datos", [])) <= ancho_objetivo:
        return
    vector["datos"] = vector["datos"][:ancho_objetivo]
    if "ventana" not in vector:
        orientacion = vector.get("orientacion")
        vector["ventana"] = [ancho_objetivo, 1] if orientacion == "columna" else [1, ancho_objetivo]


def _reducir_elemento_entrada(elemento: Any, ancho_objetivo: int) -> None:
    """Reduce matrices o vectores individuales encontrados en la entrada."""
    if not isinstance(elemento, dict):
        return
    if "filas" in elemento and "columnas" in elemento and "datos" in elemento:
        _reducir_matriz_en_diccionario(elemento, ancho_objetivo)
    elif "datos" in elemento and "orientacion" in elemento:
        _reducir_vector_en_diccionario(elemento, ancho_objetivo)


def _recorte_ventanas_entrada(contexto: Any, ancho_objetivo: int) -> None:
    """Reduce el tamaño de ventana de matrices o vectores."""
    if "datos" in contexto.entrada:
        _reducir_matriz_en_diccionario(contexto.entrada, ancho_objetivo)
        return
    for elemento in contexto.entrada.values():
        _reducir_elemento_entrada(elemento, ancho_objetivo)


def _recorte_resultado_a_estado(contexto: Any) -> None:
    """Conserva únicamente el estado y mensaje esencial del resultado."""
    if not contexto.resultado:
        return
    estado = contexto.resultado.get("estado", "")
    linea = (
        contexto.resultado.get("mensaje")
        or contexto.resultado.get("clasificacion")
        or ""
    )
    contexto.resultado = {"estado": estado}
    if linea:
        contexto.resultado["mensaje"] = linea


def _conservar_solo_primera_fila(filas: dict) -> None:
    """Conserva únicamente la primera fila del diccionario dejando las demás fuera."""
    if len(filas) <= 1:
        return
    primera_clave = next(iter(filas.keys()))
    for clave in list(filas.keys()):
        if clave != primera_clave:
            filas.pop(clave, None)


def _recorte_filas_foco(contexto: Any) -> None:
    """Conserva únicamente la primera fila antes y después en el foco."""
    if not contexto.foco:
        return
    _conservar_solo_primera_fila(contexto.foco.captura.filas_antes)
    _conservar_solo_primera_fila(contexto.foco.captura.filas_despues)


def _truncar_filas_a_4_columnas(filas: dict) -> None:
    """Trunca las listas de valores de cada fila a 4 elementos."""
    for clave in filas:
        filas[clave] = filas[clave][:4]


def _recorte_columnas_foco(contexto: Any) -> None:
    """Trunca celdas de filas a cuatro elementos y retira el rango de columnas del foco."""
    if not contexto.foco:
        return
    _truncar_filas_a_4_columnas(contexto.foco.captura.filas_antes)
    _truncar_filas_a_4_columnas(contexto.foco.captura.filas_despues)
    captura = dataclasses.replace(contexto.foco.captura, columnas=None)
    contexto.foco = dataclasses.replace(contexto.foco, captura=captura)


def _construir_foco_diccionario(foco: Any) -> dict:
    """Serializa la referencia y su captura sin incluir campos opcionales vacíos."""
    datos = {
        "indice": foco.indice,
        "total": foco.total,
        "tipo": foco.tipo,
        "operacion": foco.operacion,
        "filas_antes": foco.captura.filas_antes,
        "filas_despues": foco.captura.filas_despues,
    }
    if foco.captura.columnas:
        datos["columnas"] = list(foco.captura.columnas)
    if foco.captura.detalle:
        datos["detalle"] = foco.captura.detalle
    return datos


def _construir_meta_contexto(contexto: Any, truncado: bool) -> dict:
    """Construye metadatos de ventana, obsolescencia y truncado."""
    from src.ai.matrices_contexto import generar_nota_ventana

    metadatos = {}
    if contexto.nota_ventana:
        metadatos["ventana"] = contexto.nota_ventana
    elif isinstance(contexto.entrada, dict):
        nota = generar_nota_ventana(*contexto.entrada.values())
        if nota:
            metadatos["ventana"] = nota
    if contexto.desactualizado:
        metadatos["desactualizado"] = True
    if truncado:
        metadatos["truncado"] = True
    return metadatos


def _construir_diccionario_contexto(contexto: Any, truncado: bool) -> dict:
    """Construye el diccionario de datos para serialización JSON."""
    datos = {
        "version": 1,
        "herramienta": contexto.herramienta,
        "vista": contexto.vista,
        "entrada": contexto.entrada,
    }
    if contexto.resultado is not None:
        datos["resultado"] = contexto.resultado
    if contexto.foco is not None:
        datos["foco"] = _construir_foco_diccionario(contexto.foco)
    metadatos = _construir_meta_contexto(contexto, truncado)
    if metadatos:
        datos["metadatos"] = metadatos
    return datos


def _formatear_cadena_contexto(contexto: Any, truncado: bool = False) -> str:
    """Genera el bloque delimitado [CONTEXTO] en formato JSON."""
    datos = _construir_diccionario_contexto(contexto, truncado)
    return _formatear_bloque_contexto(datos)


def _formatear_bloque_contexto(datos: dict) -> str:
    contenido = json.dumps(
        datos, ensure_ascii=False, separators=(",", ":"), default=_valor_json_predeterminado
    )
    return f"[CONTEXTO]\n{contenido}\n[/CONTEXTO]"


def ejecutar_cascada_recortes(
    contexto: Any, *, maximo_caracteres: int = MAXIMO_CARACTERES_CONTEXTO
) -> str:
    """Aplica la cascada ordenada de estrategias de recorte hasta cumplir el límite."""
    contexto_trabajo = copy.deepcopy(contexto)
    cadena = _formatear_cadena_contexto(contexto_trabajo, truncado=False)
    if len(cadena) <= maximo_caracteres:
        return cadena

    pasos_recorte = [
        _recorte_eliminar_detalle_foco,
        _recorte_eliminar_extras_resultado,
        lambda ejercicio: _recorte_ventanas_entrada(ejercicio, 4),
        lambda ejercicio: _recorte_ventanas_entrada(ejercicio, 3),
        lambda ejercicio: _recorte_ventanas_entrada(ejercicio, 0),
        _recorte_resultado_a_estado,
        _recorte_filas_foco,
        _recorte_columnas_foco,
    ]

    for aplicar_estrategia in pasos_recorte:
        aplicar_estrategia(contexto_trabajo)
        cadena = _formatear_cadena_contexto(contexto_trabajo, truncado=True)
        if len(cadena) <= maximo_caracteres:
            return cadena

    return construir_contexto_minimo(
        contexto_trabajo.herramienta, contexto_trabajo.vista, maximo_caracteres
    )
