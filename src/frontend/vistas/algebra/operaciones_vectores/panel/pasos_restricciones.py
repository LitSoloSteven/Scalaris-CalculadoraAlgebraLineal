"""Adaptadores de pasos, tablas aumentadas y verificaciones para restricciones."""
from __future__ import annotations

import html

from nicegui import ui

from src.frontend.componentes.reproductor_pasos.formato.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.formato.html_tablas import html_tabla_aumentada
from src.frontend.componentes.reproductor_pasos.nucleo.modelo import GrupoReproductor, PasoReproductor
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    SUBTITULO_CONJUNTO_VACIO,
    SUBTITULO_SUBESPACIO_CERO,
    VEREDICTO_CONJUNTO_VACIO,
    VEREDICTO_SUBESPACIO_CERO,
)


def tabla_reduccion_subespacio(
    matriz: dict | None, adaptador_cls, columnas_izquierda: int | None,
    etiquetas: tuple[tuple[str, ...], tuple[str, ...]], datos_evento: tuple[str, dict],
) -> str:
    """Renderiza una matriz aumentada o de generadores aplicando los resaltados del paso."""
    if not matriz:
        return ""
    adaptador = adaptador_cls(matriz)
    tipo, datos = datos_evento
    izquierda = adaptador.columnas if columnas_izquierda is None else columnas_izquierda
    pivote = (datos["fila"], datos["columna"]) if tipo == "pivote" and "fila" in datos and "columna" in datos else None
    intercambio = (datos["fila"], datos["seleccionada"]) if tipo == "intercambio" and "fila" in datos else ()
    cambiadas = (datos["fila"],) if tipo in ("eliminacion", "normalizacion") and "fila" in datos else ()
    return html_tabla_aumentada(adaptador, izquierda, {
        "etiquetas_izquierda": etiquetas[0], "etiquetas_derecha": etiquetas[1],
        "pivote": pivote, "filas_intercambio": intercambio, "filas_cambiadas": cambiadas,
    })


def tabla_reduccion_restricciones(
    matriz: dict | None, adaptador_cls, dimension_ambiente: int, tipo: str, datos: dict
) -> str:
    """Renderiza una instantánea de [A | b] con etiquetas x1..xn y b."""
    etiquetas_x = tuple(f"x{indice + 1}" for indice in range(dimension_ambiente))
    return tabla_reduccion_subespacio(
        matriz, adaptador_cls, dimension_ambiente, (etiquetas_x, ("b",)), (tipo, datos)
    )


def describir_evento_restricciones(tipo: str, datos: dict, describir_base) -> tuple[str, str]:
    """Devuelve título y explicación de un paso elemental sobre [A | b]."""
    if tipo == "inicial":
        return "Matriz aumentada [A | b]", "Cada fila representa una ecuación lineal de restricción en el sistema Ax = b."
    return describir_base(tipo, datos)


def _metadatos_grupo_solucion(resultado: dict) -> tuple[str, str, str]:
    clasificacion = resultado.get("clasificacion")
    if clasificacion == "SUBESPACIO":
        if resultado.get("es_subespacio_cero"):
            return (
                "Solución trivial única del sistema homogéneo",
                "La reducción muestra rango completo y el núcleo es el subespacio cero {0}.",
                "Lectura del núcleo homogéneo",
            )
        return (
            "Lectura de la base del núcleo y familia paramétrica",
            "Las variables libres parametrizan la solución homogénea y forman la base de W.",
            "Lectura del núcleo homogéneo",
        )
    if clasificacion == "AFIN_NO_SUBESPACIO":
        return (
            "Testigo del origen y familia afín p + ker(A)",
            "El sistema es compatible con b distinto de cero; se muestran p, direcciones y testigo en el origen.",
            "Lectura de la solución afín y testigo",
        )
    return (
        "Incompatibilidad y testigo de fila contradictoria",
        "El rango aumentado supera al rango de A y la fila contradictoria demuestra que el conjunto es vacío.",
        "Lectura de incompatibilidad y testigo",
    )


def agregar_grupo_solucion_restricciones(
    resultado: dict, pasos: list[PasoReproductor], grupos: list[GrupoReproductor]
) -> None:
    """Añade el paso de lectura de solución o testigo al reproductor de restricciones."""
    indice = len(pasos)
    indice_grupo = len(grupos)
    descripcion, explicacion, titulo_grupo = _metadatos_grupo_solucion(resultado)
    pasos.append(PasoReproductor(
        indice=indice, tipo="final", etiqueta_tipo="Solución",
        descripcion=descripcion, explicacion=explicacion,
        indice_grupo=indice_grupo, cuerpo=("solucion_restricciones", resultado),
        meta_explicar={"indice": indice + 1, "tipo": "final", "operacion": descripcion, "origen": "solucion_restricciones"},
    ))
    grupos.append(GrupoReproductor(
        titulo=titulo_grupo, resumen="1 paso", tipo="final", indices_pasos=(indice,),
    ))


