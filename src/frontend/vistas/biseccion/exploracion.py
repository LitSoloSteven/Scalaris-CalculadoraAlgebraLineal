"""Panel de exploración independiente con cancelación y selección de respuestas vigentes."""
import asyncio
import logging

from nicegui import ui

from src.frontend.controladores.biseccion.vigencia_panel import invalidar_panel
from src.frontend.controladores.biseccion.exploracion import (
    LONGITUD_CAMPO_EXPLORACION, resolver_exploracion,
)
from src.frontend.controladores.captura_exploratoria_raices import capturar_exploracion, intervalo_seleccionable
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente
from src.frontend.componentes.exploracion_raices import ESTADO_INICIAL, MontajeExploracion, construir_exploracion
from src.frontend.componentes.paso_exploracion_raices import PasoExploracion
from .acciones_captura import desplegable
from .candidatos import mostrar_candidatos
from .modos_captura import MODO_BUSQUEDA
from .movimiento import animar_entrada, cancelar_entrada, modalidad_puntero, vincular_envio
from .rango_grafica import campos_rango

registro = logging.getLogger(__name__)
_ESTADO_INICIAL = ESTADO_INICIAL


class PanelExploracion(PasoExploracion):
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
        construir_exploracion(self, MontajeExploracion(
            campos_rango, desplegable, vincular_envio, "biseccion-panel-exploracion", "biseccion-candidatos",
            self._enviar_desde_boton, self._campos_captura, self._editar_rango, self._campo,
        ))

    async def _enviar_desde_boton(self, evento) -> None:
        await self.enviar_busqueda(puntero=modalidad_puntero(evento) is True)

    async def enviar_busqueda(self, *, puntero: bool = False) -> None:
        """Busca desde los controles solo cuando Buscar intervalo está activo."""
        if self.vista.modos.value == MODO_BUSQUEDA:
            await self.explorar(puntero=puntero)

    def _editar_rango(self) -> None:
        if not self.vista._cargando_captura:
            self._paso_automatico = False
            self.invalidar()
            self.actualizar_paso()

    def _campo(self, etiqueta: str, valor: str = ""):
        return ui.input(etiqueta, value=valor).classes("w-full matriz-entrada").props(
            f"inputmode=decimal maxlength={LONGITUD_CAMPO_EXPLORACION} autocomplete=off")

    def _campos_captura(self) -> tuple:
        return self.minimo, self.maximo, self.paso

    def capturar(self) -> dict:
        """Entrega función y rango sin exigir un criterio de parada válido."""
        return capturar_exploracion(self)

    def invalidar(self) -> None:
        """Cancela la espera y retira acciones antiguas sin tocar el resultado matemático."""
        if self.respuesta is not None:
            cancelar_entrada(self.contenedor_resultados)
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

    async def explorar(self, *, puntero: bool = False) -> None:
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
                self._publicar(vigente[0], puntero=puntero)
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

    def _publicar(self, respuesta: dict, *, puntero: bool = False) -> None:
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
        if respuesta["estado"] == "EXITO" and respuesta["candidatos"]:
            animar_entrada(self.contenedor_resultados, puntero)

    def seleccionar(self, respuesta: dict, candidato: dict) -> None:
        """Carga un intervalo apto actual y deja el cálculo posterior a una acción explícita."""
        intervalo = intervalo_seleccionable(self, respuesta, candidato)
        if intervalo is None:
            return
        inferior, superior = intervalo
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
