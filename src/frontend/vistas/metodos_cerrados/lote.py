"""Selección y vigencia de lotes de Bisección y Regla falsa."""
import asyncio
from functools import partial
import logging

from nicegui import ui

from src.backend.resolutores.raices.biseccion.lote.limites_resolucion_multiple import (
    MAXIMO_CANDIDATOS_MULTIPLE, MAXIMO_EVALUACIONES_MULTIPLE,
)
from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos
from src.frontend.controladores.raices.biseccion.ejecucion.resolucion_multiple import resolver_lote as resolver_biseccion
from src.frontend.controladores.raices.compartido.ejecucion.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.raices.compartido.exploracion.exploracion_raices import LONGITUD_CAMPO_EXPLORACION, presentar_candidato
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA, captura_del_metodo
from src.frontend.controladores.raices.regla_falsa.ejecucion.resolucion_multiple import resolver_lote as resolver_regla_falsa
from src.frontend.vistas.raices.biseccion.procedimiento.modo_examen import crear_control_examen_lote
from src.frontend.vistas.regla_falsa.vigencia_solicitud import SolicitudPanel, iniciar_solicitud, revocar_solicitud

from .resultados_lote import datos_detalle, mostrar_lote

_REGISTRO = logging.getLogger(__name__)
_ESTADO_INICIAL = "Busca intervalos para habilitar candidatos aptos."


