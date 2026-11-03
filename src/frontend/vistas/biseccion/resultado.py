"""Composición del resultado, tabla y procedimiento de bisección."""
from nicegui import ui

from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.controladores.biseccion.presentacion import COLUMNAS, numero, motivo, filas_tabla, construir_pasos
from .figura import crear_figura
from .captura import GUIA_CONTINUIDAD


def mostrar_resultado(vista, respuesta: dict) -> None:
    """Presenta los datos vigentes sin convertir un estado parcial en éxito."""
    with vista.contenedor_resultados:
        _resumen(respuesta)
        if "muestra" not in respuesta:
            return
        with ui.element("div").classes("biseccion-exploracion w-full"):
            with ui.column().classes("panel-tarjeta p-5 w-full min-w-0"):
                ui.label("El intervalo en la función").classes("text-lg font-bold")
                vista.grafica = ui.plotly(crear_figura(respuesta, respuesta["muestra"])).classes("w-full biseccion-grafica")
                ui.label("El muestreo puede omitir singularidades. Los huecos detectados se dejan sin unir.").classes("text-sm texto-secundario")
                ui.label(GUIA_CONTINUIDAD).classes("text-sm texto-secundario")
            with ui.column().classes("w-full min-w-0"):
                _reproductor(vista, respuesta)
        if respuesta["iteraciones"]:
            _tabla(respuesta)


def _resumen(respuesta: dict) -> None:
    with ui.column().classes("panel-tarjeta p-6 w-full gap-3"):
        if respuesta.get("aproximacion") is None:
            ui.label(respuesta["mensaje"]).classes("texto-advertencia").props('role="alert"')
            return
        decimales = respuesta["entrada"]["decimales"]
        etiqueta = "Aproximación de la raíz" if respuesta["estado"] == "EXITO" else "Aproximación provisional"
        ui.label(etiqueta).classes("texto-secundario")
        texto_aproximacion = f"{respuesta['aproximacion']:.{decimales}f}"
        ui.label(f"x ≈ {texto_aproximacion}").classes("biseccion-aproximacion texto-principal")
        ui.label(motivo(respuesta)).classes("texto-acento" if respuesta["estado"] == "EXITO" else "texto-advertencia")
        _mostrar_metricas(respuesta)
        ui.label("El redondeo de presentación no determina la convergencia. Inspecciona hasta 17 cifras en la tabla.").classes("text-sm texto-secundario")
        if respuesta.get("aviso"):
            ui.label(respuesta["aviso"]).classes("text-sm texto-advertencia")
        renderizar_copia_resultado({"estado": respuesta["estado"], "solucion": f"x ≈ {texto_aproximacion}\n" +
                                   "\n".join(f"{etiqueta}: {valor}" for etiqueta, valor in _metricas(respuesta)) + "\n" + motivo(respuesta)})


def _mostrar_metricas(respuesta: dict) -> None:
    with ui.element("div").classes("biseccion-metricas"):
        for etiqueta, valor in _metricas(respuesta):
            with ui.column().classes("gap-1 min-w-0"):
                ui.label(etiqueta).classes("text-sm texto-secundario")
                ui.label(valor).classes("biseccion-numero texto-principal")


def _metricas(respuesta: dict) -> tuple:
    inferior, superior = respuesta["intervalo_final"]
    return (("Tolerancia E", numero(respuesta["tolerancia"])),
            ("Intervalo final [a, b]", f"[{numero(inferior, True)}, {numero(superior, True)}]"),
            ("Cota geométrica (b − a) / 2", numero(respuesta["cota"], True)),
            ("Residuo |f(c)|", numero(respuesta["metricas"].get("residuo_final"), True)),
            ("Iteraciones", str(len(respuesta["iteraciones"]))))


def _reproductor(vista, respuesta: dict) -> None:
    pasos, grupos = construir_pasos(respuesta)

    def renderizar_cuerpo(paso, contenedor) -> None:
        """Actualiza la figura del paso y muestra sus magnitudes internas en texto."""
        if not vista.grafica.is_deleted:
            vista.grafica.update_figure(crear_figura(respuesta, respuesta["muestra"], paso.cuerpo, paso.tipo == "planteamiento"))
        if paso.cuerpo:
            with contenedor:
                for clave, etiqueta in COLUMNAS:
                    ui.label(f"{etiqueta}: {numero(paso.cuerpo[clave], True)}").classes("biseccion-numero text-sm")

    vista.reproductor_pasos = ReproductorPasos(pasos, grupos, renderizar_cuerpo, "biseccion", {
        "titulo": "Procedimiento paso a paso", "al_explicar": crear_accion_explicacion(vista.panel_ia, pasos),
        "esta_ocupado": lambda: bool(getattr(vista.panel_ia, "_esta_enviando", False)),
        "lineas_ayuda": ("Al cambiar de paso se actualiza el intervalo dibujado. Usa las flechas, el índice o la reproducción automática.",),
    })
    vista.reproductor_pasos.construir()


def _tabla(respuesta: dict) -> None:
    with ui.column().classes("panel-tarjeta p-5 w-full min-w-0"):
        ui.label("Tabla de iteraciones").classes("text-xl font-bold")
        ui.label("Ancho: b−a. Cota: (b−a)/2 en x, si f es continua. Residuo: |f(c)|. Error relativo: |(cᵢ−cᵢ₋₁)/cᵢ|·100%; no aplica en la primera fila o si cᵢ=0.").classes("text-sm texto-secundario")
        interruptor = ui.switch("Inspeccionar valores internos (hasta 17 cifras)")
        with ui.element("div").classes("biseccion-tabla w-full").props('tabindex=0 role=region aria-label="Tabla de iteraciones con desplazamiento horizontal"'):
            tabla = ui.table(columns=[{"name": clave, "label": etiqueta, "field": clave, "align": "left"}
                                      for clave, etiqueta in COLUMNAS], rows=filas_tabla(respuesta), row_key="i", pagination=15).classes("w-full")
            tabla.props('rows-per-page-label="Filas por página" :pagination-label="(inicio, fin, total) => inicio + \'-\' + fin + \' de \' + total"')
        interruptor.on_value_change(lambda evento: tabla.update_rows(filas_tabla(respuesta, bool(evento.value))))
