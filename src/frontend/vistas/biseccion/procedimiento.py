"""Procedimiento y tabla de una traza de bisección, con gráfico sincronizado."""
from nicegui import ui

from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.controladores.biseccion.catalogo_criterios import condicion_criterio
from src.frontend.controladores.biseccion.formato_expresion import formatear_expresion
from src.frontend.controladores.biseccion.formulas_procedimiento import formulas_iteracion
from src.frontend.controladores.biseccion.presentacion import COLUMNAS, construir_pasos, valor_columna
from .modo_examen import mostrar_accion_examen
from .tabla_iteraciones import mostrar_tabla


def mostrar_traza(respuesta: dict, examen, al_mostrar_paso, identificador: str, preferencias=None) -> ReproductorPasos:
    """Monta las pestañas y enlaza el paso activo a la figura del origen que lo abrió."""
    reproductor = _crear_reproductor(respuesta, examen, al_mostrar_paso, identificador, preferencias or {})
    with ui.tabs().classes("w-full") as pestanas:
        procedimiento = ui.tab("Procedimiento")
        tabla = ui.tab("Tabla")
    with ui.tab_panels(pestanas, value=procedimiento).classes("w-full").props(remove="animated"):
        with ui.tab_panel(procedimiento).props("tabindex=0"):
            reproductor.construir()
        with ui.tab_panel(tabla).props("tabindex=0"):
            mostrar_tabla(respuesta, examen)
    pestanas.on_value_change(reproductor.pausar)
    return reproductor


def _crear_reproductor(respuesta: dict, examen, al_mostrar_paso, identificador: str, preferencias: dict):
    pasos, grupos = construir_pasos(respuesta)

    def _renderizar_cuerpo(paso, contenedor) -> None:
        al_mostrar_paso(paso)
        with contenedor:
            if paso.cuerpo:
                _mostrar_iteracion(paso.cuerpo, examen, respuesta["estado"])
            else:
                _mostrar_paso_sin_fila(paso.tipo, respuesta)

    opciones = {
        "lineas_ayuda": ("Usa las flechas, el índice o la reproducción automática para recorrer el intervalo.",),
        "sin_movimiento": True,
    }
    panel_ia = preferencias.get("panel_ia")
    if panel_ia is not None:
        opciones["al_explicar"] = crear_accion_explicacion(panel_ia, pasos)
        opciones["esta_ocupado"] = lambda: bool(getattr(panel_ia, "_esta_enviando", False))
    reproductor = ReproductorPasos(pasos, grupos, _renderizar_cuerpo, identificador, opciones)
    reproductor.velocidad = preferencias.get("velocidad") or reproductor.velocidad
    return reproductor


def _mostrar_iteracion(fila: dict, examen, estado: str) -> None:
    renderizar_latex(r"\begin{gathered}" + r"\\".join(formulas_iteracion(fila)) + r"\end{gathered}",
                     vigilar_region=True)
    for clave, etiqueta in COLUMNAS:
        ui.label(f"{etiqueta}: {valor_columna(fila, clave, True)}").classes("biseccion-numero text-sm")
    if examen is not None:
        mostrar_accion_examen(examen, fila, estado)


def _mostrar_paso_sin_fila(tipo: str, respuesta: dict) -> None:
    if tipo == "planteamiento":
        formula = formatear_expresion(respuesta["entrada"]["expresion"])
        renderizar_latex(formula["latex"], vigilar_region=True)
        return
    criterio = respuesta.get("criterio_solicitado")
    if criterio and respuesta.get("metrica_final") is not None:
        ui.label(condicion_criterio(criterio["tipo"], criterio["parametro"])).classes("text-sm texto-secundario")
