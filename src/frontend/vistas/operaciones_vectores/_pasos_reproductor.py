"""Construcción de pasos y grupos didácticos para operaciones con vectores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from src.backend.modelos.matriz import Matriz
from src.frontend.componentes.reproductor_pasos.cuerpos import CuerpoLatex
from src.frontend.componentes.reproductor_pasos.textos import limpiar_latex_plano
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor


class _CuerpoTexto:
    """Cuerpo ejecutable que renderiza una descripción textual."""

    def __init__(self, texto: str) -> None:
        self.texto = texto

    def __call__(self) -> None:
        ui.label(self.texto).classes("text-sm font-medium text-main text-center")

    def __str__(self) -> str:
        return self.texto


def _clasificar_paso_basico(descripcion: str, latex: str | None) -> tuple[str, str, str, Any]:
    """Clasifica un paso básico según el prefijo de su descripción."""
    if descripcion.startswith("Iniciando"):
        return (
            "inicial", "Inicial",
            "Iniciamos la operación vector a vector comprobando dimensiones y orientaciones.",
            _CuerpoTexto(descripcion),
        )
    if descripcion.startswith("Ajuste de orientación"):
        return (
            "ajuste", "Ajuste",
            "Ajustamos la orientación del vector para que coincida con la del primero.",
            CuerpoLatex(latex) if latex else _CuerpoTexto(descripcion),
        )
    return (
        "componente", "Componente",
        "Calculamos el resultado correspondiente para esta componente celda a celda.",
        CuerpoLatex(latex) if latex else _CuerpoTexto(descripcion),
    )


def construir_pasos_vector_basico(
    respuesta: dict,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye los pasos del reproductor para operaciones básicas de vectores."""
    pasos_crudos = respuesta.get("steps", [])
    if not pasos_crudos:
        return (), ()

    elementos: list[tuple[str, str, str, str, Any]] = []
    for paso in pasos_crudos:
        descripcion = paso.get("description", "")
        tipo, etiqueta, explicacion, cuerpo = _clasificar_paso_basico(descripcion, paso.get("detail_latex"))
        elementos.append((tipo, etiqueta, descripcion, explicacion, cuerpo))

    latex_final = respuesta.get("result_vector_latex") or (
        respuesta.get("latex_details", [""])[-1] if respuesta.get("latex_details") else ""
    )
    if latex_final:
        elementos.append((
            "resultado", "Resultado", "Vector resultante",
            "Vector resultante obtenido tras evaluar todas las componentes.",
            CuerpoLatex(latex_final),
        ))

    total = len(elementos)
    pasos = [
        PasoReproductor(
            indice=indice, tipo=tipo, etiqueta_tipo=etiqueta, descripcion=descripcion, explicacion=explicacion,
            indice_grupo=0, cuerpo=cuerpo,
            meta_explicar={"index": indice + 1, "total": total, "kind": tipo, "op": descripcion, "rows_before": {}, "rows_after": {}, "cols": None},
        )
        for indice, (tipo, etiqueta, descripcion, explicacion, cuerpo) in enumerate(elementos)
    ]
    resumen = f"{total} pasos" if total != 1 else "1 paso"
    grupo = GrupoReproductor(titulo="Operaciones de componentes", resumen=resumen, tipo="operacion", indices_pasos=tuple(range(total)))
    return tuple(pasos), (grupo,)


def _construir_pasos_planteamiento(
    planteamiento: list[dict], total: int, pasos: list[PasoReproductor], indice_grupo: int
) -> list[int]:
    """Construye los pasos del planteamiento algebraico previo."""
    explicaciones = {
        1: "Escribimos la ecuación vectorial con una incógnita escalar multiplicando a cada vector.",
        2: "Multiplicamos cada escalar en las componentes del vector correspondiente.",
        3: "Sumamos los vectores componente a componente en el lado izquierdo.",
        4: "Obtenemos el sistema de ecuaciones lineales equivalente igualando componentes.",
        5: "Construimos la matriz aumentada [A | b] con los vectores como columnas y b a la derecha.",
    }
    indices: list[int] = []
    for paso in planteamiento:
        indice = len(pasos)
        indices.append(indice)
        numero = paso.get("step_number", len(indices))
        descripcion = paso.get("description", f"Planteamiento {numero}")
        metadatos = {"index": indice + 1, "total": total, "kind": "planteamiento", "op": descripcion, "rows_before": {}, "rows_after": {}, "cols": None}
        pasos.append(PasoReproductor(
            indice=indice, tipo="planteamiento", etiqueta_tipo="Planteamiento",
            descripcion=descripcion, explicacion=explicaciones.get(numero, descripcion),
            indice_grupo=indice_grupo, cuerpo=CuerpoLatex(paso.get("detail_latex", "")), meta_explicar=metadatos,
        ))
    return indices


