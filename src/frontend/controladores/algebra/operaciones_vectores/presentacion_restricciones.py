"""Adaptación exacta de resultados del modo restricciones para presentación."""
from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction

from src.backend.modelos.escalares.conversion_fracciones import texto_fraccion_exacta
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_subespacios import (
    descripcion_geometrica_subespacio, fraccion_latex, limpiar_texto,
    serializar_comprobaciones, serializar_matriz, serializar_pasos, serializar_vectores,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    ESTADO_CRITERIO_CUMPLE, ESTADO_CRITERIO_NO_CUMPLE, ESTADO_CRITERIO_VACUO,
    MODO_RESTRICCIONES, NOTA_DIMENSION_SUPERIOR, SUBTITULO_CONJUNTO_VACIO,
    SUBTITULO_SUBESPACIO_CERO, VEREDICTO_CONJUNTO_VACIO, VEREDICTO_SUBESPACIO_CERO,
    superindice_dimension, texto_herencia_axiomas,
    texto_veredicto_no_subespacio, texto_veredicto_subespacio,
)

_LIMITE_LATEX_VALOR = 256


def presentar_resultado_restricciones(resultado: Mapping) -> dict:
    """Convierte la salida exitosa de restricciones en estructuras exactas para la vista."""
    clasificacion = str(resultado.get("clasificacion") or "")
    dimension_ambiente = int(resultado["dimension_ambiente"])
    resumen = _resumen_comun(resultado, clasificacion, dimension_ambiente)
    if clasificacion == "SUBESPACIO":
        return {**resumen, **_detalle_homogeneo(resultado, dimension_ambiente)}
    if clasificacion == "AFIN_NO_SUBESPACIO":
        return {**resumen, **_detalle_afin(resultado, dimension_ambiente)}
    return {**resumen, **_detalle_vacio(resultado, dimension_ambiente)}


def _resumen_comun(
    resultado: Mapping, clasificacion: str, dimension_ambiente: int
) -> dict:
    return {
        "estado": "EXITO",
        "modo": MODO_RESTRICCIONES,
        "codigo": str(resultado.get("codigo", "")),
        "clasificacion": clasificacion,
        "mensaje": limpiar_texto(resultado.get("mensaje")),
        "dimension_ambiente": dimension_ambiente,
        "es_subespacio": bool(resultado.get("es_subespacio")),
        "es_espacio_vectorial": bool(resultado.get("es_subespacio")),
        "contiene_origen": bool(resultado.get("contiene_origen")),
        "es_vacio": bool(resultado.get("es_vacio")),
        "es_subespacio_cero": clasificacion == "SUBESPACIO" and resultado.get("dimension") == 0,
        "rango": int(resultado.get("rango", 0)),
        "rango_aumentada": resultado.get("rango_aumentada"),
        "dimension": resultado.get("dimension"),
        "dimension_afin": resultado.get("dimension_afin"),
        **_traza_comun(resultado),
    }


def _traza_comun(resultado: Mapping) -> dict:
    pivotes = tuple(resultado.get("columnas_pivote", ()))
    libres = tuple(resultado.get("columnas_libres", ()))
    matriz_original = resultado.get("matriz_original")
    return {
        "columnas_pivote": pivotes,
        "columnas_libres": libres,
        "variables_pivote": tuple(f"x{columna + 1}" for columna in pivotes),
        "variables_libres": tuple(f"x{columna + 1}" for columna in libres),
        "cantidad_ecuaciones": matriz_original.filas if matriz_original else 0,
        "matriz_original": serializar_matriz(matriz_original),
        "matriz_reducida": serializar_matriz(resultado.get("matriz_reducida")),
        "pasos": serializar_pasos(resultado.get("pasos", ())),
        "comprobaciones": serializar_comprobaciones(resultado.get("comprobaciones", ())),
        "dependencias": (),
        "etiquetas_generadores": (),
        "etiquetas_generadores_base": (),
    }