class LoteMetodosCerrados:
    """Vincula el lote a una selección vigente y evita duplicar el resultado individual."""

    def __init__(self, vista, mostrar_detalle):
        self.vista = vista
        self._mostrar_detalle = mostrar_detalle
        self._coordinadores = {
            BISECCION: CoordinadorTrabajosRaices(resolver_biseccion),
            REGLA_FALSA: CoordinadorTrabajosRaices(resolver_regla_falsa),
        }
        self.respuesta = self.tarea = None
        self._candidatos = {}
        self._fuente = None
        self._activo = self._cerrado = self._todos = False
        self._revision = 0
        self._detalle = self._foco = self._boton_volver = None

    @property
    def coordinador(self) -> CoordinadorTrabajosRaices:
        """Devuelve la plaza de resolución del método seleccionado."""
        return self._coordinadores[self.vista.capturar()["metodo"]]

    @property
    def modo_examen(self) -> bool:
        """Devuelve la preferencia del lote de Bisección."""
        return self.control_examen.value

    @modo_examen.setter
    def modo_examen(self, activo: bool) -> None:
        """Sincroniza el modo examen del detalle con la preferencia del lote."""
        self.control_examen.set_value(activo)

    def construir(self) -> None:
        """Monta las dos configuraciones de selección y un destino para respuestas de lote."""
        with ui.column().classes("w-full min-w-0 gap-3").bind_visibility_from(self, "_fuente", backward=bool):
            ui.label("Resolver candidatos").classes("text-lg font-semibold texto-principal")
            ui.label(f"Se aplica el criterio actual. Puedes resolver hasta {MAXIMO_CANDIDATOS_MULTIPLE} candidatos.").classes(
                "text-sm texto-secundario")
            _montar_controles(self)
            self.estado = ui.label(_ESTADO_INICIAL).classes("texto-secundario").props("role=status aria-live=polite")
            self.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-3")
        self._mostrar_carga(False)

    def actualizar_candidatos(self, fuente: dict) -> None:
        """Conserva numéricamente las posiciones originales del escaneo y monta su selección."""
        self.retirar_candidatos()
        self._fuente = fuente
        self._candidatos = {
            f"candidato-{indice}": candidato for indice, candidato in enumerate(fuente["candidatos"], 1)
            if presentar_candidato(candidato)["seleccionable"]
        }
        opciones = {clave: f"{clave} · {presentar_candidato(candidato)['intervalo']}"
                    for clave, candidato in self._candidatos.items()}
        self.selector_uno.set_options(opciones, value=next(iter(opciones), None))
        self.selector_multiple.set_options(opciones, value=[])
        self.estado.set_text(_orientacion(self))
        self._mostrar_carga(False)

    def retirar_candidatos(self) -> None:
        """Revoca la fuente, las acciones y los resultados dependientes del escaneo."""
        self._fuente = None
        self._candidatos = {}
        if not self.contenedor_resultados.is_deleted:
            self.selector_uno.set_options({}, value=None)
            self.selector_multiple.set_options({}, value=[])
        self.invalidar()

    def invalidar(self) -> None:
        """Revoca publicación y detalle por cambios relevantes a la resolución."""
        revocar_solicitud(self)
        self.respuesta = None
        self.cerrar_detalle()
        self._boton_volver = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text(_orientacion(self))
            self._mostrar_carga(False)

    def establecer_activo(self, activo: bool) -> None:
        """Cancela esperas al ocultar el lote y conserva los registros ya publicados."""
        self._activo = activo
        if not activo:
            self.cerrar_detalle()
            if self.tarea is not None:
                revocar_solicitud(self)
                self.estado.set_text(_orientacion(self))
        self._mostrar_carga(self.tarea is not None)

    def capturar(self) -> dict:
        """Produce la configuración del controlador y los registros seleccionados."""
        ejercicio = self.vista.capturar()
        configuracion = captura_del_metodo(ejercicio)
        for clave in ("extremo_izquierdo", "extremo_derecho", "cero_preferido"):
            configuracion.pop(clave, None)
        seleccion = self._seleccion(ejercicio["metodo"], self._todos)
        return {"metodo": ejercicio["metodo"], "configuracion": configuracion,
                "unidad_angular": ejercicio["unidad_angular"], "presupuesto_evaluaciones": self.presupuesto.value,
                "candidatos": tuple({"identificador": clave, "candidato": candidato}
                                    for clave, candidato in self._candidatos.items() if clave in seleccion)}

    def cerrar_detalle(self) -> None:
        """Retira un candidato activo y restaura la presentación principal."""
        if self._detalle is not None:
            self._detalle = self._foco = None
            if not self.control_examen.is_deleted:
                self.control_examen.set_visibility(True)
            if self._boton_volver is not None and not self._boton_volver.is_deleted:
                self._boton_volver.set_visibility(False)
                if self.respuesta is not None:
                    self.estado.set_text(self.respuesta["mensaje"])
            self._mostrar_detalle(None, None)

    def cerrar(self) -> None:
        """Revoca los trabajos y bloquea publicaciones del lote en el cliente desconectado."""
        self._cerrado = True
        for coordinador in self._coordinadores.values():
            coordinador.cerrar()
        self.retirar_candidatos()

    def reabrir(self) -> None:
        """Admite solicitudes posteriores si el destino todavía está montado."""
        self._cerrado = self.contenedor_resultados.is_deleted
        if not self._cerrado:
            for coordinador in self._coordinadores.values():
                coordinador.reabrir()

    def _seleccion(self, metodo: str, todos: bool):
        if metodo != BISECCION:
            return self.selector_multiple.value or ()
        return self._candidatos if todos else (self.selector_uno.value,)

    async def _resolver(self, biseccion: bool, todos: bool) -> None:
        metodo = self.vista.capturar()["metodo"]
        if biseccion != (metodo == BISECCION) or not self._puede_resolver(metodo, todos):
            return
        if self.tarea is not None or self.vista.ocupado:
            return
        self.invalidar()
        self._todos = todos
        solicitud = iniciar_solicitud(self)
        self.estado.set_text("Resolviendo candidatos con el criterio actual…")
        await self._ejecutar_solicitud(solicitud, metodo)

    async def _ejecutar_solicitud(self, solicitud: SolicitudPanel, metodo: str) -> None:
        try:
            respuesta = await self.coordinador.ejecutar(solicitud.captura)
            if respuesta is not None and solicitud.corresponde(self):
                self._publicar(respuesta, metodo)
        except asyncio.CancelledError:
            return
        except Exception:
            _REGISTRO.exception("No se pudo presentar el lote de métodos cerrados")
            if solicitud.corresponde(self):
                self.estado.set_text("No se pudo completar el lote. Revisa los datos y vuelve a resolver.")
        finally:
            if self.tarea is solicitud.tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _puede_resolver(self, metodo: str, todos: bool) -> bool:
        if not self._activo or self._cerrado or not self._candidatos or self.contenedor_resultados.is_deleted:
            return False
        seleccion = self._seleccion(metodo, todos)
        return 1 <= len(seleccion) <= MAXIMO_CANDIDATOS_MULTIPLE and all(
            clave in self._candidatos for clave in seleccion)

    def _mostrar_carga(self, ocupado: bool) -> None:
        if not self.contenedor_resultados.is_deleted:
            _configurar_controles(self, ocupado)

    def _publicar(self, respuesta: dict, metodo: str) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        if respuesta["estado"] != "ERROR":
            intervalos = {clave: presentar_candidato(candidato)["intervalo"] for clave, candidato in self._candidatos.items()}
            with self.contenedor_resultados:
                self._boton_volver = mostrar_lote(respuesta, metodo, intervalos, self._abrir, self._volver)

    def _abrir(self, lote: dict, metodo: str, registro: dict, boton) -> None:
        if not self._activo or self._cerrado or self.vista.ocupado or lote is not self.respuesta or boton.is_deleted:
            return
        datos = datos_detalle(registro, metodo)
        if datos is not None:
            self._detalle, self._foco = registro["identificador"], boton
            self.control_examen.set_visibility(False)
            self._boton_volver.set_visibility(True)
            self._mostrar_detalle(datos, self._detalle)
            self.estado.set_text(f"Detalle de {self._detalle} disponible.")
            _enfocar(self._boton_volver)

    def _volver(self, lote: dict) -> None:
        if self._activo and not self._cerrado and lote is self.respuesta:
            boton = self._foco
            self.cerrar_detalle()
            if boton is not None and not boton.is_deleted:
                _enfocar(boton)