@dataclass
class _ConstruccionPasos:
    """Agrupa los datos y colecciones compartidos por las fases de un procedimiento."""

    total: int
    variables: list[str]
    numero_variables: int
    pasos: list[PasoReproductor]
    grupos: list[GrupoReproductor]


def _construir_pasos_gauss(pasos_vista: list[dict], metadatos: list[dict], construccion: _ConstruccionPasos) -> list[int]:
    """Construye los pasos interactivos de eliminación gaussiana sobre la matriz aumentada."""
    indices: list[int] = []
    for paso in pasos_vista:
        indice = len(construccion.pasos)
        indices.append(indice)
        tipo, descripcion, explicacion = paso.get("kind", "eliminacion"), paso.get("description", ""), paso.get("explanation", "")
        datos_matriz = paso.get("matrix", {})
        matriz = Matriz(datos_matriz["rows"], datos_matriz["cols"], datos_matriz["data"]) if isinstance(datos_matriz, dict) and "rows" in datos_matriz else datos_matriz
        cuerpo = html_tabla_aumentada(
            matriz, construccion.numero_variables, filas_cambiadas=tuple(paso.get("rows_changed") or ()),
            pivote=tuple(paso["pivot"]) if paso.get("pivot") is not None else None,
            filas_intercambio=tuple(paso["swap_rows"]) if paso.get("swap_rows") is not None else (),
            bloque_resultado=False, etiquetas_izq=construccion.variables, etiquetas_der=["b"],
        )
        indice_original = paso.get("index", len(indices) - 1)
        referencia = dict(metadatos[indice_original]) if indice_original < len(metadatos) else {
            "index": indice + 1, "total": construccion.total, "kind": tipo, "op": descripcion,
            "pivot": paso.get("pivot"), "rows_before": {}, "rows_after": {}, "cols": None,
        }
        referencia.update({"total": construccion.total, "index": indice + 1})
        construccion.pasos.append(PasoReproductor(
            indice=indice, tipo=tipo, etiqueta_tipo=tipo.capitalize(), descripcion=descripcion,
            explicacion=explicacion or descripcion, indice_grupo=len(construccion.grupos),
            cuerpo=cuerpo, meta_explicar=referencia,
        ))
    return indices


def _construir_pasos_sustitucion(
    sustitucion: list[str], total: int, pasos: list[PasoReproductor], indice_grupo: int
) -> list[int]:
    """Construye los pasos de sustitución hacia atrás."""
    indices: list[int] = []
    for linea in sustitucion:
        indice = len(pasos)
        indices.append(indice)
        operacion = limpiar_latex_plano(linea)
        metadatos = {"index": indice + 1, "total": total, "kind": "sustitucion", "op": operacion, "rows_before": {}, "rows_after": {}, "cols": None}
        pasos.append(PasoReproductor(
            indice=indice, tipo="sustitucion", etiqueta_tipo="Sustitución",
            descripcion=operacion, explicacion="Despejamos y sustituimos hacia atrás los valores conocidos.",
            indice_grupo=indice_grupo, cuerpo=CuerpoLatex(linea), meta_explicar=metadatos,
        ))
    return indices


