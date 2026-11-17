"""Captura y publicación de intervalos candidatos para ambos métodos cerrados."""
import asyncio
import logging

from nicegui import ui

from src.frontend.componentes.candidatos_raices import PresentacionCandidatos, mostrar_candidatos
from src.frontend.componentes.captura_exploracion_raices import campos_rango
from src.frontend.componentes.exploracion_raices import ESTADO_INICIAL
from src.frontend.componentes.paso_exploracion_raices import PasoExploracion
from src.frontend.controladores.captura_exploratoria_raices import intervalo_seleccionable
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.exploracion_raices import (
    LONGITUD_CAMPO_EXPLORACION, PASO_EXPLORACION_DEFECTO, resolver_exploracion,
)
from src.frontend.controladores.metodos_cerrados.adaptadores import METODOS
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO
from src.frontend.vistas.biseccion.estado_captura import transaccion
from src.frontend.vistas.regla_falsa.vigencia_solicitud import iniciar_solicitud, revocar_solicitud

from .lote import LoteMetodosCerrados

_REGISTRO = logging.getLogger(__name__)
_PRESENTACION = PresentacionCandidatos(
    "Carga un intervalo y pulsa Calcular raíz. Si eliges un cero evaluado, el método lo comprueba al calcular.",
    "break-all", "No se detectaron candidatos en este rango. Cambia el rango o el paso.",
)


