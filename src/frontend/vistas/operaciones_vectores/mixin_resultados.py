"""Presentación de resultados y procedimientos de operaciones vectoriales."""
import html

from nicegui import ui

from src.frontend.controladores.operaciones_vectores.captura import preparar_transferencia
from ._pasos_reproductor import construir_pasos_combinacion_lineal, construir_pasos_vector_basico
from .mixin_pasos import MixinPasosVectores, OpcionesReproductorVectores


class MixinResultadosVectores(MixinPasosVectores):
    """Presenta errores, resultados y procedimientos en el panel de salida."""

    def renderizar_estado_vacio(self) -> None:
        """Retira la salida y detiene la reproducción activa antes de mostrar orientación."""
        if self.reproductor_pasos is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None
        if self.panel_resultados is None:
            return
        self.panel_resultados.clear()
        with (
            self.panel_resultados,
            ui.column().classes("w-full h-full justify-center items-center text-center opacity-50"),
        ):
            ui.icon("functions", size="4rem").classes("mb-4")
            ui.label("Ingresa los vectores y presiona Calcular").classes("text-lg")

    def renderizar_resultado(self, resultado: dict) -> None:
        """Muestra el estado del cálculo y compone su resumen y procedimiento."""
        if self.reproductor_pasos is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None
        self.panel_resultados.clear()
        with self.panel_resultados:
            estado = resultado.get("estado", "ERROR")
            mensaje = resultado.get("mensaje", "")
            self._renderizar_insignia(estado, mensaje)
            if self.panel_ia:
                self.panel_ia.renderizar_sugerencias_en_linea()
            if estado == "ERROR":
                return
            if self.operacion_activa in ("suma_resta", "escalar"):
                self.renderizar_resultado_basico(resultado)
            else:
                self.renderizar_resultado_combinacion(resultado)
            self._renderizar_boton_visualizador(resultado)

    def _renderizar_insignia(self, estado: str, mensaje: str) -> None:
        clase, icono = "distintivo-exito", "check"
        if estado == "ERROR":
            clase, icono = "distintivo-error", "close"
        elif self.operacion_activa == "combinacion_lineal":
            clase, icono = {"UNICA": ("distintivo-exito", "check"),
                            "INFINITA": ("distintivo-advertencia", "warning_amber")}.get(estado, ("distintivo-error", "close"))
        with ui.row().classes(f"items-center gap-2 px-4 py-2 {clase} mb-6 w-fit"):
            ui.icon(icono, size="sm")
            ui.label(mensaje).classes("font-bold").props('role="alert"' if estado == "ERROR" else 'role="status"')

    def renderizar_resultado_basico(self, resultado: dict) -> None:
        """Muestra el vector resultante y su procedimiento de componentes."""
        latex_final = resultado.get("vector_resultado_latex")
        if not latex_final and resultado.get("detalles_latex"):
            latex_final = resultado["detalles_latex"][-1]
        if latex_final:
            ui.label("Resultado").classes("text-xl font-bold mb-4 texto-principal")
            with ui.card().classes("panel-tarjeta w-full p-6 mb-6 items-center justify-center"):
                ui.html(f'<div class="matematicas-desplazamiento matematicas-etiqueta p-4 text-lg text-center">$$ {html.escape(latex_final)} $$</div>')
        pasos, grupos = construir_pasos_vector_basico(resultado)
        if len(pasos) > 1:
            self._renderizar_reproductor(pasos, grupos, OpcionesReproductorVectores(
                "vector-basico", tipos_leyenda=("inicial", "ajuste", "componente", "resultado")))

    def renderizar_resultado_combinacion(self, resultado: dict) -> None:
        """Muestra coeficientes o parámetros y el procedimiento de combinación lineal."""
        estado = resultado.get("estado")
        if estado == "UNICA":
            coeficientes = ", ".join(resultado.get("coeficientes_texto", []))
            coeficientes_seguros = html.escape(coeficientes)
            ui.html(f'<div class="matematicas-desplazamiento mb-4"><strong>Coeficientes:</strong> <code class="font-mono text-sm">{coeficientes_seguros}</code></div>')
        elif estado == "INFINITA":
            solucion = ", ".join(resultado.get("solucion_parametrica", []))
            solucion_segura = html.escape(solucion)
            parametros = ", ".join(resultado.get("parametros_libres", []))
            parametros_seguros = html.escape(parametros)
            ui.html(f'<div class="matematicas-desplazamiento mb-4"><strong>Solución paramétrica:</strong> <code class="font-mono text-sm">{solucion_segura}</code></div>')
            ui.html(f'<div class="matematicas-desplazamiento mb-4"><strong>Variables libres:</strong> <code class="font-mono text-sm">{parametros_seguros}</code></div>')
        pasos, grupos = construir_pasos_combinacion_lineal(resultado)
        if pasos:
            self._renderizar_reproductor(pasos, grupos, OpcionesReproductorVectores(
                "vector-combinacion", tipos_leyenda=("planteamiento", "eliminacion", "sustitucion", "verificacion")))

    def _renderizar_boton_visualizador(self, resultado: dict) -> None:
        if resultado.get("estado") == "ERROR":
            return
        from src.frontend.componentes.transferencia import url_transferencia, guardar_vectores
        from src.frontend.navegacion import ruta_de
        vectores, escena = preparar_transferencia(self.operacion_activa, self._capturar())
        if not vectores:
            return

        def ir_al_visualizador():
            """Transfiere los vectores capturados al visualizador geométrico."""
            token = guardar_vectores("vectores", escena, vectores)
            destino = url_transferencia(ruta_de("visualizador"), token) + f"&escena={escena}"
            ui.navigate.to(destino)

        with ui.row().classes("mt-6"):
            ui.button("Ver en el Visualizador", icon="explore", color=None,
                      on_click=ir_al_visualizador).classes("boton-discreto").props("ripple=false")
