"""Panel de exploración independiente con cancelación y selección de respuestas vigentes."""
import asyncio
import logging

from nicegui import ui

from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion
from src.frontend.controladores.biseccion.exploracion import (
    LONGITUD_CAMPO_EXPLORACION, PASO_EXPLORACION_DEFECTO, presentar_candidato, resolver_exploracion,
)
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from .candidatos import mostrar_candidatos

registro = logging.getLogger(__name__)


class PanelExploracion:
    """Gestiona solo el rango exploratorio, sus tareas y la carga explícita de un candidato."""

    def __init__(self, vista):
        self.vista = vista
        self._revision_captura = 0
        self._identificador_calculo = 0
        self.tarea = None
        self.respuesta = None
        self._cerrado = False

    def construir(self) -> None:
        """Monta campos con nombres accesibles y estados de carga, error y candidatos."""
        with ui.column().classes("panel-tarjeta biseccion-panel-exploracion w-full gap-4 p-6"):
            ui.label("Explorar intervalos").classes("text-xl font-semibold texto-principal")
            ui.label("Busca candidatos de la función capturada en un rango independiente. Los resultados del cálculo se conservan hasta cargar un intervalo.").classes(
                "text-sm texto-secundario")
            with ui.element("div").classes("biseccion-campos"):
                self.minimo = self._campo("Mínimo de exploración x_min")
                self.maximo = self._campo("Máximo de exploración x_max")
            self.paso = self._campo("Paso de exploración h", PASO_EXPLORACION_DEFECTO)
            with ui.row().classes("w-full gap-3"):
                ui.button("Usar intervalo actual", color=None, on_click=self.usar_intervalo).classes("boton-discreto").props("ripple=false")
                self.boton = ui.button("Explorar candidatos", color=None, on_click=self.explorar).classes("boton-discreto").props("ripple=false")
            self.estado = ui.label("Define un rango y un paso para explorar la función.").classes(
                "texto-secundario").props("role=status aria-live=polite")
            self.contenedor_resultados = ui.column().classes("biseccion-candidatos w-full gap-4")
        for campo in self._campos_captura():
            campo.on_value_change(self.invalidar)
            campo.on("keydown.enter", self.explorar)

    def _campo(self, etiqueta: str, valor: str = ""):
        return ui.input(etiqueta, value=valor).classes("w-full matriz-entrada").props(
            f"inputmode=decimal maxlength={LONGITUD_CAMPO_EXPLORACION} autocomplete=off")

    def _campos_captura(self) -> tuple:
        return self.minimo, self.maximo, self.paso

    def capturar(self) -> dict:
        """Entrega función y rango sin exigir un criterio de parada válido."""
        return {"expresion": self.vista.expresion.value, "x_min": self.minimo.value,
                "x_max": self.maximo.value, "paso": self.paso.value}

    def invalidar(self) -> None:
        """Cancela la espera y retira acciones antiguas sin tocar el resultado matemático."""
        self._revision_captura += 1
        self._identificador_calculo += 1
        cancelar_actualizacion(self.tarea)
        self.tarea = None
        self.respuesta = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text("Datos editados. Explora para obtener candidatos vigentes.")
            self._mostrar_carga(False)

    def usar_intervalo(self) -> None:
        """Copia los extremos capturados al rango exploratorio sin calcular ni cambiar a/b."""
        if self._cerrado or self.contenedor_resultados.is_deleted:
            return
        self.minimo.set_value(self.vista.inferior.value)
        self.maximo.set_value(self.vista.superior.value)
        self.invalidar()

    async def explorar(self) -> None:
        """Ejecuta fuera de UI y publica solo en la revisión y contenedor aún vigentes."""
        if self._cerrado or self.contenedor_resultados.is_deleted or self.tarea is not None:
            return
        self.invalidar()
        tarea = self.tarea = asyncio.current_task()
        revision = self._revision_captura
        self._mostrar_carga(True)
        self.estado.set_text("Explorando la malla de la función…")
        try:
            vigente = await ejecutar_calculo_vigente(self, self.capturar, resolver_exploracion)
            if vigente is not None:
                self._publicar(vigente[0])
        except Exception:
            registro.exception("No se pudo presentar la exploración de bisección")
            if revision == self._revision_captura and not self.estado.is_deleted:
                self.estado.set_text("No se pudo completar la exploración. Revisa la función y vuelve a intentarlo.")
        finally:
            if self.tarea is tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _mostrar_carga(self, ocupado: bool) -> None:
        if not self.boton.is_deleted:
            self.boton.set_enabled(not ocupado)
            self.boton.props("loading" if ocupado else "", remove="" if ocupado else "loading")

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        with self.contenedor_resultados:
            if respuesta["estado"] == "EXITO":
                mostrar_candidatos(self, respuesta)
            else:
                ui.label(respuesta["mensaje"]).classes("texto-secundario")

    def seleccionar(self, respuesta: dict, candidato: dict) -> None:
        """Carga un intervalo apto actual y deja el cálculo posterior a una acción explícita."""
        if self._cerrado or self.contenedor_resultados.is_deleted or self.vista.ocupado:
            return
        if self.respuesta is not respuesta or not any(candidato is actual for actual in respuesta["candidatos"]):
            return
        if not presentar_candidato(candidato)["seleccionable"]:
            return
        inferior, superior = candidato["intervalo"]
        self.vista.cargar_captura({"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior)})

    def cerrar(self) -> None:
        """Invalida acciones y cancela la espera del cliente desconectado."""
        self.invalidar()
        self._cerrado = True

    def reabrir(self) -> None:
        """Permite nuevas solicitudes al reconectar sin recuperar respuestas anteriores."""
        self._cerrado = False
