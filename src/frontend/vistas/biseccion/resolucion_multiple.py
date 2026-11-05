"""Panel de lote con candidatos vigentes, selección individual y trabajo fuera de interfaz."""
import asyncio
import logging

from nicegui import ui

from src.backend.resolutores.raices.limites_resolucion_multiple import MAXIMO_CANDIDATOS_MULTIPLE
from src.frontend.controladores.biseccion.exploracion import presentar_candidato
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.controladores.biseccion.vigencia_panel import invalidar_panel
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from .resultados_multiples import mostrar_resultados_multiples

registro = logging.getLogger(__name__)


class PanelResolucionMultiple:
    """Resuelve una selección del escaneo actual sin alterar el cálculo principal."""

    def __init__(self, vista):
        self.vista = vista
        self.tarea = None
        self.respuesta = None
        self.candidatos = {}
        self._fuente = None
        self._revision_captura = 0
        self._identificador_calculo = 0
        self._cerrado = False
        self._todos = False

    def construir(self) -> None:
        """Monta acciones independientes con selección accesible y estados del lote."""
        with ui.column().classes("panel-tarjeta biseccion-panel-multiple w-full gap-4 p-6"):
            ui.label("Resolver candidatos").classes("text-xl font-semibold texto-principal")
            ui.label(f"Usa el criterio y el límite actuales para resolver uno o hasta {MAXIMO_CANDIDATOS_MULTIPLE} candidatos aptos. "
                     "Cada resultado conserva su propia tabla; el cálculo principal se mantiene.").classes("text-sm texto-secundario")
            self.selector = ui.select({}, label="Candidato para resolver").classes("w-full matriz-entrada")
            self.intervalo = ui.label().classes("biseccion-numero texto-secundario")
            with ui.row().classes("w-full gap-3"):
                self.boton_uno = ui.button("Resolver candidato", color=None, on_click=self.resolver_uno).classes(
                    "boton-discreto").props("ripple=false")
                self.boton_todos = ui.button("Resolver todos los aptos", color=None, on_click=self.resolver_todos).classes(
                    "boton-discreto").props("ripple=false")
            self.estado = ui.label("Explora la función para habilitar candidatos actuales.").classes(
                "texto-secundario").props("role=status aria-live=polite")
            self.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-4")
        self.selector.on_value_change(self._seleccionar)
        self._actualizar_controles(False)
        ui.context.client.on_delete(self.cerrar)

    def _campos_captura(self) -> tuple:
        return (self.selector,)

    def _seleccionar(self) -> None:
        self.invalidar()
        candidato = self.candidatos.get(self.selector.value)
        self.intervalo.set_text(presentar_candidato(candidato)["intervalo"] if candidato else "")

    def actualizar_candidatos(self, fuente: dict) -> None:
        """Recibe solo los candidatos del escaneo recién publicado y retira cualquier lote anterior."""
        self.retirar_candidatos()
        self._fuente = fuente
        self.candidatos = {f"candidato-{indice}": candidato for indice, candidato in enumerate(fuente["candidatos"], 1)
                           if presentar_candidato(candidato)["seleccionable"]}
        opciones = {clave: clave.replace("candidato-", "Candidato ") for clave in self.candidatos}
        self.selector.set_options(opciones, value=next(iter(opciones), None))
        self._seleccionar()
        self.estado.set_text("Elige un candidato o resuelve todos los aptos." if opciones else
                             "Esta malla no contiene candidatos aptos para bisección. Cambia el rango o el paso.")

    def retirar_candidatos(self) -> None:
        """Invalida tareas y selección cuando el escaneo deja de corresponder a la captura."""
        self.invalidar()
        self._fuente = None
        self.candidatos = {}
        if not self.selector.is_deleted:
            self.selector.set_options({}, value=None)
            self.intervalo.set_text("")
            self.estado.set_text("Explora la función para habilitar candidatos actuales.")
            self._actualizar_controles(False)

    def invalidar(self) -> None:
        """Cancela la espera y retira resultados del lote sin tocar el cálculo individual."""
        invalidar_panel(self)
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text("Solicita la resolución para obtener resultados vigentes.")
            self._actualizar_controles(False)

    def capturar(self) -> dict:
        """Entrega configuración común y selección actual con identificadores del escaneo."""
        candidatos = self.candidatos if self._todos else {
            clave: candidato for clave, candidato in self.candidatos.items() if clave == self.selector.value}
        return {"configuracion": self.vista.capturar(), "unidad_angular": self.vista.unidad_angular.value,
                "candidatos": tuple({"identificador": clave, "candidato": candidato}
                                    for clave, candidato in candidatos.items())}

    async def resolver_uno(self) -> None:
        """Resuelve el candidato seleccionado mediante el mismo controlador del lote."""
        await self._resolver(False)

    async def resolver_todos(self) -> None:
        """Resuelve todos los aptos actuales sin truncar una selección excesiva."""
        await self._resolver(True)

    async def _resolver(self, todos: bool) -> None:
        if not self._puede_resolver() or self.tarea is not None or self.vista.ocupado:
            return
        self.invalidar()
        self._todos = todos
        tarea = self.tarea = asyncio.current_task()
        revision = self._revision_captura
        self._actualizar_controles(True)
        self.estado.set_text("Resolviendo candidatos con el criterio actual…")
        try:
            vigente = await ejecutar_calculo_vigente(self, self.capturar, resolver_lote)
            if vigente is not None:
                self._publicar_si_vigente(vigente[0], tarea)
        except Exception:
            registro.warning("No se pudo presentar la resolución múltiple de bisección")
            if revision == self._revision_captura and self._puede_resolver():
                self.estado.set_text("No se pudo completar el lote. Revisa los datos y vuelve a resolver.")
        finally:
            if self.tarea is tarea:
                self.tarea = None
                self._actualizar_controles(False)

    def _puede_resolver(self) -> bool:
        return (not self._cerrado and not self.contenedor_resultados.is_deleted and bool(self.candidatos)
                and self._fuente is self.vista.exploracion.respuesta)

    def _publicar_si_vigente(self, respuesta: dict, tarea: asyncio.Task) -> None:
        if self.tarea is tarea and self._puede_resolver():
            self._publicar(respuesta)

    def _actualizar_controles(self, ocupado: bool) -> None:
        for boton in (self.boton_uno, self.boton_todos):
            if not boton.is_deleted:
                boton.set_enabled(not ocupado and self._puede_resolver())
                boton.props("loading" if ocupado else "", remove="" if ocupado else "loading")

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        if respuesta["estado"] != "ERROR":
            with self.contenedor_resultados:
                mostrar_resultados_multiples(respuesta)

    def cerrar(self) -> None:
        """Bloquea el panel desconectado y retira tareas, selección y resultados anteriores."""
        self._cerrado = True
        self.retirar_candidatos()

    def reabrir(self) -> None:
        """Permite otra exploración al reconectar sin recuperar candidatos anteriores."""
        self._cerrado = False
