"""Búsqueda acotada por cliente con descarte de respuestas y acciones antiguas."""
import asyncio
import logging

from nicegui import ui

from src.ai.huellas import calcular_huella
from src.backend.resolutores.raices.unidades_angulares import opciones_unidad
from src.frontend.componentes.captura_exploracion_raices import campos_rango
from src.frontend.componentes.exploracion_raices import ESTADO_INICIAL, MontajeExploracion, construir_exploracion
from src.frontend.componentes.paso_exploracion_raices import PasoExploracion
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.exploracion_raices import (
    LONGITUD_CAMPO_EXPLORACION, PASO_EXPLORACION_DEFECTO, resolver_exploracion,
)
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO
from src.frontend.vistas.biseccion.acciones_captura import desplegable
from src.frontend.vistas.biseccion.estado_captura import transaccion
from .modos_captura import MODO_BUSQUEDA
from .seleccion_candidato import presentar_candidatos, seleccionar_candidato

_registro = logging.getLogger(__name__)


class PanelExploracion(PasoExploracion):
    """Mantiene una plaza real de exploración y un único borrador reemplazable."""

    def __init__(self, vista):
        self.vista = vista
        self.coordinador = CoordinadorTrabajosRaices(resolver_exploracion)
        self.respuesta = self.tarea = None
        self._revision = 0
        self._cerrado = False
        self._paso_automatico = True

    def construir(self) -> None:
        """Reutiliza campos y candidatos neutrales con acciones propias de regla falsa."""
        construir_exploracion(self, MontajeExploracion(
            self._rango, desplegable, self._vincular_envio, "regla-falsa-exploracion",
            "regla-falsa-candidatos", self.enviar_busqueda, self._campos_captura,
            self._editar_paso, self._campo,
        ))
        for campo in (self.minimo, self.maximo):
            campo.on_value_change(self._editar_rango)

    def _rango(self, contexto: str) -> tuple:
        return campos_rango(contexto, "regla-falsa-campos")

    def _vincular_envio(self, boton, accion) -> None:
        boton.on_click(accion)

    def _campo(self, etiqueta: str, valor: str = ""):
        return ui.input(etiqueta, value=valor).classes("w-full matriz-entrada").props(
            f"inputmode=decimal maxlength={LONGITUD_CAMPO_EXPLORACION} autocomplete=off")

    def _campos_captura(self) -> tuple:
        return self.minimo, self.maximo, self.paso

    def _editar_paso(self) -> None:
        if not self.vista._cargando_captura:
            self._paso_automatico = False
            self._editar_rango()

    def _editar_rango(self) -> None:
        if not self.vista._cargando_captura:
            self.invalidar()
            self.actualizar_paso()

    def capturar(self) -> dict:
        """Entrega solo función, unidad, rango y paso; no consulta extremos ni parada."""
        return {"expresion": self.vista.expresion.value, "x_min": self.minimo.value,
                "x_max": self.maximo.value, "paso": self._capturar_paso(),
                **opciones_unidad(self.vista.unidad_angular.value)}

    async def enviar_busqueda(self) -> None:
        """Atiende Enter y el botón únicamente en la tarea de búsqueda."""
        if self.vista.modos.value == MODO_BUSQUEDA:
            await self.explorar()

    def invalidar(self) -> None:
        """Retira acciones y espera antigua conservando la plaza hasta el cierre real."""
        self._revision += 1
        self.coordinador.invalidar()
        if self.tarea is not None:
            self.tarea.cancel()
            self.tarea = None
        self.respuesta = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text("Datos editados. Explora para obtener candidatos vigentes.")
            self._mostrar_carga(False)

    async def explorar(self) -> None:
        """Ejecuta el dominio fuera de UI y publica solo captura y destino vigentes."""
        if self._cerrado or self.contenedor_resultados.is_deleted:
            return
        self.invalidar()
        tarea = self.tarea = asyncio.current_task()
        revision, destino = self._revision, self.contenedor_resultados
        captura = self.capturar()
        huella = calcular_huella(captura)
        self._mostrar_carga(True)
        self.estado.set_text("Explorando la malla de la función…")
        try:
            respuesta = await self.coordinador.ejecutar(captura)
            if respuesta is not None and self._sigue_vigente(revision, destino, huella):
                self._publicar(respuesta)
        except asyncio.CancelledError:
            return
        except Exception:
            _registro.exception("No se pudo presentar la exploración de regla falsa")
            if revision == self._revision and not self.estado.is_deleted:
                self.estado.set_text("No se pudo completar la exploración. Revisa la función y vuelve a intentarlo.")
        finally:
            if self.tarea is tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def _sigue_vigente(self, revision: int, destino, huella: str) -> bool:
        return (revision == self._revision and not self._cerrado
                and destino is self.contenedor_resultados and not destino.is_deleted
                and huella == calcular_huella(self.capturar()))

    def _mostrar_carga(self, ocupado: bool) -> None:
        if not self.boton.is_deleted:
            self.boton.set_enabled(not ocupado)
            self.boton.props("loading" if ocupado else "", remove="" if ocupado else "loading")

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        with self.contenedor_resultados:
            if respuesta["estado"] == "EXITO":
                presentar_candidatos(self, respuesta)
            else:
                ui.label(respuesta["mensaje"]).classes("texto-secundario")

    def seleccionar(self, respuesta: dict, candidato: dict) -> None:
        """Delega la carga transaccional de un candidato actual, sin resolver."""
        seleccionar_candidato(self, respuesta, candidato)

    def restablecer(self) -> None:
        """Restaura rango y paso iniciales conservando las preferencias de cálculo."""
        with transaccion(self.vista):
            for campo, valor in zip((self.minimo, self.maximo), RANGO_GRAFICA_DEFECTO):
                campo.set_value(str(valor))
            self.paso.set_value(PASO_EXPLORACION_DEFECTO)
        self.restablecer_paso()
        self.estado.set_text(ESTADO_INICIAL)

    def hay_datos(self) -> bool:
        """Indica si la limpieza retiraría un rango o paso editado."""
        return ((self.minimo.value, self.maximo.value) != tuple(map(str, RANGO_GRAFICA_DEFECTO))
                or self.paso.value != PASO_EXPLORACION_DEFECTO or not self._paso_automatico)

    def cerrar(self) -> None:
        """Revoca publicaciones y borra pendientes al desconectar o eliminar el cliente."""
        self._cerrado = True
        self.coordinador.cerrar()
        self.invalidar()

    def reabrir(self) -> None:
        """Admite nuevas solicitudes sin recuperar respuestas anteriores a la desconexión."""
        self._cerrado = self.contenedor_resultados.is_deleted
        if not self._cerrado:
            self.coordinador.reabrir()
