"""Publicación del paso vigente después de preparar su fórmula."""
import json
import logging
from asyncio import Task

from nicegui import background_tasks, ui

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.temporizacion import reiniciar_espera
from .movimiento import REGISTRAR_ENTRADA, modalidad_puntero, vincular_envio

_TOKEN_PASO = {"Rápida": "--dur-panel", "Normal": "--dur-view", "Lenta": "--dur-didactic"}
registro = logging.getLogger(__name__)


class ReproductorBiseccion(ReproductorPasos):
    """Mantiene visible el paso publicado mientras se prepara su sucesor."""

    def configurar_preparacion(self, latex_paso) -> None:
        """Recibe la proyección TeX de cada paso y crea su región de estado."""
        self.latex_paso = latex_paso
        self.revision = 0
        self.tarea_paso: Task | None = None
        self.formula_preparada = None
        self._puntero_accion = None
        self._puntero_reproduccion = None
        self._destino_paso = None
        self.estado_paso = ui.label().props("role=status aria-live=polite").classes("text-sm texto-secundario")

    def vincular_accion(self, boton, accion) -> None:
        """Captura la modalidad al activar un control, antes del viaje al servidor."""
        def _ejecutar(evento) -> None:
            self._puntero_accion = modalidad_puntero(evento)
            if boton is self.boton_reproducir:
                self._puntero_reproduccion = self._puntero_accion
            try:
                accion()
            finally:
                self._puntero_accion = None

        vincular_envio(boton, _ejecutar)

    def vincular_deslizador(self) -> None:
        """Captura el índice y su modalidad juntos antes de enviarlos."""
        def _desplazar(evento) -> None:
            if not isinstance(evento.args, list) or len(evento.args) != 2:
                return
            indice, puntero = evento.args
            if type(indice) is not int or indice == self.indice_solicitado:
                return
            self._puntero_accion = puntero is True
            try:
                self.ir_a(indice)
            finally:
                self._puntero_accion = None

        self.deslizador.on("pointerdown.capture", js_handler=REGISTRAR_ENTRADA)
        self.deslizador.on("keydown.capture", js_handler=REGISTRAR_ENTRADA)
        self.deslizador.on(
            "change", _desplazar,
            js_handler=(
                "valor => emit([valor, getHtmlElement(" + str(self.deslizador.id) +
                ").hasAttribute('data-biseccion-puntero')])"
            ),
        )

    @property
    def indice_solicitado(self) -> int:
        """Devuelve el destino pendiente para que las ráfagas acumulen avances."""
        return self.indice_actual if self._destino_paso is None else self._destino_paso

    def ir_a(self, indice: int, *, autoreproduccion: bool = False) -> None:
        """Prepara un destino interactivo o aplica inmediatamente una restauración."""
        modalidad = self._puntero_reproduccion if autoreproduccion else self._puntero_accion
        if modalidad is None or self.tarjeta is None or self.tarjeta.is_deleted:
            self._cancelar_preparacion()
            super().ir_a(indice, autoreproduccion=autoreproduccion)
            return
        destino = max(0, min(indice, len(self.pasos) - 1))
        if destino == self._destino_paso:
            return
        self._cancelar_preparacion()
        if destino == self.indice_actual:
            self._restaurar_deslizador()
            return
        self._destino_paso = destino
        self.estado_paso.set_text(f"Preparando paso {destino + 1}…")
        self.tarea_paso = background_tasks.create(
            self._preparar(destino, self.revision, modalidad, autoreproduccion))

    async def _preparar(self, destino: int, revision: int, puntero: bool, autoreproduccion: bool) -> None:
        token = _TOKEN_PASO.get(self.velocidad, _TOKEN_PASO["Normal"])
        cuerpo = self.contenedor_cuerpo.html_id
        preparado = False
        paso = self.pasos[destino]
        extremos = [paso.cuerpo["extremo_izquierdo"], paso.cuerpo["extremo_derecho"]] if puntero and paso.cuerpo else None
        datos = {"cuerpo": cuerpo, "revision": revision, "puntero": puntero, "token": token}
        try:
            solicitud = dict(datos, latex=self.latex_paso(paso), extremos=extremos)
            preparado = await self.tarjeta.client.run_javascript(
                f"window.scalaris.pasoBiseccion?.preparar({json.dumps(solicitud)})",
                timeout=6,
            )
        except TimeoutError:
            pass
        except Exception:
            registro.exception("No se pudo preparar el paso de bisección")
        if revision != self.revision or self.tarjeta.is_deleted:
            return
        with self.tarjeta:
            self._publicar_paso(destino, datos, preparado, autoreproduccion)

    def _publicar_paso(self, destino: int, datos: dict, preparado: bool, autoreproduccion: bool) -> None:
        self.tarea_paso = self._destino_paso = None
        self.estado_paso.set_text("")
        self.formula_preparada = datos if preparado else None
        super().ir_a(destino, autoreproduccion=autoreproduccion)
        self.formula_preparada = None
        if autoreproduccion and self.temporizador is not None and self.temporizador.active:
            reiniciar_espera(self)

    def _avanzar(self) -> None:
        if self.tarea_paso is None:
            super()._avanzar()

    def _seleccionar_desde_indice(self, indice: int) -> None:
        self.ir_a(indice)
        ui.run_javascript(
            f"document.getElementById({json.dumps(self.id_tarjeta)})?.scrollIntoView({{block: 'center'}})"
        )

    def _pausar_reproduccion(self) -> None:
        if self.temporizador is not None and self.temporizador.active:
            self._cancelar_preparacion()
        super()._pausar_reproduccion()

    def pausar(self) -> None:
        """Pausa el reloj y revoca el paso preparado al abandonar el procedimiento."""
        self._cancelar_preparacion()
        self._restaurar_deslizador()
        super().pausar()

    def detener(self) -> None:
        """Revoca la preparación antes de desmontar el reproductor."""
        self._cancelar_preparacion()
        super().detener()

    def _cancelar_preparacion(self) -> None:
        self.revision += 1
        if self.tarea_paso is not None:
            self.tarea_paso.cancel()
            self.tarea_paso = self._destino_paso = None
            if not self.estado_paso.is_deleted:
                self.estado_paso.set_text("")
                self.tarjeta.client.run_javascript(
                    f"window.scalaris.pasoBiseccion.descartar({json.dumps([self.contenedor_cuerpo.html_id, self.revision])})"
                )

    def _restaurar_deslizador(self) -> None:
        if self.deslizador is not None and not self.deslizador.is_deleted:
            self.deslizador.set_value(self.indice_actual)
