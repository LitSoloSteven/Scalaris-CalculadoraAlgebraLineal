"""Cálculo vigente y presentación de resultados de factorización LU."""
from nicegui import ui

from src.frontend.nucleo.textos import textos
from src.frontend.componentes.captura.nucleo.cuadricula_base import ubicar_celda_matriz
from src.frontend.controladores.compartido.sesion.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.controladores.algebra.operaciones_matrices import ControladorFactorizacionLU
from src.frontend.controladores.compartido.sesion.sesion_matricial import actualizar_contexto, invalidar_resultado
from src.frontend.controladores.algebra.operaciones_matrices.base.captura_factorizacion_lu import localizar_invalida
from src.frontend.vistas.algebra.operaciones_matrices.compartido._estados_modelos import ejecutar_modelo, mostrar_estado
from ._factores_factorizacion_lu import mostrar_factores_lu
from ._presentacion_factorizacion_lu import montar_reproductor_lu
from src.frontend.componentes.exportacion_pdf.montaje.integracion import region_pdf, completar_exportacion
from src.frontend.controladores.exportacion_pdf.documento.vigencia import EnlacePDF
from src.frontend.componentes.resultados.acciones.acciones_matriz import renderizar_acciones_matriz


class ResultadosFactorizacionLU:
    """Coordina cálculos de LU y publica únicamente resultados vigentes."""

    async def calcular(self, evento) -> None:
        """Calcula con el botón del evento o muestra orientación si no hay captura."""
        if self.panel_matriz.esta_vacio():
            mostrar_estado(self.contenedor_resultados, textos.LU_VACIA, "ERROR")
            return
        vacia = self._primera_celda_vacia()
        if vacia is not None:
            fila, columna = vacia
            self._marcar_celda_invalida(fila, columna)
            mostrar_estado(
                self.contenedor_resultados,
                f"La celda A[{fila + 1},{columna + 1}] está vacía. Ingresa un número antes de calcular.",
                "ERROR",
            )
            ubicar_celda_matriz("A", fila, columna)
            return
        if getattr(self, "_calculando", False):
            return
        self._limpiar_estado_invalido()
        invalidar_resultado(self)
        self.panel_ia.limpiar_foco_explicacion()
        actualizar_contexto(self)
        await ejecutar_modelo(self, evento.sender, self._calcular_nucleo)

    async def _calcular_nucleo(self) -> None:
        captura = self._capturar()
        calculo = await ejecutar_calculo_vigente(self, self._capturar, ControladorFactorizacionLU.procesar_captura)
        if calculo is None:
            return
        resultado, self._huella_resultado = calculo
        self.ultimo_resultado = resultado
        self.contenedor_resultados.clear()
        if resultado.get("estado") == "ERROR":
            self._mostrar_error_captura(resultado)
        else:
            self._mostrar_exito(resultado, captura["matriz_a"])
        actualizar_contexto(self)

    def _primera_celda_vacia(self) -> tuple[int, int] | None:
        crudos = getattr(self.panel_matriz, "obtener_datos_crudos", lambda: ())()
        for fila, valores in enumerate(crudos):
            for columna, valor in enumerate(valores):
                if not str(valor or "").strip():
                    return (fila, columna)
        return None

    def _marcar_celda_invalida(self, fila: int, columna: int) -> None:
        celdas = getattr(self.panel_matriz, "celdas", ())
        if 0 <= fila < len(celdas) and 0 <= columna < len(celdas[fila]):
            celdas[fila][columna].props('aria-invalid="true"')

    def _limpiar_estado_invalido(self) -> None:
        for fila in getattr(self.panel_matriz, "celdas", ()):
            for celda in fila:
                celda.props('aria-invalid="false"')

    def _mostrar_error_captura(self, resultado: dict) -> None:
        mostrar_estado(self.contenedor_resultados, resultado["mensaje"], "ERROR")
        datos = self.panel_matriz.obtener_datos_matriz()
        invalida = localizar_invalida(datos)
        if invalida and invalida.foco:
            self._marcar_celda_invalida(*invalida.foco)
            ubicar_celda_matriz("A", *invalida.foco)

    def _mostrar_exito(self, resultado: dict, datos: list[list[str]]) -> None:
        self._agregar_a_historial({"datos": datos, "filas": resultado["filas"], "columnas": resultado["columnas"],
                                   "rango": resultado["rango"], "estado": "FACTORIZACION_LU_CALCULADA"})
        with self.contenedor_resultados:
            with region_pdf('lu-resumen'):
                ui.badge(textos.HISTORIAL_FACTORIZACION_LU_CALCULADA, color=None).classes("distintivo-exito")
                ui.label(textos.LU_DATOS.format(**resultado)).classes("texto-secundario sesion-numero").props('role="status"')
            self.panel_ia.renderizar_sugerencias_en_linea()
            with region_pdf('lu-factores'):
                mostrar_factores_lu(resultado)
            self.reproductor_pasos = montar_reproductor_lu(resultado, self.panel_ia)
            renderizar_acciones_matriz("factorizacion_lu", datos)
            enlace = EnlacePDF(self, self._capturar, f'c{self.contenedor_resultados.id}')
            completar_exportacion(self, 'lu', resultado, enlace)