def _detalle_homogeneo(resultado: Mapping, dimension_ambiente: int) -> dict:
    dimension = int(resultado.get("dimension") or 0)
    direcciones_raw = tuple(resultado.get("direcciones") or ())
    direcciones_texto = serializar_vectores(direcciones_raw)
    particular_raw = tuple(resultado.get("particular") or (Fraction(0),) * dimension_ambiente)
    subtitulo = (
        f"{VEREDICTO_SUBESPACIO_CERO}: {SUBTITULO_SUBESPACIO_CERO}"
        if dimension == 0
        else f"Núcleo homogéneo de dimensión {dimension} incluido en ℝ{superindice_dimension(dimension_ambiente)}."
    )
    return {
        "veredicto": texto_veredicto_subespacio(dimension_ambiente),
        "subtitulo_veredicto": subtitulo,
        "herencia_axiomas": texto_herencia_axiomas(dimension_ambiente),
        "base": serializar_vectores(resultado.get("base") or ()),
        "direcciones": direcciones_texto,
        "particular": tuple(texto_fraccion_exacta(valor) for valor in particular_raw),
        "testigo": None,
        "familia_parametrica": _familia_parametrica(particular_raw, direcciones_raw, incluir_particular=False),
        "criterios": _criterios_homogeneo(),
        "descripcion_geometrica": descripcion_geometrica_subespacio(dimension, dimension_ambiente),
    }


def _detalle_afin(resultado: Mapping, dimension_ambiente: int) -> dict:
    dimension_afin = int(resultado.get("dimension_afin") or 0)
    particular_raw = tuple(resultado.get("particular") or ())
    direcciones_raw = tuple(resultado.get("direcciones") or ())
    testigo = _serializar_testigo(resultado.get("testigo"))
    return {
        "veredicto": texto_veredicto_no_subespacio(dimension_ambiente),
        "subtitulo_veredicto": (
            f"Conjunto afín de dimensión afín {dimension_afin} en "
            f"ℝ{superindice_dimension(dimension_ambiente)} que no contiene al origen."
        ),
        "herencia_axiomas": "",
        "base": None,
        "direcciones": serializar_vectores(direcciones_raw),
        "particular": tuple(texto_fraccion_exacta(valor) for valor in particular_raw),
        "testigo": testigo,
        "familia_parametrica": _familia_parametrica(particular_raw, direcciones_raw, incluir_particular=True),
        "criterios": _criterios_afin(particular_raw, testigo),
        "descripcion_geometrica": _descripcion_afin(dimension_afin, dimension_ambiente),
    }


def _detalle_vacio(resultado: Mapping, dimension_ambiente: int) -> dict:
    testigo = _serializar_testigo(resultado.get("testigo"))
    return {
        "veredicto": texto_veredicto_no_subespacio(dimension_ambiente),
        "subtitulo_veredicto": f"{VEREDICTO_CONJUNTO_VACIO}: {SUBTITULO_CONJUNTO_VACIO}",
        "herencia_axiomas": "", "base": None, "direcciones": None, "particular": None,
        "testigo": testigo, "familia_parametrica": None, "criterios": _criterios_vacio(testigo),
        "descripcion_geometrica": (
            f"Conjunto vacío en ℝ{superindice_dimension(dimension_ambiente)}: "
            "no contiene al origen ni tiene elementos."
        ),
    }


def _serializar_testigo(testigo: Mapping | None) -> dict | None:
    if not testigo:
        return None
    indice_fila = testigo.get("indice_fila")
    termino = Fraction(testigo.get("termino_independiente", 0))
    return {
        "tipo": str(testigo.get("tipo", "")),
        "indice_fila": indice_fila,
        "fila_visible": (int(indice_fila) + 1) if indice_fila is not None else None,
        "coeficientes": tuple(texto_fraccion_exacta(valor) for valor in testigo.get("coeficientes", ())),
        "termino_independiente": texto_fraccion_exacta(termino),
        "doble_termino": texto_fraccion_exacta(2 * termino),
        "valor_izquierdo": texto_fraccion_exacta(testigo.get("valor_izquierdo", 0)),
        "descripcion": limpiar_texto(testigo.get("descripcion", "")),
    }


def _vector_texto(valores: tuple[Fraction, ...]) -> str:
    return "(" + ", ".join(texto_fraccion_exacta(valor) for valor in valores) + ")"


def _vector_latex(valores: tuple[Fraction, ...]) -> str:
    celdas = r" \\ ".join(fraccion_latex(valor) for valor in valores)
    return rf"\begin{{pmatrix}} {celdas} \end{{pmatrix}}"


def _admite_latex(vectores: tuple[tuple[Fraction, ...], ...]) -> bool:
    return all(
        len(texto_fraccion_exacta(valor)) <= _LIMITE_LATEX_VALOR
        for vector in vectores
        for valor in vector
    )


