"""Orquesta el resumen, la tabla y el reproductor de la solución."""
from collections.abc import Callable

from nicegui import ui

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.controladores.metodos_abiertos.pasos import construir_secuencia
from .procedimiento import renderizar_iteracion, renderizar_resumen_paso
from .resumen import mostrar_resumen
from .tabla import TablaIteraciones


class SalidaMetodosAbiertos:
    """Mantiene sincronizadas la tabla, el reproductor y la gráfica activa."""

    def __init__(self, actualizar_figura: Callable[[dict | None], None]):
        self._actualizar_figura = actualizar_figura
        self.resultado = None
        self.fila_activa = None
        self.reproductor = None
        self.tabla = TablaIteraciones(self._seleccionar_fila)

    def mostrar(self, datos: dict, contenedor_resultados, contenedor_reproductor) -> None:
        """Presenta el resultado y crea el reproductor de su procedimiento."""
        self.resultado = datos
        with contenedor_resultados:
            mostrar_resumen(datos)
            if datos.get("iteraciones"):
                self._mostrar_tabla(datos)
        self._crear_reproductor(datos, contenedor_reproductor)

    def _mostrar_tabla(self, datos: dict) -> None:
        with ui.column().classes(
                "w-full min-w-0 gap-2 metodos-abiertos-entrada metodos-abiertos-entrada-2"):
            ui.label("Tabla de iteraciones").classes("text-xl font-semibold texto-principal")
            self.tabla.mostrar(datos["iteraciones"], datos.get("metodo", "newton"))

    def _crear_reproductor(self, datos: dict, contenedor) -> None:
        pasos, grupos = construir_secuencia(datos)
        self.reproductor = ReproductorPasos(
            pasos, grupos, self._renderizar_paso, "metodos-abiertos",
            {"titulo": "Procedimiento de métodos abiertos", "sin_movimiento": True},
        )
        with contenedor:
            self.reproductor.construir()
        if self.reproductor.tarjeta is not None:
            self.reproductor.tarjeta.classes(
                "metodos-abiertos-entrada metodos-abiertos-entrada-3")

    def _renderizar_paso(self, paso, contenedor) -> None:
        if paso.cuerpo is not None:
            self.fila_activa = paso.cuerpo
        elif paso.tipo == "resultado" and self.resultado.get("iteraciones"):
            self.fila_activa = self.resultado["iteraciones"][-1]
        else:
            self.fila_activa = None
        self._actualizar_figura(self.fila_activa)
        self.tabla.sincronizar(self.fila_activa)
        with contenedor:
            self._renderizar_contenido(paso)

    def _renderizar_contenido(self, paso) -> None:
        if paso.cuerpo is None:
            renderizar_resumen_paso(paso, self.resultado)
        else:
            renderizar_iteracion(paso.cuerpo, self.resultado)

    def _seleccionar_fila(self, fila: dict | None, indice_paso: int | None) -> None:
        self.fila_activa = fila
        self._actualizar_figura(fila)
        if self.reproductor is not None and indice_paso is not None:
            self.reproductor.ir_a(indice_paso)
        elif self.reproductor is not None:
            self.reproductor.ir_a(0)

    def limpiar(self, contenedor_resultados, contenedor_reproductor) -> None:
        """Detiene el reproductor y retira el resultado y las filas anteriores."""
        if self.reproductor is not None:
            self.reproductor.detener()
        contenedor_resultados.clear()
        contenedor_reproductor.clear()
        self.resultado = self.fila_activa = self.reproductor = None
        self.tabla.limpiar()
