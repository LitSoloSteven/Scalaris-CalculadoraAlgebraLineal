"""Presentacion de la vista previa de sistemas lineales."""

import html
import itertools
import logging

from nicegui import ui

from src.frontend.controladores.sistemas_lineales.captura import preparar_vista_previa

registro = logging.getLogger(__name__)


class MixinVistaPreviaSistemasLineales:
    """Actualiza y dibuja la vista previa de los modos Matriz y Ecuaciones."""

    _contador_previa = itertools.count()

    async def _actualizar_vista_previa(self):
        """Espera el intervalo de antirrebote y actualiza la vista previa activa."""
        contenedor = getattr(self, "contenedor_vista_previa", None)
        if contenedor is None or contenedor.is_deleted:
            return
        if contenedor.is_deleted or contenedor is not self.contenedor_vista_previa:
            return
        try:
            contenedor.clear()
            with contenedor:
                if self.pestanas_modo.value == "Ecuaciones":
                    self._actualizar_previa_ecuaciones()
                else:
                    self._actualizar_previa_matriz()
        except Exception as error:
            registro.error("Error al actualizar vista previa", exc_info=error)
            if not contenedor.is_deleted:
                with contenedor:
                    self._pintar_mensaje("No se pudo generar la vista previa.")

    def _actualizar_previa_matriz(self):
        """Prepara la matriz aumentada y sus ecuaciones desde las celdas."""
        matriz_a, vector_b = self.cuadricula.obtener_datos_matriz()
        resultado = preparar_vista_previa({"matriz_a": matriz_a, "vector_b": vector_b})
        if resultado["estado"] == "vacio":
            self._pintar_mensaje("La matriz está vacía.")
            return
        self._pintar_bloques(resultado)

    def _actualizar_previa_ecuaciones(self):
        """Analiza y presenta las ecuaciones escritas por la persona."""
        lineas = [entrada.value or "" for entrada in self.entradas_ecuaciones]
        resultado = preparar_vista_previa({"ecuaciones": lineas})
        if resultado["estado"] == "vacio":
            self._pintar_mensaje("Escribe al menos una ecuación para ver la vista previa.")
            return
        if resultado["estado"] == "error":
            self._pintar_mensaje(resultado["mensaje"], error=True)
            return
        self._pintar_bloques(resultado)

    def _pintar_bloques(self, resultado: dict):
        """Renderiza bloques matemáticos y el estado de validación."""
        if resultado["matriz_latex"] is None:
            return
        identificador = next(self._contador_previa)
        id_matriz = f"sistemas-previa-matriz-{identificador}"
        id_sistema = f"sistemas-previa-ecuaciones-{identificador}"
        latex_matriz = html.escape(resultado["matriz_latex"])
        ui.html(self._bloque_latex(id_matriz, latex_matriz, "mb-6"))
        if resultado["mensaje"]:
            self._pintar_mensaje(resultado["mensaje"], error=True)
        if resultado.get("mensaje_sistema"):
            self._pintar_mensaje(resultado["mensaje_sistema"])
        elif resultado["sistema_latex"] is not None:
            latex_ecuaciones = html.escape(resultado["sistema_latex"])
            ui.html(self._bloque_latex(id_sistema, latex_ecuaciones, ""))
        ui.run_javascript(f"if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax(['{id_matriz}', '{id_sistema}']);")

    @staticmethod
    def _bloque_latex(identificador: str, contenido: str, margen: str) -> str:
        """Construye un bloque MathJax contenido en su propio scroll."""
        return (
            f'<div id="{identificador}" class="matematicas-desplazamiento matematicas-etiqueta '
            f'text-lg w-full text-center {margen}">$$ {contenido} $$</div>'
        )

    @staticmethod
    def _pintar_mensaje(mensaje: str, error: bool = False):
        """Muestra una orientación o un error de validación."""
        clase = "distintivo-error" if error else "texto-secundario italic text-sm"
        ui.label(mensaje).classes(f"{clase} mt-4 text-center")
