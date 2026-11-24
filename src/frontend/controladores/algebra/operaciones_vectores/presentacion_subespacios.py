"""Adaptación exacta de resultados de subespacios para su presentación en la interfaz."""
from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
import re

from src.backend.modelos.escalares.conversion_fracciones import (
    texto_entero_exacto,
    texto_fraccion_exacta,
)
from src.backend.modelos.matriz import Matriz
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    CRITERIOS_TEOREMA_GENERADORES,
    MENSAJE_CALCULO_NO_VERIFICADO,
    MODO_GENERADORES,
    NOTA_DIMENSION_SUPERIOR,
    SUBTITULO_SUBESPACIO_CERO,
    VEREDICTO_SUBESPACIO_CERO,
    superindice_dimension,
    texto_herencia_axiomas,
    texto_veredicto_subespacio,
)

_CODIGOS_INTERNOS = frozenset({"VERIFICACION_INCONSISTENTE", "ERROR_INTERNO"})


def presentar_resultado_subespacio(
    resultado: Mapping,
    etiquetas: tuple[str, ...] = (),
    diagnostico: dict | None = None,
) -> dict:
    """Convierte la salida del motor en estructuras serializables y exactas para la vista."""
    if resultado.get("estado") != "EXITO":
        return _presentar_error(resultado, diagnostico)
    return {**_resumen_exito(resultado), **_traza_exito(resultado, etiquetas)}


def _resumen_exito(resultado: Mapping) -> dict:
    dimension_ambiente = int(resultado["dimension_ambiente"])
    dimension_subespacio = int(resultado["dimension"] or 0)
    return {
        "estado": "EXITO",
        "modo": resultado.get("modo") or MODO_GENERADORES,
        "codigo": resultado.get("codigo", "SUBESPACIO_GENERADO"),
        "clasificacion": resultado.get("clasificacion"),
        "mensaje": str(resultado.get("mensaje", "")),
        "dimension_ambiente": dimension_ambiente,
        "es_subespacio": bool(resultado.get("es_subespacio")),
        "es_espacio_vectorial": bool(resultado.get("es_subespacio")),
        "contiene_origen": bool(resultado.get("contiene_origen")),
        "es_vacio": bool(resultado.get("es_vacio")),
        "es_subespacio_cero": dimension_subespacio == 0,
        "rango": int(resultado.get("rango") or 0),
        "dimension": dimension_subespacio,
        "veredicto": texto_veredicto_subespacio(dimension_ambiente),
        "subtitulo_veredicto": _subtitulo_veredicto(dimension_subespacio, dimension_ambiente),
        "herencia_axiomas": texto_herencia_axiomas(dimension_ambiente),
        "descripcion_geometrica": descripcion_geometrica_subespacio(dimension_subespacio, dimension_ambiente),
    }


def _traza_exito(resultado: Mapping, etiquetas: tuple[str, ...]) -> dict:
    matriz_original = resultado["matriz_original"]
    matriz_reducida = resultado["matriz_reducida"]
    etiquetas_efectivas = _resolver_etiquetas(etiquetas, matriz_original)
    pivotes = tuple(resultado.get("columnas_pivote") or ())
    libres = tuple(resultado.get("columnas_libres") or ())
    return {
        "base": serializar_vectores(resultado.get("base") or ()),
        "indices_generadores_base": tuple(resultado.get("indices_generadores_base") or ()),
        "etiquetas_generadores_base": tuple(resultado.get("etiquetas_generadores_base") or ()),
        "etiquetas_generadores": etiquetas_efectivas,
        "columnas_pivote": pivotes,
        "columnas_libres": libres,
        "dependencias": _extraer_dependencias(matriz_reducida, etiquetas_efectivas, pivotes, libres),
        "matriz_original": serializar_matriz(matriz_original),
        "matriz_reducida": serializar_matriz(matriz_reducida),
        "pasos": serializar_pasos(resultado.get("pasos") or ()),
        "criterios": tuple(dict(criterio) for criterio in CRITERIOS_TEOREMA_GENERADORES),
        "comprobaciones": serializar_comprobaciones(resultado.get("comprobaciones") or ()),
    }


