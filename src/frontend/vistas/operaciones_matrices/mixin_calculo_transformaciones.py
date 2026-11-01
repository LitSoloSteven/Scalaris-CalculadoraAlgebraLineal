"""Cálculo y estados de resultado para transformaciones lineales."""
import json
from nicegui import ui
from ._estados_modelos import mostrar_estado
from src.frontend.controladores.operaciones_matrices import ControladorTransformaciones
from src.frontend.controladores.operaciones_matrices.controlador_aplicacion_transformacion import ControladorAplicacionTransformacion
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from src.frontend import textos_transformaciones as textos
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.operaciones_matrices.capturas_modelos import capturar_transformaciones
from ._renderizado_transformaciones import renderizar_resultado_transformaciones
from .resultado_aplicacion_transformacion import renderizar_resultado_aplicacion

from ._estados_modelos import ejecutar_modelo


class MixinCalculoTransformaciones:
    """Orquesta el análisis de la matriz capturada y presenta su resultado."""

    async def _analizar(self, boton):
        if getattr(self, "_calculando", False):
            return
        self._restablecer_resultados()
        await ejecutar_modelo(self, boton, self._analizar_nucleo)

    async def _analizar_nucleo(self):
        captura = capturar_transformaciones(self)
        controlador = (ControladorAplicacionTransformacion if "vector_original" in captura
                       else ControladorTransformaciones)
        calculo = await ejecutar_calculo_vigente(
            self, lambda: capturar_transformaciones(self),
            lambda captura: controlador.procesar(json.dumps(captura)),
        )
        if calculo is None:
            return
        respuesta_json, self._huella_resultado = calculo
        respuesta = json.loads(respuesta_json)
        self.ultimo_resultado = respuesta

        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(remove="items-center justify-center", add="items-start justify-start")
        if "vector_original" in captura:
            self.reproductor_aplicacion = renderizar_resultado_aplicacion(self.contenedor_resultados, respuesta, captura)
            actualizar_contexto(self)
        else:
            self._presentar_analisis(respuesta, captura)

        ui.run_javascript("if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();")

    def _presentar_analisis(self, respuesta: dict, captura: dict) -> None:
        with self.contenedor_resultados:
            renderizar_resultado_transformaciones(respuesta)
            self._completar_resultado_modelo(captura)

    def _restablecer_resultados(self):
        self._sincronizar_captura_modelo()
        mensaje = (textos.ESTADO_APLICACION if self.modo_transformacion == textos.MODO_APLICACION
                   else textos.ESTADO_ANALISIS)
        mostrar_estado(self.contenedor_resultados, mensaje)
