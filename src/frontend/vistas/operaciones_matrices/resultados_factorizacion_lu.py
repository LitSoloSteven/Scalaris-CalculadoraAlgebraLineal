"""Cálculo vigente y presentación de resultados de factorización LU."""
from nicegui import ui

from src.frontend import textos
from src.frontend.componentes.cuadricula_base import ubicar_celda_matriz
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.operaciones_matrices import ControladorFactorizacionLU
from src.frontend.controladores.sesion_matricial import actualizar_contexto, invalidar_resultado
from src.frontend.controladores.operaciones_matrices.captura_factorizacion_lu import localizar_invalida
from ._estados_modelos import ejecutar_modelo, mostrar_estado
from ._factores_factorizacion_lu import mostrar_factores_lu
from ._presentacion_factorizacion_lu import montar_reproductor_lu


class ResultadosFactorizacionLU:
    """Coordina cálculos de LU y publica únicamente resultados vigentes."""

    async def calcular(self, evento) -> None:
        """Calcula con el botón del evento o muestra orientación si no hay captura."""
        if self.panel_matriz.esta_vacio():
            mostrar_estado(self.contenedor_resultados, textos.LU_VACIA, "ERROR")
            return
        if getattr(self, "_calculando", False):
            return
        invalidar_resultado(self)
        self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)
        await ejecutar_modelo(self, evento.sender, self._calcular_nucleo)

    async def _calcular_nucleo(self) -> None:
        calculo = await ejecutar_calculo_vigente(self, self._capturar, ControladorFactorizacionLU.procesar_captura)
        if calculo is None:
            return
        resultado, self._huella_resultado = calculo
        self.ultimo_resultado = resultado
        self.contenedor_resultados.clear()
        if resultado.get("estado") == "ERROR":
            self._mostrar_error_captura(resultado)
        else:
            self._mostrar_exito(resultado)
        actualizar_contexto(self)

    def _mostrar_error_captura(self, resultado: dict) -> None:
        mostrar_estado(self.contenedor_resultados, resultado["mensaje"], "ERROR")
        datos = self.panel_matriz.obtener_datos_matriz()
        invalida = localizar_invalida(datos)
        if invalida and invalida.foco:
            ubicar_celda_matriz("A", *invalida.foco)

    def _mostrar_exito(self, resultado: dict) -> None:
        datos = self.panel_matriz.obtener_datos_matriz()
        self._agregar_a_historial({"datos": datos, "filas": resultado["filas"], "columnas": resultado["columnas"],
                                   "rango": resultado["rango"], "estado": "FACTORIZACION_LU_CALCULADA"})
        with self.contenedor_resultados:
            ui.badge(textos.LU_TITULO, color=None).classes("distintivo-exito")
            ui.label(textos.LU_DATOS.format(**resultado)).classes("texto-secundario sesion-numero").props('role="status"')
            self.panel_ia.renderizar_sugerencias_en_linea()
            mostrar_factores_lu(resultado)
            self.reproductor_pasos = montar_reproductor_lu(resultado, self.panel_ia)
