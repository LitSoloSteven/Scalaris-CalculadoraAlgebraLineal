"""Panel de exploración independiente con cancelación y selección de respuestas vigentes."""
import asyncio
import logging

from nicegui import ui
from src.backend.resolutores.raices.unidades_angulares import opciones_unidad

from src.frontend.controladores.biseccion.vigencia_panel import invalidar_panel
from src.frontend.controladores.biseccion.exploracion import (
    LONGITUD_CAMPO_EXPLORACION, PASO_EXPLORACION_DEFECTO, presentar_candidato, resolver_exploracion, sugerir_paso,
)
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from .acciones_captura import desplegable
from .candidatos import mostrar_candidatos
from .modos_captura import MODO_BUSQUEDA
from .rango_grafica import campos_rango

registro = logging.getLogger(__name__)
_ESTADO_INICIAL = "Define un rango y un paso para explorar la función."


class PanelExploracion:
    """Gestiona solo el rango exploratorio, sus tareas y la carga explícita de un candidato."""

    def __init__(self, vista):
        self.vista = vista
        self._revision_captura = 0
        self._identificador_calculo = 0
        self.tarea = None
        self.respuesta = None
        self._cerrado = False
        self._paso_automatico = True

    def construir(self) -> None:
        """Monta campos con nombres accesibles y estados de carga, error y candidatos."""
        with ui.column().classes("panel-tarjeta biseccion-panel-exploracion w-full gap-4 p-6"):
            ui.label("Explorar intervalos").classes("text-xl font-semibold texto-principal")
            ui.label("Busca candidatos en el rango del gráfico. Los extremos del cálculo cambian al cargar un intervalo.").classes(
                "text-sm texto-secundario")
            self.minimo, self.maximo = campos_rango("rango de búsqueda")
            with desplegable("Avanzado"):
                self.paso = self._campo("Paso h", PASO_EXPLORACION_DEFECTO)
                self.etiqueta_paso = ui.label().classes("text-sm texto-secundario")
                ui.button("Volver a automático", color=None, on_click=self.restablecer_paso).classes("boton-discreto")
            with ui.row().classes("w-full gap-3"):
                self.boton = ui.button("Explorar candidatos", color=None, on_click=self.enviar_busqueda).classes(
                    "boton-principal").props("ripple=false")
            self.estado = ui.label(_ESTADO_INICIAL).classes(
                "texto-secundario").props("role=status aria-live=polite")
            self.contenedor_resultados = ui.column().classes("biseccion-candidatos w-full gap-4")
        for campo in self._campos_captura():
            campo.on("keydown.enter", self.enviar_busqueda)
        self.paso.on_value_change(self._editar_rango)
        self.actualizar_paso()

    async def enviar_busqueda(self) -> None:
        """Busca desde los controles solo cuando Buscar intervalo está activo."""
        if self.vista.modos.value == MODO_BUSQUEDA:
            await self.explorar()

    def _editar_rango(self) -> None:
        if not self.vista._cargando_captura:
            self._paso_automatico = False
            self.invalidar()
            self.actualizar_paso()

    def restablecer_paso(self) -> None:
        """Recupera la sugerencia de paso y retira el escaneo hecho con el paso anterior."""
        self._paso_automatico = True
        self.actualizar_paso()
        self.invalidar()

    def actualizar_paso(self) -> None:
        """Publica la sugerencia visible de paso o la orientación ante un rango inválido."""
        if not self._paso_automatico:
            self.etiqueta_paso.set_text("Paso manual.")
            return
        try:
            valor = sugerir_paso({"x_min": self.minimo.value, "x_max": self.maximo.value})
            texto = f"Paso automático efectivo · {valor:.9g}"
        except ValueError as error:
            texto = str(error)
        self.etiqueta_paso.set_text(texto)

    def _capturar_paso(self):
        if not self._paso_automatico:
            return self.paso.value
        try:
            return sugerir_paso({"x_min": self.minimo.value, "x_max": self.maximo.value})
        except ValueError:
            return None

    def _campo(self, etiqueta: str, valor: str = ""):
        return ui.input(etiqueta, value=valor).classes("w-full matriz-entrada").props(
            f"inputmode=decimal maxlength={LONGITUD_CAMPO_EXPLORACION} autocomplete=off")

    def _campos_captura(self) -> tuple:
        return self.minimo, self.maximo, self.paso

    def capturar(self) -> dict:
        """Entrega función y rango sin exigir un criterio de parada válido."""
        return {"expresion": self.vista.expresion.value, "x_min": self.minimo.value,
                "x_max": self.maximo.value, "paso": self._capturar_paso(),
                **opciones_unidad(self.vista.unidad_angular.value)}

    def invalidar(self) -> None:
        """Cancela la espera y retira acciones antiguas sin tocar el resultado matemático."""
        invalidar_panel(self)
        lote = getattr(self.vista, "resolucion_multiple", None)
        if lote is not None:
            lote.retirar_candidatos()
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text("Datos editados. Explora para obtener candidatos vigentes.")
            self._mostrar_carga(False)

    def usar_intervalo(self) -> None:
        """Copia los extremos capturados al rango exploratorio sin calcular ni cambiar a/b."""
        self.vista.vista_previa.usar_intervalo()

    def mostrar_estado_inicial(self) -> None:
        """Restablece la orientación tras vaciar el rango de búsqueda."""
        self.estado.set_text(_ESTADO_INICIAL)

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
        lote = getattr(self.vista, "resolucion_multiple", None)
        if lote is not None and respuesta["estado"] == "EXITO":
            lote.actualizar_candidatos(respuesta)

    def seleccionar(self, respuesta: dict, candidato: dict) -> None:
        """Carga un intervalo apto actual y deja el cálculo posterior a una acción explícita."""
        if self._cerrado or self.contenedor_resultados.is_deleted or self.vista.ocupado:
            return
        if self.respuesta is not respuesta or not any(candidato is actual for actual in respuesta["candidatos"]):
            return
        if not presentar_candidato(candidato)["seleccionable"]:
            return
        inferior, superior = candidato["intervalo"]
        captura = {"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior)}
        if candidato["tipo"] == "cero_evaluado":
            captura["cero_preferido"] = candidato["abscisa"]
        self.vista.cargar_captura(captura)
        self.vista.inferior.run_method("focus")

    def cerrar(self) -> None:
        """Invalida acciones y cancela la espera del cliente desconectado."""
        self.invalidar()
        self._cerrado = True

    def reabrir(self) -> None:
        """Permite nuevas solicitudes al reconectar sin recuperar respuestas anteriores."""
        self._cerrado = False
