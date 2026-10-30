"""Integración de Glosa y ciclo de vida de los modelos matriciales."""
from nicegui import ui

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.cuadricula_base import ubicar_celda_matriz
from src.frontend.controladores.limpieza_captura import retirar_estado_calculado
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto
from src.frontend.controladores.operaciones_matrices.contexto_modelos import obtener_contexto_modelo, obtener_senales_modelo
from ._presentacion_modelos import montar_pasos_modelo


class MixinGlosaModelos:
    """Comparte contexto, señales e invalidación de modelos sin conservar cálculos obsoletos."""

    def _conectar_modelo(self) -> None:
        self.reproductor_pasos = None
        self.panel_ia = PanelIA(self)
        self.panel_ia.construir()
        ui.context.client.on_delete(lambda: invalidar_resultado(self))
        self._sincronizar_captura_modelo()

    def _sincronizar_captura_modelo(self) -> None:
        retirar_estado_calculado(self)
        for campo in self._campos_captura():
            if not getattr(campo, "_vigila_modelo", False):
                campo.on_value_change(self._restablecer_resultados)
                campo._vigila_modelo = True

    def obtener_contexto_ia(self):
        """Devuelve la captura y el resultado vigente para Glosa."""
        return obtener_contexto_modelo(self)

    def _completar_resultado_modelo(self) -> None:
        self.panel_ia.renderizar_sugerencias_en_linea()
        self.reproductor_pasos = montar_pasos_modelo(self)
        actualizar_contexto(self)

    def obtener_senales_ia(self):
        """Devuelve estados, banderas y errores numéricos del modelo actual."""
        return obtener_senales_modelo(self)

    def enfocar_celda(self, coordenada: tuple[int, int]) -> None:
        """Enfoca la celda indicada por una sugerencia de Glosa."""
        ubicar_celda_matriz("C" if self.herramienta_modelo == "leontief" else "A", *coordenada)
