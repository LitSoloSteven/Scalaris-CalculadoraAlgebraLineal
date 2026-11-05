"""Composición del resultado, tabla y procedimiento de bisección."""
from nicegui import ui

from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.controladores.biseccion.presentacion import COLUMNAS, filas_tabla, construir_pasos, valor_columna
from src.frontend.controladores.biseccion.salidas_biseccion import COLUMNAS_EXAMEN, datos_examen
from .figura import crear_figura
from .captura import GUIA_CONTINUIDAD
from .modo_examen import crear_interruptor_examen, mostrar_accion_examen
from .resumen_criterio import mostrar_resumen


def mostrar_resultado(vista, respuesta: dict) -> None:
    """Presenta los datos vigentes sin convertir un estado parcial en éxito."""
    with vista.contenedor_resultados:
        hay_filas = bool(respuesta.get("iteraciones"))
        examen = crear_interruptor_examen(vista) if hay_filas else None
        mostrar_resumen(vista, respuesta, examen)
        if "muestra" in respuesta:
            _mostrar_exploracion(vista, respuesta, examen)
        elif hay_filas:
            _reproductor(vista, respuesta, examen)
        if hay_filas:
            mostrar_tabla(respuesta, examen)


def _mostrar_exploracion(vista, respuesta: dict, examen: ui.switch | None) -> None:
    with ui.element("div").classes("biseccion-exploracion w-full"):
        with ui.column().classes("panel-tarjeta p-5 w-full min-w-0"):
            ui.label("El intervalo en la función").classes("text-lg font-bold")
            vista.grafica = ui.plotly(crear_figura(respuesta, respuesta["muestra"])).classes("w-full biseccion-grafica")
            vista.grafica.on("plotly_afterplot", js_handler="() => window.scalaris.sincronizarTemaPlotly()")
            ui.label("El muestreo puede omitir singularidades. Los huecos detectados se dejan sin unir.").classes("text-sm texto-secundario")
            ui.label(GUIA_CONTINUIDAD).classes("text-sm texto-secundario")
        with ui.column().classes("w-full min-w-0"):
            _reproductor(vista, respuesta, examen)


def _reproductor(vista, respuesta: dict, examen: ui.switch | None) -> None:
    pasos, grupos = construir_pasos(respuesta)

    def renderizar_cuerpo(paso, contenedor) -> None:
        """Actualiza la figura del paso y muestra sus magnitudes internas en texto."""
        if "muestra" in respuesta and not vista.grafica.is_deleted:
            vista.grafica.update_figure(crear_figura(respuesta, respuesta["muestra"], paso.cuerpo, paso.tipo == "planteamiento"))
        if not paso.cuerpo:
            return
        with contenedor:
            for clave, etiqueta in COLUMNAS:
                ui.label(f"{etiqueta}: {valor_columna(paso.cuerpo, clave, True)}").classes("biseccion-numero text-sm")
            if examen is not None:
                mostrar_accion_examen(examen, paso.cuerpo, respuesta["estado"])

    vista.reproductor_pasos = ReproductorPasos(pasos, grupos, renderizar_cuerpo, "biseccion", {
        "titulo": "Procedimiento paso a paso", "al_explicar": crear_accion_explicacion(vista.panel_ia, pasos),
        "esta_ocupado": lambda: bool(getattr(vista.panel_ia, "_esta_enviando", False)),
        "lineas_ayuda": (_ayuda_reproductor(respuesta),),
    })
    vista.reproductor_pasos.construir()


def _ayuda_reproductor(respuesta: dict) -> str:
    controles = "Usa las flechas, el índice o la reproducción automática."
    if "muestra" in respuesta:
        return "Al cambiar de paso se actualiza el intervalo dibujado. " + controles
    return "El procedimiento conserva las filas válidas anteriores al fallo. " + controles


def mostrar_tabla(respuesta: dict, examen: ui.switch | None = None) -> None:
    """Monta la traza de una sola respuesta con formato e inspección de valores internos."""
    with ui.column().classes("panel-tarjeta p-5 w-full min-w-0"):
        ui.label("Tabla de iteraciones").classes("text-xl font-bold")
        ui.label("Ancho: b−a. Cota: (b−a)/2 en x, si f es continua. Residuo: |f(c)|. Error relativo: |(cᵢ−cᵢ₋₁)/cᵢ|·100%; no aplica en la primera fila o si cᵢ=0.").classes("text-sm texto-secundario")
        precision = ui.switch("Inspeccionar valores internos (hasta 17 cifras)")
        with ui.element("div").classes("biseccion-tabla w-full").props('tabindex=0 role=region aria-label="Tabla de iteraciones con desplazamiento horizontal"'):
            tabla = ui.table(columns=[], rows=[], row_key="i", pagination=15).classes("w-full")
            tabla.props('rows-per-page-label="Filas por página" :pagination-label="(inicio, fin, total) => inicio + \'-\' + fin + \' de \' + total"')
    def _actualizar() -> None:
        _actualizar_tabla(tabla, respuesta, precision.value, examen is not None and examen.value)

    _actualizar()
    precision.on_value_change(_actualizar)
    if examen is not None:
        examen.on_value_change(_actualizar)


def _actualizar_tabla(tabla: ui.table, respuesta: dict, precision: bool, examen: bool) -> None:
    if tabla.is_deleted:
        return
    columnas = COLUMNAS + COLUMNAS_EXAMEN if examen else COLUMNAS
    tabla.columns = [{"name": clave, "label": etiqueta, "field": clave, "align": "left"}
                     for clave, etiqueta in columnas]
    filas = filas_tabla(respuesta, precision)
    if examen:
        for fila, original in zip(filas, respuesta["iteraciones"]):
            fila.update(datos_examen(original, respuesta["estado"]))
    tabla.update_rows(filas)
