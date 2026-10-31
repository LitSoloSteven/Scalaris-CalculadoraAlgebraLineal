"""Integración de Glosa y ciclo de vida de los modelos matriciales."""
from nicegui import ui

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.cuadricula_base import ubicar_celda_matriz
from src.frontend.controladores.limpieza_captura import retirar_estado_calculado
from src.frontend.controladores.sesion_matricial import invalidar_resultado, actualizar_contexto, programar_vista_previa, cancelar_vista_previa
from src.frontend.controladores.operaciones_matrices.contexto_modelos import obtener_contexto_modelo, obtener_senales_modelo
from ._presentacion_modelos import montar_pasos_modelo
from .herramientas_modelos import MixinHerramientasModelos
from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.componentes.acciones_matriz import renderizar_acciones_matriz


class MixinGlosaModelos(MixinHerramientasModelos):
    """Comparte contexto, señales e invalidación de modelos sin conservar cálculos obsoletos."""

    def _conectar_modelo(self) -> None:
        self.reproductor_pasos = None
        self.panel_ia = PanelIA(self)
        self.panel_ia.construir()
        self._construir_herramientas_modelo()
        ui.context.client.on_delete(self._desmontar_modelo)
        self._sincronizar_captura_modelo()

    def _desmontar_modelo(self) -> None:
        cancelar_vista_previa(self)
        invalidar_resultado(self)

    def _sincronizar_captura_modelo(self) -> None:
        retirar_estado_calculado(self)
        for campo in self._campos_captura():
            if not getattr(campo, "_vigila_modelo", False):
                campo.on_value_change(self._restablecer_resultados)
                campo._vigila_modelo = True
        if getattr(self, "contenedor_vista_previa", None):
            programar_vista_previa(self)

    def obtener_contexto_ia(self):
        """Devuelve la captura y el resultado vigente para Glosa."""
        return obtener_contexto_modelo(self)

    def _completar_resultado_modelo(self, captura: dict | None = None) -> None:
        self.panel_ia.renderizar_sugerencias_en_linea()
        renderizar_copia_resultado(self.ultimo_resultado)
        self.reproductor_pasos = montar_pasos_modelo(self)
        self._registrar_modelo()
        if self.ultimo_resultado.get("estado") == "EXITO" and captura is not None:
            clave = "matriz_coeficientes" if self.herramienta_modelo == "leontief" else "matriz_transformacion"
            renderizar_acciones_matriz(self.herramienta_modelo, captura[clave])
        actualizar_contexto(self)

    def obtener_senales_ia(self):
        """Devuelve estados, banderas y errores numéricos del modelo actual."""
        return obtener_senales_modelo(self)

    def enfocar_celda(self, coordenada: tuple[int, int]) -> None:
        """Enfoca la celda indicada por una sugerencia de Glosa."""
        ubicar_celda_matriz("C" if self.herramienta_modelo == "leontief" else "A", *coordenada)