def _presentar_error(resultado: Mapping, diagnostico: dict | None) -> dict:
    codigo = str(resultado.get("codigo") or "ENTRADA_INVALIDA")
    es_interno = codigo in _CODIGOS_INTERNOS
    mensaje = (
        MENSAJE_CALCULO_NO_VERIFICADO if es_interno
        else (limpiar_texto(resultado.get("mensaje")) or MENSAJE_CALCULO_NO_VERIFICADO)
    )
    detalle = None if es_interno else diagnostico
    if detalle is None and codigo == "ENTRADA_INVALIDA":
        detalle = {
            "mensaje": mensaje, "ubicacion": None, "campo": None,
            "fila": None, "columna": None, "etiqueta": None, "componente": None,
        }
    return {
        "estado": "ERROR", "modo": resultado.get("modo") or MODO_GENERADORES, "codigo": codigo,
        "clasificacion": None, "mensaje": mensaje, "diagnostico": detalle,
        "dimension_ambiente": resultado.get("dimension_ambiente"), "es_subespacio": None,
        "es_espacio_vectorial": None, "base": None, "particular": None, "direcciones": None,
        "testigo": None, "familia_parametrica": None, "pasos": (),
        "comprobaciones": (), "criterios": (), "dependencias": (),
    }


def limpiar_texto(valor: object) -> str:
    """Normaliza espacios y saltos de línea en un texto de salida."""
    return " ".join(str(valor or "").split())


def _resolver_etiquetas(etiquetas: tuple[str, ...], matriz_original: Matriz | None) -> tuple[str, ...]:
    if etiquetas:
        return tuple(etiquetas)
    cantidad = matriz_original.columnas if matriz_original is not None else 0
    return tuple(f"v_{indice + 1}" for indice in range(cantidad))


def _subtitulo_veredicto(dimension: int, dimension_ambiente: int) -> str:
    if dimension == 0:
        return f"{VEREDICTO_SUBESPACIO_CERO}: {SUBTITULO_SUBESPACIO_CERO}"
    return f"Subespacio de dimensión {dimension} incluido en ℝ{superindice_dimension(dimension_ambiente)}."


def serializar_vectores(vectores: tuple[tuple[Fraction, ...], ...]) -> tuple[tuple[str, ...], ...]:
    """Serializa una secuencia de vectores racionales a cadenas exactas."""
    return tuple(tuple(texto_fraccion_exacta(valor) for valor in vector) for vector in vectores)


def serializar_matriz(matriz: Matriz | None) -> dict | None:
    """Serializa una matriz racional con todas sus celdas como texto exacto."""
    if matriz is None:
        return None
    return {
        "filas": matriz.filas,
        "columnas": matriz.columnas,
        "datos": tuple(tuple(texto_fraccion_exacta(valor) for valor in fila) for fila in matriz.datos),
    }


def _serializar_dato_exacto(valor: object) -> object:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, Fraction)):
        return texto_fraccion_exacta(valor)
    if isinstance(valor, Mapping):
        return {str(clave): _serializar_dato_exacto(dato) for clave, dato in valor.items()}
    if isinstance(valor, (tuple, list)):
        return tuple(_serializar_dato_exacto(dato) for dato in valor)
    return valor


def serializar_pasos(pasos: tuple) -> tuple[dict, ...]:
    """Serializa la traza de pasos preservando matrices y datos exactos."""
    return tuple(
        {
            "tipo": str(paso.get("tipo", "otro")),
            "datos": _serializar_dato_exacto(paso.get("datos") or {}),
            "matriz": serializar_matriz(paso.get("matriz")),
        }
        for paso in pasos
    )


def serializar_comprobaciones(comprobaciones: tuple[Mapping, ...]) -> tuple[dict, ...]:
    """Serializa las verificaciones exactas devueltas por el motor."""
    return tuple(
        {
            "tipo": str(elemento.get("tipo", "")),
            "coincide": bool(elemento.get("coincide", False)),
            "detalle": limpiar_texto(elemento.get("detalle", "")),
            "detalle_latex": str(elemento.get("detalle_latex") or ""),
            "fila": elemento.get("fila"),
            "indice": elemento.get("indice"),
            "origen": "motor",
        }
        for elemento in comprobaciones
    )


def _reduccion_respalda_dependencias(
    matriz_reducida: Matriz | None, pivotes: tuple[int, ...], libres: tuple[int, ...],
) -> bool:
    if matriz_reducida is None or len(pivotes) > matriz_reducida.filas:
        return False
    for fila_pivote, columna_pivote in enumerate(pivotes):
        if not 0 <= columna_pivote < matriz_reducida.columnas:
            return False
        if any(
            matriz_reducida.obtener(fila, columna_pivote) != (1 if fila == fila_pivote else 0)
            for fila in range(matriz_reducida.filas)
        ):
            return False
    return all(
        matriz_reducida.obtener(fila, columna_libre) == 0
        for columna_libre in libres
        for fila in range(len(pivotes), matriz_reducida.filas)
    )


