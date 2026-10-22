"""Presencia y vaciado de la captura de la escena geométrica activa."""
from src.backend.utilidades.estado_captura import captura_vacia
from src.frontend.controladores.limpieza_captura import retirar_estado_calculado


class MixinLimpiezaGeometria:
    """Retira capturas y figuras sin depender de un panel de resultados."""

    def _panel_vectorial_activo(self):
        return self.panel_vectores if self.escena == 'vectores' else self.panel_combinacion

    def esta_completamente_vacio(self) -> bool:
        """Consulta exclusivamente las entradas de la escena activa."""
        if self.escena == 'rectas-planos':
            return self.cuadricula.esta_completamente_vacio()
        valores = (valor for vector in self._panel_vectorial_activo().vectores.values()
                   for valor in vector['celdas'].values())
        return captura_vacia(valores, considerar_cero=False)

    def limpiar_todo(self) -> None:
        """Cancela la actualización pendiente y devuelve la escena al estado vacío."""
        self._cancelar_actualizacion()
        if self.escena == 'rectas-planos':
            self.cuadricula.limpiar()
        else:
            panel = self._panel_vectorial_activo()
            for vector in panel.vectores.values():
                vector['celdas'].clear()
            panel.renderizar_todos_vectores()
        self._cancelar_actualizacion()
        self._tarea_previa = None
        self.ultimo_hash_entrada = None
        self._primer_dibujo = True
        self._elemento_plotly = None
        self._clave_figura = None
        self._mostrar_estado_vacio()
        retirar_estado_calculado(self)

    async def _visualizar_captura(self) -> None:
        self._cancelar_actualizacion()
        self._tarea_previa = self._lanzar_tarea(self._actualizar_figura())
        await self._tarea_previa