def _familia_latex(
    particular: tuple[Fraction, ...],
    direcciones: tuple[tuple[Fraction, ...], ...],
    incluir_particular: bool,
) -> str:
    if not direcciones and not incluir_particular:
        return r"\mathbf{x} = \mathbf{0}"
    vectores = (particular, *direcciones) if incluir_particular else direcciones
    if not _admite_latex(vectores):
        terminos = [r"\mathbf{p}"] if incluir_particular else []
        terminos.extend(f"t_{{{indice + 1}}}\\mathbf{{d}}_{{{indice + 1}}}" for indice in range(len(direcciones)))
        return r"\mathbf{x} = " + " + ".join(terminos)
    partes = [_vector_latex(particular)] if incluir_particular else []
    partes.extend(f"t_{{{indice + 1}}} {_vector_latex(vector)}" for indice, vector in enumerate(direcciones))
    return r"\mathbf{x} = " + " + ".join(partes)


def _familia_parametrica(
    particular: tuple[Fraction, ...],
    direcciones: tuple[tuple[Fraction, ...], ...],
    *,
    incluir_particular: bool,
) -> dict[str, str]:
    partes = [_vector_texto(particular)] if incluir_particular else []
    partes.extend(f"t_{indice + 1}·{_vector_texto(vector)}" for indice, vector in enumerate(direcciones))
    texto = "x = " + (" + ".join(partes) if partes else _vector_texto(particular))
    return {"texto": texto, "latex": _familia_latex(particular, direcciones, incluir_particular)}


def _criterio(
    clave: str, titulo: str, estado: str, clase_estado: str, datos: dict[str, str]
) -> dict[str, str]:
    return {
        "clave": clave, "titulo": titulo, "estado": estado,
        "clase_estado": clase_estado, "origen": "teorema", **datos,
    }


def _criterios_homogeneo() -> tuple[dict[str, str], ...]:
    return (
        _criterio("origen", "Contiene al vector cero", ESTADO_CRITERIO_CUMPLE, "exito", {
            "resumen": "Al evaluar x = 0 en todas las ecuaciones homogéneas se cumple A·0 = 0.",
            "formula_latex": r"A\mathbf{0} = \mathbf{0} \implies \mathbf{0} \in W",
        }),
        _criterio("suma", "Cerrado bajo la suma", ESTADO_CRITERIO_CUMPLE, "exito", {
            "resumen": "Si u, v ∈ W cumplen Au = 0 y Av = 0, por linealidad A(u + v) = Au + Av = 0.",
            "formula_latex": r"A(\mathbf{u} + \mathbf{v}) = A\mathbf{u} + A\mathbf{v} = \mathbf{0} \implies \mathbf{u} + \mathbf{v} \in W",
        }),
        _criterio("escalar", "Cerrado bajo el producto por escalar", ESTADO_CRITERIO_CUMPLE, "exito", {
            "resumen": "Si u ∈ W cumple Au = 0 y λ ∈ ℝ, entonces A(λu) = λ(Au) = 0.",
            "formula_latex": r"A(\lambda\mathbf{u}) = \lambda(A\mathbf{u}) = \lambda\mathbf{0} = \mathbf{0} \implies \lambda\mathbf{u} \in W",
        }),
    )


def _comparaciones_afin(testigo: dict | None, b_texto: str, doble_texto: str) -> tuple[str, str]:
    corto = bool(testigo) and len(b_texto) <= _LIMITE_LATEX_VALOR and len(doble_texto) <= _LIMITE_LATEX_VALOR
    if not corto:
        return "", ""
    b_latex = fraccion_latex(Fraction(b_texto))
    doble_latex = fraccion_latex(Fraction(doble_texto))
    return rf"\; (0 \neq {b_latex})", rf"\; ({doble_latex} \neq {b_latex})"