def _construir_pasos_verificacion(
    verificacion: dict, total: int, pasos: list[PasoReproductor], indice_grupo: int
) -> list[int]:
    """Construye los 4 pasos formales de comprobación."""
    indices: list[int] = []
    bloques = (
        (verificacion.get("formula_latex", ""), "Definición simbólica del vector", "Planteamos la combinación lineal simbólica del vector y."),
        (verificacion.get("substitution_latex", ""), "Sustitución de escalares y vectores", "Sustituimos los coeficientes y vectores en la combinación."),
        (verificacion.get("evaluated_vector_latex", ""), "Evaluación numérica del vector", "Evaluamos numéricamente el vector resultante de la combinación."),
        (verificacion.get("comparison_latex", ""), "Comparación con el vector objetivo b", "Comprobamos si el vector evaluado coincide con el vector b."),
    )
    for latex, descripcion, explicacion in bloques:
        indice = len(pasos)
        indices.append(indice)
        metadatos = {"index": indice + 1, "total": total, "kind": "verificacion", "op": descripcion, "rows_before": {}, "rows_after": {}, "cols": None}
        pasos.append(PasoReproductor(
            indice=indice, tipo="verificacion", etiqueta_tipo="Verificación",
            descripcion=descripcion, explicacion=explicacion,
            indice_grupo=indice_grupo, cuerpo=CuerpoLatex(latex), meta_explicar=metadatos,
        ))
    return indices


def _agregar_fase_planteamiento_gauss(respuesta: dict, construccion: _ConstruccionPasos) -> None:
    """Incorpora fases de planteamiento algebraico y eliminación gaussiana."""
    planteamiento = respuesta.get("setup_steps") or []
    if planteamiento:
        indices_planteamiento = _construir_pasos_planteamiento(planteamiento, construccion.total, construccion.pasos, len(construccion.grupos))
        resumen_planteamiento = "1 operación" if len(indices_planteamiento) == 1 else f"{len(indices_planteamiento)} operaciones"
        construccion.grupos.append(GrupoReproductor(
            titulo="Planteamiento algebraico", resumen=resumen_planteamiento,
            tipo="planteamiento", indices_pasos=tuple(indices_planteamiento),
        ))

    pasos_vista = respuesta.get("steps_view") or []
    if pasos_vista:
        metadatos = respuesta.get("steps_meta") or []
        indices_gauss = _construir_pasos_gauss(pasos_vista, metadatos, construccion)
        resumen_gauss = "1 operación" if len(indices_gauss) == 1 else f"{len(indices_gauss)} operaciones"
        construccion.grupos.append(GrupoReproductor(
            titulo="Eliminación gaussiana", resumen=resumen_gauss,
            tipo="eliminacion", indices_pasos=tuple(indices_gauss),
        ))


def _agregar_fase_sustitucion_verificacion(
    respuesta: dict, total: int, pasos: list[PasoReproductor], grupos: list[GrupoReproductor],
) -> None:
    """Incorpora fases de sustitución hacia atrás y comprobación."""
    sustitucion = respuesta.get("back_substitution_steps") or []
    if sustitucion:
        indices_sustitucion = _construir_pasos_sustitucion(sustitucion, total, pasos, len(grupos))
        resumen_sustitucion = "1 operación" if len(indices_sustitucion) == 1 else f"{len(indices_sustitucion)} operaciones"
        grupos.append(GrupoReproductor(
            titulo="Sustitución hacia atrás", resumen=resumen_sustitucion,
            tipo="sustitucion", indices_pasos=tuple(indices_sustitucion),
        ))

    verificacion = respuesta.get("verification_step")
    if verificacion:
        indices_verificacion = _construir_pasos_verificacion(verificacion, total, pasos, len(grupos))
        grupos.append(GrupoReproductor(
            titulo="Comprobación", resumen="4 operaciones",
            tipo="verificacion", indices_pasos=tuple(indices_verificacion),
        ))


def construir_pasos_combinacion_lineal(
    respuesta: dict,
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Construye las tuplas de pasos y grupos para el reproductor de combinación lineal."""
    if respuesta.get("status") == "ERROR":
        return (), ()

    planteamiento = respuesta.get("setup_steps") or []
    pasos_vista = respuesta.get("steps_view") or []
    sustitucion = respuesta.get("back_substitution_steps") or []
    verificacion = respuesta.get("verification_step")
    variables = respuesta.get("variables") or []
    numero_variables = respuesta.get("n_vars", len(variables))

    cantidad_verificaciones = 4 if verificacion else 0
    total = len(planteamiento) + len(pasos_vista) + len(sustitucion) + cantidad_verificaciones
    if total == 0:
        return (), ()

    pasos: list[PasoReproductor] = []
    grupos: list[GrupoReproductor] = []
    _agregar_fase_planteamiento_gauss(respuesta, _ConstruccionPasos(total, variables, numero_variables, pasos, grupos))
    _agregar_fase_sustitucion_verificacion(respuesta, total, pasos, grupos)

    return tuple(pasos), tuple(grupos)
