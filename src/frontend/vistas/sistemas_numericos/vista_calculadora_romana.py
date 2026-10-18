"""Vista principal de la Calculadora de Números Romanos en Scalaris."""

from __future__ import annotations

import logging
import asyncio
from typing import Any

from nicegui import ui

from src.ai.huellas import calcular_huella
from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    CalculadoraRomana,
    ErrorNumeroRomano,
)
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.navegacion import ruta_de
from src.frontend.controladores.captura_contexto import capturar_romanos
from .mixin_resultado_romano import MixinResultadoRomano
from .mixin_contexto_romanos import MixinContextoRomano
from .mixin_captura_romanos import MixinCapturaRomanos
from .presentacion_romana import PresentacionRomana

registro = logging.getLogger(__name__)


class VistaCalculadoraRomana(MixinResultadoRomano, MixinContextoRomano, MixinCapturaRomanos):
    """Controlador de vista modular para operaciones con números romanos."""

    def __init__(self) -> None:
        self.panel_ia = None
        self.ultimo_resultado = None
        self.ultimo_error = None
        self._huella_resultado = None
        self.reproductor = None
        self.contenedor_sugerencias = None
        self.contenedor_resultado = None
        self.entrada_a = None
        self.entrada_b = None
        self.pestanas_operacion = None
        self.etiqueta_signo = None
        self.etiqueta_error = None
        self.boton_calcular = None
        self._calculando = False

    def construir(self) -> None:
        """Construye la interfaz de usuario de la calculadora romana."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("romanos"))

        with ui.column().classes("w-full max-w-4xl mx-auto items-center q-pa-md mt-6 vista-raiz"):
            with ui.column().classes("w-full panel-tarjeta p-6 gap-6"):
                ui.label("Números romanos").classes("text-2xl font-bold texto-principal")

                with (
                    ui.row().classes("w-full items-center gap-3"),
                    ui.tabs().classes("pestanas-controles pestanas-metodo pestanas-anchas w-full") as self.pestanas_operacion,
                ):
                    ui.tab("suma", label="Suma")
                    ui.tab("resta", label="Resta")
                    ui.tab("multiplicacion", label="Multiplicación")

                self._construir_ejemplos_rapidos()
                self._construir_campos_entrada()

                self.contenedor_sugerencias = ui.column().classes("w-full mt-2")
                self.boton_calcular = ui.button(
                    "Calcular", on_click=self._operar_desde_control, color=None
                ).classes("boton-principal w-full py-3 text-lg mt-2 font-bold")

            self.contenedor_resultado = ui.column().classes("w-full gap-6 mt-6")
            with self.contenedor_resultado:
                ui.label("Ingresa dos operandos romanos y pulsa Calcular.").props('role="status"')

        self._conectar_controles()
        self.panel_ia.construir()

    def _conectar_controles(self):
        self.pestanas_operacion.on_value_change(self.actualizar_signo)
        self.pestanas_operacion.set_value("suma")
        self.entrada_a.on_value_change(lambda _: self._notificar_cambio())
        self.entrada_b.on_value_change(lambda _: self._notificar_cambio())
        self.entrada_a.on("keydown.enter", self._operar_desde_control)
        self.entrada_b.on("keydown.enter", self._operar_desde_control)


    def operar_romanos(self) -> None:
        """Ejecuta la operación aritmética romana y monta el resultado y los pasos."""
        self.etiqueta_error.text = ""
        self._orientar_error_operandos()
        if self.reproductor is not None:
            self.reproductor.detener()
            self.reproductor = None
        self.contenedor_resultado.clear()

        operando_a = (self.entrada_a.value or "").strip().upper()
        operando_b = (self.entrada_b.value or "").strip().upper()
        operacion = getattr(self.pestanas_operacion, "value", "suma") or "suma"

        try:
            resultado, presentacion = self._ejecutar_resolutor(operacion, operando_a, operando_b)
            self.ultimo_resultado = resultado
            self.ultimo_error = None
            self._renderizar_vista_exito(resultado, presentacion)
        except ErrorNumeroRomano as error:
            self._manejar_error(error, str(error))
        except Exception:
            registro.exception("Error inesperado en calculadora de números romanos")
            self._manejar_error(None, "Ocurrió un error inesperado al procesar la operación. Inténtalo de nuevo.")
        finally:
            self._finalizar_calculo(operando_a, operando_b, operacion)

    async def _operar_desde_control(self) -> None:
        if self._calculando:
            return
        self._calculando = True
        self.boton_calcular.props("loading")
        try:
            await asyncio.sleep(0)
            self.operar_romanos()
        finally:
            self._calculando = False
            self.boton_calcular.props(remove="loading")

    def _ejecutar_resolutor(self, operacion: str, operando_a: str, operando_b: str) -> tuple[Any, PresentacionRomana]:
        resolutor, simbolo, nombre = {
            "suma": (CalculadoraRomana.sumar, "+", "Suma"),
            "resta": (CalculadoraRomana.restar, "−", "Resta"),
            "multiplicacion": (CalculadoraRomana.multiplicar_un_digito, "×", "Multiplicación"),
        }[operacion]
        presentacion = PresentacionRomana((operando_a, operando_b), simbolo, nombre, operacion)
        return resolutor(operando_a, operando_b), presentacion

    def _renderizar_vista_exito(self, resultado: Any, presentacion: PresentacionRomana) -> None:
        self._actualizar_sugerencias()
        with self.contenedor_resultado:
            self._renderizar_tarjeta_resultado_destacado(presentacion, resultado.resultado_romano)
            self._renderizar_reproductor_romano(resultado, presentacion.operacion)

    def _actualizar_sugerencias(self) -> None:
        if self.panel_ia and self.contenedor_sugerencias:
            self.contenedor_sugerencias.clear()
            with self.contenedor_sugerencias:
                self.panel_ia.renderizar_sugerencias_en_linea()

    def _manejar_error(self, error: Exception | None, mensaje: str) -> None:
        """Registra el fallo y actualiza la orientación de operandos y sugerencias."""
        self.ultimo_resultado = None
        self.ultimo_error = error
        self.etiqueta_error.text = mensaje
        self._orientar_error_operandos(error, mensaje)
        self._actualizar_sugerencias()

    def _finalizar_calculo(self, operando_a: str, operando_b: str, operacion: str) -> None:
        """Registra la huella de entrada y actualiza el contexto de IA."""
        entrada = capturar_romanos(operando_a, operando_b, operacion)
        self._huella_resultado = calcular_huella(entrada)
        self._notificar_cambio()
