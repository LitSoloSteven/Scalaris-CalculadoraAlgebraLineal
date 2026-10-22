"""Construcción de pasos y grupos didácticos para operaciones con vectores."""

from __future__ import annotations
from src.frontend.componentes.presentacion_analisis import adaptar_analisis

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from src.frontend.componentes.reproductor_pasos.cuerpos import CuerpoLatex
from src.frontend.componentes.reproductor_pasos.textos import limpiar_latex_plano
from src.frontend.controladores.operaciones_vectores.presentacion_pasos import construir_tabla_paso_vectorial
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor


class _CuerpoTexto:
    """Cuerpo ejecutable que renderiza una descripción textual."""

    def __init__(self, texto: str) -> None:
        self.texto = texto

    def __call__(self) -> None:
        ui.label(self.texto).classes("text-sm font-medium texto-principal text-center")

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
    pasos_crudos = respuesta.get("pasos", [])
    if not pasos_crudos:
        return (), ()

    elementos: list[tuple[str, str, str, str, Any]] = []
    for paso in pasos_crudos:
        descripcion = paso.get("descripcion", "")
        tipo, etiqueta, explicacion, cuerpo = _clasificar_paso_basico(descripcion, paso.get("detalle_latex"))
        elementos.append((tipo, etiqueta, descripcion, explicacion, cuerpo))

    latex_final = respuesta.get("vector_resultado_latex") or (
        respuesta.get("detalles_latex", [""])[-1] if respuesta.get("detalles_latex") else ""
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
            meta_explicar={"indice": indice + 1, "total": total, "tipo": tipo, "operacion": descripcion, "filas_antes": {}, "filas_despues": {}, "columnas": None},
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
        numero = paso.get("numero_paso", len(indices))
        descripcion = paso.get("descripcion", f"Planteamiento {numero}")
        metadatos = {"indice": indice + 1, "total": total, "tipo": "planteamiento", "operacion": descripcion, "filas_antes": {}, "filas_despues": {}, "columnas": None}
        pasos.append(PasoReproductor(
            indice=indice, tipo="planteamiento", etiqueta_tipo="Planteamiento",
            descripcion=descripcion, explicacion=explicaciones.get(numero, descripcion),
            indice_grupo=indice_grupo, cuerpo=CuerpoLatex(paso.get("detalle_latex", "")), meta_explicar=metadatos,
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
        tipo, descripcion, explicacion = paso.get("tipo", "eliminacion"), paso.get("descripcion", ""), paso.get("explicacion", "")
        cuerpo = construir_tabla_paso_vectorial(paso, construccion.numero_variables, construccion.variables)
        indice_original = paso.get("indice", len(indices) - 1)
        referencia = dict(metadatos[indice_original]) if indice_original < len(metadatos) else {
            "indice": indice + 1, "total": construccion.total, "tipo": tipo, "operacion": descripcion,
            "pivote": paso.get("pivote"), "filas_antes": {}, "filas_despues": {}, "columnas": None,
        }
        referencia.update({"total": construccion.total, "indice": indice + 1})
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
        metadatos = {"indice": indice + 1, "total": total, "tipo": "sustitucion", "operacion": operacion, "filas_antes": {}, "filas_despues": {}, "columnas": None}
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
        (verificacion.get("sustitucion_latex", ""), "Sustitución de escalares y vectores", "Sustituimos los coeficientes y vectores en la combinación."),
        (verificacion.get("vector_evaluado_latex", ""), "Evaluación numérica del vector", "Evaluamos numéricamente el vector resultante de la combinación."),
        (verificacion.get("comparacion_latex", ""), "Comparación con el vector objetivo b", "Comprobamos si el vector evaluado coincide con el vector b."),
    )
    for latex, descripcion, explicacion in bloques:
        indice = len(pasos)
        indices.append(indice)
        metadatos = {"indice": indice + 1, "total": total, "tipo": "verificacion", "operacion": descripcion, "filas_antes": {}, "filas_despues": {}, "columnas": None}
        pasos.append(PasoReproductor(
            indice=indice, tipo="verificacion", etiqueta_tipo="Verificación",
            descripcion=descripcion, explicacion=explicacion,
            indice_grupo=indice_grupo, cuerpo=CuerpoLatex(latex), meta_explicar=metadatos,
        ))
    return indices


def _agregar_fase_planteamiento_gauss(respuesta: dict, construccion: _ConstruccionPasos) -> None:
    """Incorpora fases de planteamiento algebraico y eliminación gaussiana."""
    planteamiento = respuesta.get("pasos_planteamiento") or []
    if planteamiento:
        indices_planteamiento = _construir_pasos_planteamiento(planteamiento, construccion.total, construccion.pasos, len(construccion.grupos))
        resumen_planteamiento = "1 operación" if len(indices_planteamiento) == 1 else f"{len(indices_planteamiento)} operaciones"
        construccion.grupos.append(GrupoReproductor(
            titulo="Planteamiento algebraico", resumen=resumen_planteamiento,
            tipo="planteamiento", indices_pasos=tuple(indices_planteamiento),
        ))

    pasos_vista = respuesta.get("vista_pasos") or []
    if pasos_vista:
        metadatos = respuesta.get("metadatos_pasos") or []
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
    sustitucion = respuesta.get("pasos_sustitucion_regresiva") or []
    if sustitucion:
        indices_sustitucion = _construir_pasos_sustitucion(sustitucion, total, pasos, len(grupos))
        resumen_sustitucion = "1 operación" if len(indices_sustitucion) == 1 else f"{len(indices_sustitucion)} operaciones"
        grupos.append(GrupoReproductor(
            titulo="Sustitución hacia atrás", resumen=resumen_sustitucion,
            tipo="sustitucion", indices_pasos=tuple(indices_sustitucion),
        ))

    verificacion = respuesta.get("paso_verificacion")
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
    if respuesta.get("estado") == "ERROR":
        return (), ()

    planteamiento = respuesta.get("pasos_planteamiento") or []
    pasos_vista = respuesta.get("vista_pasos") or []
    sustitucion = respuesta.get("pasos_sustitucion_regresiva") or []
    verificacion = respuesta.get("paso_verificacion")
    variables = respuesta.get("variables") or []
    numero_variables = respuesta.get("numero_variables", len(variables))

    cantidad_verificaciones = (4 if verificacion else 0) + len(_traza_comprobacion(respuesta))
    total = len(planteamiento) + len(pasos_vista) + len(sustitucion) + cantidad_verificaciones
    if total == 0:
        return (), ()

    pasos: list[PasoReproductor] = []
    grupos: list[GrupoReproductor] = []
    _agregar_fase_planteamiento_gauss(respuesta, _ConstruccionPasos(total, variables, numero_variables, pasos, grupos))
    _agregar_fase_sustitucion_verificacion(respuesta, total, pasos, grupos)
    _anexar_comprobacion(respuesta, pasos, grupos)
    return tuple(pasos), tuple(grupos)


def _anexar_comprobacion(respuesta: dict, pasos: list, grupos: list) -> None:
    traza = _traza_comprobacion(respuesta)
    if not traza:
        return
    anterior = grupos.pop() if grupos[-1].tipo == "verificacion" else None
    adicionales, _ = adaptar_analisis({"traza": traza}, (len(pasos), len(grupos)))
    indices = (anterior.indices_pasos if anterior else ()) + tuple(paso.indice for paso in adicionales)
    pasos.extend(adicionales)
    grupos.append(GrupoReproductor("Comprobación", f"{len(indices)} operaciones", "verificacion", indices))


def _traza_comprobacion(respuesta: dict) -> list:
    verificacion = respuesta.get("paso_verificacion") or {}
    return respuesta.get("traza_comprobacion") or verificacion.get("traza", [])
