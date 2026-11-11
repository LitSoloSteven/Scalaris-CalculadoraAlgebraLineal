"""Selección de candidatos y coordinación cancelable de una única solicitud de lote."""
import asyncio
import logging

from nicegui import ui

from src.backend.resolutores.raices.limites_resolucion_multiple import MAXIMO_CANDIDATOS_MULTIPLE, MAXIMO_EVALUACIONES_MULTIPLE
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.exploracion_raices import LONGITUD_CAMPO_EXPLORACION, presentar_candidato
from src.frontend.controladores.regla_falsa.resolucion_multiple import resolver_lote
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from .detalle_resultado import presentar_detalle
from .modos_captura import MODO_BUSQUEDA
from .resultados_multiples import mostrar_resultados_multiples
from .vigencia_solicitud import iniciar_solicitud, revocar_solicitud

_registro = logging.getLogger(__name__)
_ESTADO_INICIAL = "Explora y selecciona candidatos para resolver un lote."
_ESTADO_ELEGIR = "Selecciona los candidatos que quieres resolver."
_ESTADO_SIN_APTOS = "Esta malla no contiene cruces ni ceros aptos. Ajusta el rango o el paso."


class PanelResolucionMultiple:
    """Mantiene selección, trabajo y detalle vigentes sin liberar la plaza al cancelar la espera."""

    def __init__(self, vista):
        self.vista = vista
        self.coordinador = CoordinadorTrabajosRaices(resolver_lote)
        self.respuesta = self.tarea = self._fuente = self.activo = None
        self.candidatos = {}
        self._revision = 0
        self._cerrado = False

    def construir(self) -> None:
        """Monta selección explícita y presupuesto acotado por los límites del dominio."""
        with ui.column().classes("w-full min-w-0 gap-3"):
            ui.label("Resolver varios candidatos").classes("text-lg font-semibold texto-principal")
            ui.label(f"Selecciona hasta {MAXIMO_CANDIDATOS_MULTIPLE} candidatos. Se aplica el criterio y el límite actuales.").classes(
                "text-sm texto-secundario")
            self.contenedor_selector = ui.column().classes("w-full min-w-0")
            self._montar_selector({})
            self.presupuesto = ui.input("Presupuesto de evaluaciones", value=str(MAXIMO_EVALUACIONES_MULTIPLE)).classes(
                "w-full matriz-entrada").props(f"inputmode=numeric maxlength={LONGITUD_CAMPO_EXPLORACION}")
            self.boton = ui.button("Resolver selección", color=None, on_click=self.resolver).classes("boton-discreto").props("ripple=false")
            self.estado = ui.label(_ESTADO_INICIAL).classes("texto-secundario").props(
                "role=status aria-live=polite aria-atomic=true")
            self.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-3")
        self.presupuesto.on_value_change(self.invalidar)
        self._mostrar_carga(False)

    def _montar_selector(self, opciones: dict) -> None:
        self.contenedor_selector.clear()
        with self.contenedor_selector:
            selector = self.selector = ui.select(opciones, value=[], multiple=True, label="Candidatos del lote").classes(
                "w-full matriz-entrada").props(f":max-values={MAXIMO_CANDIDATOS_MULTIPLE}")
        selector.set_enabled(bool(opciones))
        selector.on_value_change(lambda: self.invalidar() if self.selector is selector else None)

    def actualizar_candidatos(self, fuente: dict) -> None:
        """Asocia identificadores a las posiciones originales del escaneo y exige elegir de nuevo."""
        self.retirar_candidatos()
        self._fuente = fuente
        self.candidatos = {f"candidato-{indice}": candidato for indice, candidato in enumerate(fuente["candidatos"], 1)
                           if presentar_candidato(candidato)["seleccionable"]}
        opciones = {clave: f"{clave} · {presentar_candidato(candidato)['intervalo']}" for clave, candidato in self.candidatos.items()}
        self._montar_selector(opciones)
        self.estado.set_text(self._orientar())

    def retirar_candidatos(self) -> None:
        """Revoca la fuente, la selección y los resultados de un escaneo retirado."""
        self.invalidar()
        self._fuente = None
        self.candidatos = {}
        if not self.contenedor_selector.is_deleted:
            if self.selector.enabled:
                self._montar_selector({})
            self.estado.set_text(self._orientar())
            self._mostrar_carga(False)

    def invalidar(self) -> None:
        """Retira publicación y detalle conservando el trabajador real hasta que termine."""
        revocar_solicitud(self)
        activo, self.activo = self.activo, None
        if activo is not None:
            self.vista._retirar_resultado()
            if not self.vista._cerrada:
                self.vista.continuidad.programar()
            if not self.vista.estado.is_deleted:
                self.vista.estado.set_text("El detalle del lote dejó de estar vigente. Resuelve de nuevo.")
        self.respuesta = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text(self._orientar())
            self._mostrar_carga(False)

    def _orientar(self) -> str:
        if self._fuente is None:
            return _ESTADO_INICIAL
        if not self.candidatos:
            return _ESTADO_SIN_APTOS
        return "Resuelve la selección para obtener resultados vigentes." if self.selector.value else _ESTADO_ELEGIR

    def capturar(self) -> dict:
        """Lee configuración común y selección en el orden estable del escaneo actual."""
        configuracion = self.vista.capturar()
        for clave in ("extremo_izquierdo", "extremo_derecho", "cero_preferido"):
            configuracion.pop(clave, None)
        seleccion = self.selector.value or []
        return {"configuracion": configuracion, "presupuesto_evaluaciones": self.presupuesto.value,
                "candidatos": tuple({"identificador": clave, "candidato": candidato}
                                    for clave, candidato in self.candidatos.items() if clave in seleccion)}

    async def resolver(self) -> None:
        """Publica una sola respuesta B3 si fuente, revisión, captura y destino siguen vigentes."""
        if not self._puede_resolver() or self.tarea is not None or self.vista.ocupado:
            return
        self.invalidar()
        solicitud = iniciar_solicitud(self)
        self.estado.set_text("Resolviendo la selección por regla falsa…")
        try:
            respuesta = await self.coordinador.ejecutar(solicitud.captura)
            if respuesta is not None and self._puede_resolver() and solicitud.corresponde(self):
                self._publicar(respuesta)
        except asyncio.CancelledError:
            return
        except Exception:
            _registro.exception("No se pudo presentar el lote de regla falsa")
            if self._puede_resolver() and solicitud.corresponde(self):
                self.respuesta = None
                solicitud.destino.clear()
                self.estado.set_text("No se pudo completar el lote. Revisa los datos y vuelve a resolver.")
        finally:
            if self.tarea is solicitud.tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _puede_resolver(self) -> bool:
        return (not self._cerrado and not self.contenedor_resultados.is_deleted
                and self.vista.modos.value == MODO_BUSQUEDA and bool(self.candidatos)
                and self._fuente is self.vista.exploracion.respuesta
                and 1 <= len(self.selector.value or []) <= MAXIMO_CANDIDATOS_MULTIPLE)

    def _mostrar_carga(self, ocupado: bool) -> None:
        if not self.boton.is_deleted:
            self.boton.set_enabled(not ocupado and self._puede_resolver())
            self.boton.props("loading" if ocupado else "", remove="" if ocupado else "loading")

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        if respuesta["estado"] != "ERROR":
            with self.contenedor_resultados:
                mostrar_resultados_multiples(respuesta, lambda identificador: self.abrir(identificador, respuesta))

    def abrir(self, identificador: str, lote: dict) -> None:
        """Abre únicamente un registro del lote vigente y retira tabla, secante y foco anteriores."""
        if lote is not self.respuesta or not self._puede_resolver():
            return
        registro = next((actual for actual in self.respuesta["resultados"] if actual["identificador"] == identificador), None)
        if registro is None or registro["datos"] is None:
            return
        self.vista._retirar_resultado()
        self.activo = identificador
        with self.vista.contenedor_resultados, ui.element("h3").props("tabindex=-1") as titulo:
            ui.label(f"Detalle de {identificador}").classes("font-semibold texto-principal")
        presentar_detalle(self.vista, registro["datos"])
        self.vista.estado.set_text(f"Detalle de {identificador}. La tabla, secante y copia corresponden a este candidato.")
        titulo.client.run_javascript(f"document.getElementById('{titulo.html_id}')?.focus()")
        actualizar_contexto(self.vista)

    def cerrar(self) -> None:
        """Revoca selección y publicaciones al desconectar o desmontar el cliente."""
        self._cerrado = True
        self.coordinador.cerrar()
        self.retirar_candidatos()

    def reabrir(self) -> None:
        """Permite solicitudes nuevas sin recuperar resultados de otra conexión."""
        self._cerrado = self.contenedor_resultados.is_deleted
        if not self._cerrado:
            self.coordinador.reabrir()