def renderizar_cuerpo_solucion_restricciones(resultado: dict, adaptador_cls) -> None:
    """Renderiza la forma reducida de [A | b] y la interpretación exacta del conjunto."""
    dimension = int(resultado.get("dimension_ambiente") or 1)
    matriz_reducida = resultado.get("matriz_reducida")
    if matriz_reducida:
        adaptador = adaptador_cls(matriz_reducida)
        etiquetas_x = tuple(f"x{indice + 1}" for indice in range(dimension))
        ui.label("Forma escalonada reducida de [A | b]").classes("text-sm font-semibold texto-principal")
        ui.html(html_tabla_aumentada(adaptador, dimension, {
            "etiquetas_izquierda": etiquetas_x, "etiquetas_derecha": ("b",), "bloque_resultado": True,
        })).classes("w-full")
    clasificacion = resultado.get("clasificacion")
    if clasificacion == "VACIO_NO_SUBESPACIO":
        _cuerpo_vacio(resultado)
        return
    _mostrar_variables(resultado)
    if clasificacion == "SUBESPACIO":
        _cuerpo_homogeneo(resultado)
    else:
        _cuerpo_afin(resultado)


def _mostrar_variables(resultado: dict) -> None:
    pivotes = ", ".join(resultado.get("variables_pivote") or ()) or "ninguna"
    libres = ", ".join(resultado.get("variables_libres") or ()) or "ninguna"
    ui.label(f"Variables pivote: {pivotes} · Variables libres: {libres}").classes(
        "subespacios-numero texto-secundario text-sm"
    )


def _mostrar_familia(resultado: dict) -> None:
    familia = resultado.get("familia_parametrica")
    if not familia:
        return
    ui.label("Familia paramétrica de soluciones").classes("text-sm font-semibold texto-principal")
    if familia.get("latex"):
        renderizar_latex(familia["latex"], vigilar_region=True)
    ui.label(familia["texto"]).classes("subespacios-numero texto-secundario text-sm select-text")


def _cuerpo_homogeneo(resultado: dict) -> None:
    if resultado.get("es_subespacio_cero"):
        ui.label(f"{VEREDICTO_SUBESPACIO_CERO}: {SUBTITULO_SUBESPACIO_CERO}").classes("texto-principal text-sm")
        return
    for indice, vector in enumerate(resultado.get("base") or (), 1):
        ui.label(f"d_{indice} = ({', '.join(vector)})").classes("subespacios-numero texto-principal text-sm select-text")
    _mostrar_familia(resultado)


def _cuerpo_afin(resultado: dict) -> None:
    testigo = resultado.get("testigo") or {}
    if testigo.get("descripcion"):
        ui.label(f"Testigo del origen: {testigo['descripcion']}").classes("subespacios-numero texto-principal text-sm")
    particular = resultado.get("particular") or ()
    ui.label(f"Punto particular: p = ({', '.join(particular)})").classes(
        "subespacios-numero texto-principal text-sm font-semibold select-text"
    )
    for indice, vector in enumerate(resultado.get("direcciones") or (), 1):
        ui.label(f"Dirección d_{indice} = ({', '.join(vector)})").classes("subespacios-numero texto-secundario text-sm select-text")
    _mostrar_familia(resultado)


def _cuerpo_vacio(resultado: dict) -> None:
    rango_a = resultado.get("rango")
    rango_ab = resultado.get("rango_aumentada")
    ui.label(f"{VEREDICTO_CONJUNTO_VACIO}: {SUBTITULO_CONJUNTO_VACIO}").classes("texto-principal text-sm font-semibold")
    if rango_ab is not None:
        ui.label(f"Rango(A) = {rango_a} y rango([A | b]) = {rango_ab}.").classes("subespacios-numero texto-secundario text-sm")
    testigo = resultado.get("testigo") or {}
    if testigo.get("descripcion"):
        ui.label(f"Testigo: {testigo['descripcion']}").classes("subespacios-numero texto-principal text-sm select-text")


def renderizar_verificacion_motor(elemento: dict) -> None:
    """Renderiza una verificación del motor ya sea textual o en bloque LaTeX."""
    if elemento.get("detalle_latex"):
        fila = elemento.get("fila")
        if fila is not None:
            ui.label(f"Ecuación {fila} verificada exactamente:").classes("texto-secundario text-xs font-semibold")
        renderizar_latex(elemento["detalle_latex"], vigilar_region=True)
        return
    estado = "Cumple" if elemento.get("coincide") else "Error"
    detalle = html.unescape(str(elemento.get("detalle") or ""))
    ui.label(f"{estado}: {detalle}").classes("subespacios-numero texto-principal text-sm")