def _criterios_afin(
    particular: tuple[Fraction, ...], testigo: dict | None
) -> tuple[dict[str, str], ...]:
    fila = testigo["fila_visible"] if testigo and testigo["fila_visible"] else 1
    b_texto = testigo["termino_independiente"] if testigo else "b_i"
    doble_texto = testigo["doble_termino"] if testigo else "2b_i"
    p_texto = _vector_texto(particular)
    doble_p_texto = _vector_texto(tuple(2 * valor for valor in particular))
    detalle_origen = testigo["descripcion"] if testigo else "En el origen, Ax = 0 difiere de b."
    comp_origen, comp_doble = _comparaciones_afin(testigo, b_texto, doble_texto)
    return (
        _criterio("origen", "Contiene al vector cero", ESTADO_CRITERIO_NO_CUMPLE, "error", {
            "resumen": f"En x = 0 se obtiene A·0 = 0, pero la ecuación {fila} exige {b_texto} ≠ 0.",
            "formula_latex": rf"A\mathbf{{0}} = \mathbf{{0}} \neq \mathbf{{b}}{comp_origen}",
            "detalle_testigo": detalle_origen,
        }),
        _criterio("suma", "Cerrado bajo la suma", ESTADO_CRITERIO_NO_CUMPLE, "error", {
            "resumen": f"Con p ∈ W (Ap = b), en la ecuación {fila} resulta A(p + p) = {doble_texto} ≠ {b_texto}.",
            "formula_latex": rf"A(\mathbf{{p}} + \mathbf{{p}}) = 2\mathbf{{b}} \neq \mathbf{{b}}{comp_doble}",
            "detalle_testigo": f"Contraejemplo con p = {p_texto}: p + p = {doble_p_texto} no satisface la ecuación {fila}.",
        }),
        _criterio("escalar", "Cerrado bajo el producto por escalar", ESTADO_CRITERIO_NO_CUMPLE, "error", {
            "resumen": f"Con λ = 2 y p ∈ W, en la ecuación {fila} resulta A(2p) = {doble_texto} ≠ {b_texto}.",
            "formula_latex": rf"A(2\mathbf{{p}}) = 2\mathbf{{b}} \neq \mathbf{{b}}{comp_doble}",
            "detalle_testigo": f"Contraejemplo con λ = 2 y p = {p_texto}: 2p = {doble_p_texto} no satisface la ecuación {fila}.",
        }),
    )


def _criterios_vacio(testigo: dict | None) -> tuple[dict[str, str], ...]:
    fila = testigo["fila_visible"] if testigo and testigo["fila_visible"] else 1
    detalle = testigo["descripcion"] if testigo else "El sistema es incompatible."
    return (
        _criterio("origen", "Contiene al vector cero", ESTADO_CRITERIO_NO_CUMPLE, "error", {
            "resumen": f"El sistema es incompatible (contradicción en la fila {fila}): ningún vector satisface Ax = b y 0 ∉ W.",
            "formula_latex": r"W = \varnothing \implies \mathbf{0} \notin W",
            "detalle_testigo": detalle,
        }),
        _criterio("suma", "Cerrado bajo la suma", ESTADO_CRITERIO_VACUO, "vacuo", {
            "resumen": "Se cumple vacuamente porque no existen elementos en W = ∅ para formar un contraejemplo. La ausencia del cero basta para descartar que sea espacio vectorial o subespacio.",
            "formula_latex": r"W = \varnothing \implies \forall \mathbf{u},\mathbf{v} \in W,\; \mathbf{u}+\mathbf{v}\in W",
        }),
        _criterio("escalar", "Cerrado bajo el producto por escalar", ESTADO_CRITERIO_VACUO, "vacuo", {
            "resumen": "Se cumple vacuamente porque no existen vectores en W = ∅ que escalar. La ausencia del cero basta para descartar que sea espacio vectorial o subespacio.",
            "formula_latex": r"W = \varnothing \implies \forall \lambda \in \mathbb{R},\, \mathbf{u} \in W,\; \lambda\mathbf{u}\in W",
        }),
    )


def _descripcion_afin(dimension_afin: int, dimension_ambiente: int) -> str:
    ambiente = f"ℝ{superindice_dimension(dimension_ambiente)}"
    if dimension_ambiente > 3:
        return (
            f"Conjunto afín de dimensión afín {dimension_afin} en {ambiente}; "
            f"no contiene al origen. {NOTA_DIMENSION_SUPERIOR}"
        )
    if dimension_afin == 0:
        return f"Punto afín único de dimensión afín 0 en {ambiente}; no contiene al origen."
    if dimension_afin == 1:
        return f"Recta afín de dimensión afín 1 en {ambiente} que no pasa por el origen."
    return f"Plano afín de dimensión afín 2 en {ambiente} que no pasa por el origen."