def _extraer_dependencias(
    matriz_reducida: Matriz | None,
    etiquetas: tuple[str, ...],
    pivotes: tuple[int, ...],
    libres: tuple[int, ...],
) -> tuple[dict, ...]:
    if not libres:
        return ()
    if not _reduccion_respalda_dependencias(matriz_reducida, pivotes, libres):
        return tuple(
            {
                "indice": indice_libre,
                "etiqueta": etiquetas[indice_libre],
                "respaldada": False,
                "terminos": (),
                "texto": f"{etiquetas[indice_libre]} es dependiente según las columnas pivote.",
                "latex": "",
            }
            for indice_libre in libres
        )
    return tuple(_dependencia_columna(matriz_reducida, etiquetas, pivotes, indice_libre) for indice_libre in libres)


def _dependencia_columna(
    matriz_reducida: Matriz, etiquetas: tuple[str, ...], pivotes: tuple[int, ...], indice_libre: int,
) -> dict:
    etiqueta_libre = etiquetas[indice_libre]
    terminos = []
    for fila_pivote, columna_pivote in enumerate(pivotes):
        coeficiente = Fraction(matriz_reducida.obtener(fila_pivote, indice_libre))
        if coeficiente != 0:
            terminos.append((etiquetas[columna_pivote], coeficiente))
    return {
        "indice": indice_libre,
        "etiqueta": etiqueta_libre,
        "respaldada": True,
        "terminos": tuple((nombre, texto_fraccion_exacta(coeficiente)) for nombre, coeficiente in terminos),
        "texto": _formatear_dependencia_texto(etiqueta_libre, terminos),
        "latex": _formatear_dependencia_latex(etiqueta_libre, terminos),
    }


def _formatear_combinacion(terminos: list[tuple[str, Fraction]], formatear_escala, formatear_nombre) -> str:
    partes = []
    for posicion, (nombre, coeficiente) in enumerate(terminos):
        signo = " - " if coeficiente < 0 else (" + " if posicion > 0 else "")
        prefijo = "-" if posicion == 0 and coeficiente < 0 else signo
        magnitud = abs(coeficiente)
        escala = "" if magnitud == 1 else formatear_escala(magnitud)
        partes.append(f"{prefijo}{escala}{formatear_nombre(nombre)}")
    return "".join(partes)


def _formatear_dependencia_texto(etiqueta_libre: str, terminos: list[tuple[str, Fraction]]) -> str:
    if not terminos:
        return f"{etiqueta_libre} = 0"
    cuerpo = _formatear_combinacion(
        terminos, lambda magnitud: f"{texto_fraccion_exacta(magnitud)}·", lambda nombre: nombre,
    )
    return f"{etiqueta_libre} = {cuerpo}"


def _etiqueta_latex(etiqueta: str) -> str:
    coincidencia = re.fullmatch(r"([A-Za-z]+)_?(\d+)", etiqueta)
    if coincidencia:
        return f"{coincidencia.group(1)}_{{{coincidencia.group(2)}}}"
    segura = re.sub(r"[^A-Za-z0-9_ .-]", "", etiqueta) or "v"
    return rf"\text{{{segura}}}"


def fraccion_latex(valor: Fraction) -> str:
    """Formatea un racional exacto en LaTeX para enteros o fracciones."""
    numerador = texto_entero_exacto(valor.numerator)
    if valor.denominator == 1:
        return numerador
    return rf"\frac{{{numerador}}}{{{texto_entero_exacto(valor.denominator)}}}"


def _formatear_dependencia_latex(etiqueta_libre: str, terminos: list[tuple[str, Fraction]]) -> str:
    izquierda = _etiqueta_latex(etiqueta_libre)
    if not terminos:
        return f"{izquierda} = \\mathbf{{0}}"
    return f"{izquierda} = {_formatear_combinacion(terminos, fraccion_latex, _etiqueta_latex)}"


def descripcion_geometrica_subespacio(dimension: int, dimension_ambiente: int) -> str:
    """Resume geométricamente un subespacio de dimensión dada dentro de ℝⁿ."""
    ambiente = f"ℝ{superindice_dimension(dimension_ambiente)}"
    if dimension_ambiente > 3:
        return f"Subespacio de dimensión {dimension} en {ambiente}; contiene al origen. {NOTA_DIMENSION_SUPERIOR}"
    if dimension == 0:
        return f"Punto único en el origen de {ambiente}, con dimensión 0; contiene al origen."
    if dimension == dimension_ambiente:
        return f"Todo el espacio ambiente {ambiente}, con dimensión {dimension}; contiene al origen."
    if dimension == 1:
        return f"Recta que pasa por el origen en {ambiente}, de dimensión 1."
    return f"Plano que pasa por el origen en {ambiente}, de dimensión 2."