def _montar_controles(lote: LoteMetodosCerrados) -> None:
    with ui.column().classes("w-full") as lote.campos_biseccion:
        lote.selector_uno = ui.select({}, label="Candidato para resolver").classes("w-full matriz-entrada")
        lote.control_examen = crear_control_examen_lote()
        with ui.row().classes("w-full gap-3"):
            lote.boton_uno = _boton("Resolver candidato", partial(lote._resolver, True, False))
            lote.boton_todos = _boton("Resolver todos", partial(lote._resolver, True, True))
    with ui.column().classes("w-full") as lote.campos_regla_falsa:
        lote.selector_multiple = ui.select({}, value=[], multiple=True, label="Candidatos del lote").classes(
            "w-full matriz-entrada").props(f":max-values={MAXIMO_CANDIDATOS_MULTIPLE}")
        lote.presupuesto = ui.input("Presupuesto de evaluaciones", value=str(MAXIMO_EVALUACIONES_MULTIPLE)).classes(
            "w-full matriz-entrada").props(f"inputmode=numeric maxlength={LONGITUD_CAMPO_EXPLORACION}")
        habilitar_simbolos(lote.presupuesto, "entero")
        lote.boton_seleccion = _boton("Resolver selección", partial(lote._resolver, False, False))
    for campo in (lote.selector_uno, lote.selector_multiple, lote.presupuesto):
        campo.on_value_change(lote.invalidar)


def _configurar_controles(lote: LoteMetodosCerrados, ocupado: bool) -> None:
    metodo = lote.vista.capturar()["metodo"]
    biseccion = metodo == BISECCION
    lote.campos_biseccion.set_visibility(biseccion)
    lote.campos_regla_falsa.set_visibility(not biseccion)
    lote.boton_todos.set_visibility(2 <= len(lote._candidatos) <= MAXIMO_CANDIDATOS_MULTIPLE)
    for boton, todos in ((lote.boton_uno, False), (lote.boton_todos, True), (lote.boton_seleccion, False)):
        boton.set_enabled(not ocupado and lote._puede_resolver(metodo, todos))
        boton.props("loading" if ocupado else "", remove="" if ocupado else "loading")


def _enfocar(boton) -> None:
    boton.client.run_javascript(f"document.getElementById('{boton.html_id}')?.focus()")


def _boton(etiqueta: str, accion) -> ui.button:
    return ui.button(etiqueta, color=None, on_click=accion).classes("boton-discreto").props("ripple=false")


def _orientacion(lote: LoteMetodosCerrados) -> str:
    if lote._fuente is None:
        return _ESTADO_INICIAL
    if not lote._candidatos:
        return "La malla no contiene intervalos aptos. Ajusta el rango o el paso."
    if lote.vista.capturar()["metodo"] == BISECCION and len(lote._candidatos) > MAXIMO_CANDIDATOS_MULTIPLE:
        return f"Hay más de {MAXIMO_CANDIDATOS_MULTIPLE} candidatos aptos. Elige uno o reduce el rango."
    return "Elige los candidatos que quieres resolver."