class ExploracionMetodosCerrados(PasoExploracion):
    """Busca en la malla vigente y entrega los candidatos aptos al lote."""

    def __init__(self, vista, aplicar, mostrar_detalle, *, al_editar_rango, al_buscar):
        self.vista = vista
        self._aplicar = aplicar
        self._al_editar_rango = al_editar_rango
        self._mostrar_carga = al_buscar
        self._coordinadores = {metodo: CoordinadorTrabajosRaices(resolver_exploracion) for metodo in METODOS}
        self.lote = LoteMetodosCerrados(vista, mostrar_detalle)
        self.respuesta = self.tarea = None
        self._revision = 0
        self._activa = self._cerrado = self._cargando_captura = False
        self._paso_automatico = True
        self._clave_malla = self._clave_lote = None

    @property
    def coordinador(self) -> CoordinadorTrabajosRaices:
        """Devuelve la plaza de trabajo del método activo."""
        return self._coordinadores[self.vista.capturar()["metodo"]]

    def construir_campos(self) -> None:
        """Monta rango y paso en el formulario que posee la acción de búsqueda."""
        self.minimo, self.maximo = campos_rango("rango de búsqueda", "row metodos-raices-campos w-full")
        with ui.row().classes("metodos-raices-campos w-full items-center"):
            self.paso = ui.input("Paso h", value=PASO_EXPLORACION_DEFECTO).classes("matriz-entrada min-w-0").props(
                f"inputmode=decimal maxlength={LONGITUD_CAMPO_EXPLORACION} autocomplete=off")
            ui.button("Volver a automático", color=None, on_click=self.restablecer_paso).classes("boton-discreto").props(
                "type=button ripple=false")
        self.etiqueta_paso = ui.label().classes("text-sm texto-secundario").props("aria-live=polite")
        self.paso.on_value_change(self._editar_paso)
        for campo in (self.minimo, self.maximo):
            campo.on_value_change(self._editar_rango)
        self.actualizar_paso()

    def construir_resultados(self) -> None:
        """Monta la región viva y el lote fuera del formulario de búsqueda."""
        self.estado = ui.label(ESTADO_INICIAL).classes("texto-secundario").props("role=status aria-live=polite")
        self.contenedor_resultados = ui.column().classes("w-full min-w-0 gap-4")
        self.lote.construir()

    def capturar_rango(self) -> dict:
        """Devuelve los extremos exploratorios sin alterar ni validar su borrador."""
        return {"x_min": self.minimo.value, "x_max": self.maximo.value}

    def capturar(self) -> dict:
        """Lee método, función, unidad y malla para identificar una exploración vigente."""
        captura = self.vista.capturar()
        return {"metodo": captura["metodo"], "expresion": captura["expresion"],
                "unidad_angular": captura["unidad_angular"], **self.capturar_rango(), "paso": self._capturar_paso()}

    def definir_rango(self, rango: tuple) -> None:
        """Aplica el rango de la gráfica e invalida resultados si los extremos cambiaron."""
        valores = tuple(map(str, rango))
        if valores == tuple(self.capturar_rango().values()):
            return
        with transaccion(self):
            self.minimo.set_value(valores[0])
            self.maximo.set_value(valores[1])
        self._editar_rango()

    def hay_datos(self) -> bool:
        """Indica si se editaron los extremos o se eligió un paso manual."""
        return (tuple(self.capturar_rango().values()) != tuple(map(str, RANGO_GRAFICA_DEFECTO))
                or not self._paso_automatico)

    def restablecer(self) -> None:
        """Recupera rango y paso iniciales, conservando el presupuesto del lote."""
        with transaccion(self):
            self.minimo.set_value(str(RANGO_GRAFICA_DEFECTO[0]))
            self.maximo.set_value(str(RANGO_GRAFICA_DEFECTO[1]))
            self.paso.set_value(PASO_EXPLORACION_DEFECTO)
        self.restablecer_paso()
        self._al_editar_rango()

    def establecer_activa(self, activa: bool) -> None:
        """Revoca esperas y cierra el detalle al salir, conservando respuestas ya publicadas."""
        self._activa = activa
        self.lote.establecer_activo(activa)
        if not activa and self.tarea is not None:
            revocar_solicitud(self)
            self.estado.set_text("Pulsa Buscar intervalos para iniciar otra búsqueda.")
            self._mostrar_carga(False)

    def cerrar_detalle(self) -> None:
        """Devuelve la salida al cálculo principal si algún candidato estaba abierto."""
        self.lote.cerrar_detalle()

    def invalidar(self) -> None:
        """Revoca búsqueda, candidatos y lote cuando el ejercicio deja de corresponder."""
        self._retirar_busqueda()
        self.lote.retirar_candidatos()

    def _retirar_busqueda(self) -> None:
        revocar_solicitud(self)
        self.respuesta = None
        if not self.contenedor_resultados.is_deleted:
            self.contenedor_resultados.clear()
            self.estado.set_text(ESTADO_INICIAL)
            self._mostrar_carga(False)

    def invalidar_lote(self) -> None:
        """Retira el lote por cambios de parada y conserva los candidatos de la malla."""
        self.lote.invalidar()

    def actualizar_captura(self) -> None:
        """Retira únicamente las respuestas cuya función, malla o parada cambió."""
        captura = self.vista.capturar()
        clave_malla = tuple(captura[clave] for clave in ("metodo", "expresion", "unidad_angular"))
        clave_lote = (captura["criterio"], captura["limite_iteraciones"])
        if clave_malla != self._clave_malla:
            self.invalidar()
        elif clave_lote != self._clave_lote:
            self.invalidar_lote()
        self._clave_malla, self._clave_lote = clave_malla, clave_lote

    async def buscar(self) -> None:
        """Ejecuta la búsqueda fuera de la interfaz y exige una solicitud aún vigente."""
        if not self._puede_buscar() or self.tarea is not None:
            return
        self.invalidar()
        solicitud = iniciar_solicitud(self)
        self.estado.set_text("Buscando intervalos en la función…")
        try:
            respuesta = await self.coordinador.ejecutar(solicitud.captura)
            if respuesta is not None and solicitud.corresponde(self):
                self._publicar(respuesta)
        except asyncio.CancelledError:
            return
        except Exception:
            _REGISTRO.exception("No se pudo presentar la exploración de métodos cerrados")
            if solicitud.corresponde(self):
                self.estado.set_text("No se pudo buscar. Revisa la función, el rango y el paso.")
        finally:
            if self.tarea is solicitud.tarea:
                self.tarea = None
                self._mostrar_carga(False)

    def cerrar(self) -> None:
        """Bloquea el panel y deja sin efecto publicaciones y eventos anteriores."""
        self._cerrado = True
        for coordinador in self._coordinadores.values():
            coordinador.cerrar()
        self.lote.cerrar()
        self._retirar_busqueda()

    def reabrir(self) -> None:
        """Acepta nuevas búsquedas en la captura actual si el panel sigue montado."""
        self._cerrado = self.contenedor_resultados.is_deleted
        if not self._cerrado:
            for coordinador in self._coordinadores.values():
                coordinador.reabrir()
            self.lote.reabrir()

    def _puede_buscar(self) -> bool:
        return self._activa and not self._cerrado and not self.contenedor_resultados.is_deleted and not self.vista.ocupado

    def _editar_paso(self) -> None:
        if not self._cargando_captura:
            self._paso_automatico = False
            self.actualizar_paso()
            self.invalidar()

    def _editar_rango(self) -> None:
        if not self._cargando_captura:
            self.actualizar_paso()
            self.invalidar()
            self._al_editar_rango()

    def _publicar(self, respuesta: dict) -> None:
        self.respuesta = respuesta
        self.estado.set_text(respuesta["mensaje"])
        if respuesta["estado"] == "EXITO":
            with self.contenedor_resultados:
                mostrar_candidatos(respuesta, self._seleccionar, _PRESENTACION)
            self.lote.actualizar_candidatos(respuesta)

    def _seleccionar(self, respuesta: dict, candidato: dict) -> None:
        if not self._activa:
            return
        intervalo = intervalo_seleccionable(self, respuesta, candidato)
        if intervalo is not None:
            inferior, superior = intervalo
            self._aplicar({"extremo_izquierdo": str(inferior), "extremo_derecho": str(superior),
                           "cero_preferido": candidato["abscisa"] if candidato["tipo"] == "cero_evaluado" else None})
