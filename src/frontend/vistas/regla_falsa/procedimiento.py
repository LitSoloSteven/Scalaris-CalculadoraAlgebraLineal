"""Detalle sincronizado de gráfica, fórmula, tabla y foco del procedimiento."""
from nicegui import ui

from src.frontend.componentes.glosa_foco import crear_accion_explicacion
from src.frontend.componentes.reproductor_pasos import ReproductorPasos, renderizar_latex
from src.frontend.controladores.biseccion.formato_expresion import formatear_expresion
from src.frontend.controladores.regla_falsa.formulas_procedimiento import formulas_iteracion
from src.frontend.controladores.regla_falsa.pasos import construir_pasos, referencia_paso
from src.frontend.controladores.regla_falsa.tabla import COLUMNAS, valor_columna
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from .figura import crear_figura
from .tabla_iteraciones import TablaReglaFalsa


class PanelProcedimiento:
    """Publica la fila del paso activo como única fuente del detalle y de la secante."""

    def __init__(self, vista, datos: dict):
        self.vista, self.datos = vista, datos
        self.respuesta = datos["resultado"]
        self.fila_activa = None
        pasos, grupos = construir_pasos(self.respuesta)
        opciones = {"sin_movimiento": True, "titulo": "Procedimiento de regla falsa"}
        if vista.panel_ia is not None:
            opciones.update(al_explicar=crear_accion_explicacion(vista.panel_ia, pasos),
                            esta_ocupado=lambda: bool(getattr(vista.panel_ia, "_esta_enviando", False)))
        self.reproductor = ReproductorPasos(pasos, grupos, self._renderizar, "regla-falsa", opciones)

    def construir(self) -> None:
        """Monta un nodo Plotly persistente y enlaza selección y navegación al reproductor genérico."""
        with self.vista.contenedor_detalle:
            ui.label("Función y secante").classes("text-xl font-bold texto-principal")
            ui.label("El muestreo es orientativo y no demuestra continuidad. La secante usa las evaluaciones del motor.").classes(
                "text-sm texto-secundario")
            self.grafica = ui.plotly(self._figura(None, True)).classes("regla-falsa-grafica w-full").props(
                'role=img aria-label="Función, secante y evaluación del paso activo"')
            self.grafica.on("plotly_afterplot", js_handler="() => window.scalaris?.sincronizarTemaPlotly?.()")
            if self.datos["aviso_grafica"]:
                ui.label(self.datos["aviso_grafica"]).classes("texto-advertencia text-sm")
            self.estado_paso = ui.label().classes("texto-secundario").props("role=status aria-live=polite")
            contenedor_reproductor = ui.column().classes("w-full min-w-0")
            self.tabla = TablaReglaFalsa(self.respuesta["iteraciones"], self.reproductor.ir_a)
            self.tabla.construir()
            with contenedor_reproductor:
                self.reproductor.construir()

    def _figura(self, fila: dict | None, inicial: bool) -> dict:
        figura = crear_figura(self.respuesta, self.datos["muestra"], fila, inicial)
        return {**figura.to_plotly_json(), "config": {"displayModeBar": False, "responsive": True}}

    def _renderizar(self, paso, contenedor) -> None:
        self.fila_activa = paso.cuerpo
        self.vista._foco_procedimiento = referencia_paso(paso, len(self.reproductor.pasos))
        self.grafica.update_figure(self._figura(paso.cuerpo, paso.tipo == "planteamiento"))
        self.tabla.seleccionar(paso.cuerpo)
        self.estado_paso.set_text(f"Paso {paso.indice + 1}: {paso.descripcion}")
        with contenedor:
            self._mostrar_cuerpo(paso)
        actualizar_contexto(self.vista)

    def _mostrar_cuerpo(self, paso) -> None:
        if paso.cuerpo is not None:
            for formula in formulas_iteracion(paso.cuerpo):
                renderizar_latex(formula, vigilar_region=True)
            for clave, etiqueta in COLUMNAS:
                ui.label(f"{etiqueta}: {valor_columna(paso.cuerpo, clave, True)}").classes(
                    "regla-falsa-numero texto-principal text-sm")
        elif paso.tipo == "planteamiento" and self.respuesta.get("entrada"):
            try:
                formula = formatear_expresion(self.respuesta["entrada"]["expresion"])["latex"]
            except ValueError:
                return
            renderizar_latex(formula, vigilar_region=True)
