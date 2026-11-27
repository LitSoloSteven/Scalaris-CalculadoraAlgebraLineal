"""Gráfica única para la curva orientativa, los extremos y el procedimiento."""
import logging
from types import SimpleNamespace

from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import (
    cancelar_actualizacion,
    programar_actualizacion,
)
from src.frontend.controladores.raices.compartido.ejecucion.coordinacion_trabajos_raices import (
    CoordinadorTrabajosRaices,
)
from src.frontend.controladores.raices.compartido.exploracion.vista_previa_raices import preparar_vista_previa
from src.frontend.controladores.raices.compartido.formato.rango_exploracion_raices import (
    interpretar_relayout_x,
    rango_grafica,
)
from src.frontend.nucleo.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.vistas.raices.regla_falsa.grafica.seleccion_grafico import SeleccionGrafico
from ._figuras_cerrados import (
    calcular_encuadre,
    intervalo_desde_captura,
    montar_panel_grafica,
    preparar_figura_cerrados,
    rango_base_cerrados,
)

_MENSAJE_INICIAL = "Escribe una función para ver la gráfica. El muestreo no demuestra continuidad."
_registro = logging.getLogger(__name__)


class GraficaMetodosCerrados:
    """Conserva identidad, zoom desacoplado y curva mientras publica el resultado vigente."""

    def __init__(self, captura):
        self.captura = captura
        self.coordinador = CoordinadorTrabajosRaices(preparar_vista_previa)
        self.tarea = self.previa = self._previa_camara = self.resultado = self.fila = None
        self._solicitud = self._clave_ejercicio = self._rango_detalle = self._rango_camara = None
        self._revision = self._revision_camara = self._revision_ejercicio = 0
        self._reencuadres = self._revision_seleccion = 0
        self._puntos_borrador = []
        self._mostrando_detalle = self._inicial = self._cerrada = False
        self.respuesta = None

    def construir(self) -> None:
        """Monta el único nodo Plotly, sus acciones y su estado accesible."""
        self.ajuste, self.restablecer, self.estado, self.nodo = montar_panel_grafica(
            self.ajustar_intervalo, self.restablecer_vista, self._encuadrar_busqueda, _MENSAJE_INICIAL,
        )
        destino = SimpleNamespace(vista_previa=self, inferior=self.captura.inferior,
                                  cargar_captura=self.captura.vista.aplicar_intervalo)
        self.seleccion = SeleccionGrafico(destino)
        self.seleccion.construir()
        self.actualizar()

    @property
    def grafica(self):
        """Expone el nodo estable a la selección compartida."""
        return self.nodo

    @property
    def identidad(self) -> str:
        """Identifica la vigencia de la curva frente a cambios de ejercicio o selección."""
        return f"{self._revision_ejercicio}:{self._revision_seleccion}"

    def actualizar(self) -> None:
        """Revoca la curva solo si cambia la función, la unidad o el rango base de muestreo."""
        if not self.disponible():
            return
        solicitud = self._captura_rango()
        clave_ejercicio = (solicitud.get("expresion"), solicitud.get("unidad_angular"))
        if clave_ejercicio != self._clave_ejercicio:
            self._clave_ejercicio = clave_ejercicio
            self._revision_ejercicio += 1
        if solicitud != self._solicitud:
            self._solicitud = solicitud
            self._revision += 1
            self._rango_camara = self._previa_camara = self.previa = None
            self._programar_muestreo(solicitud, es_camara=False)
        self._dibujar()

    def _programar_muestreo(self, solicitud: dict, *, es_camara: bool) -> None:
        self._revision_camara += 1
        revision = self._revision_camara
        self.coordinador.invalidar()
        cancelar_actualizacion(self.tarea)
        self.tarea = None
        if not str(solicitud.get("expresion") or "").strip():
            self.estado.set_text(_MENSAJE_INICIAL)
            if es_camara:
                self._dibujar()
            return
        self.estado.set_text("Actualizando la gráfica…" if es_camara else "Preparando la gráfica…")
        self.tarea = programar_actualizacion(
            None, lambda: self._ejecutar_muestreo(solicitud, revision, es_camara=es_camara),
            self.disponible, ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS,
        )

    def mostrar(self, resultado: dict | None, fila: dict | None = None, *, inicial: bool = False) -> None:
        """Representa un resultado o devuelve los marcadores a la captura."""
        detalle = resultado is not None and self.captura.vista.candidato_activo is not None
        if self._mostrando_detalle != detalle:
            self.cancelar_seleccion()
        if self._mostrando_detalle and not detalle:
            self._rango_detalle = None
            self._reencuadres += 1
        if resultado is not self.resultado:
            self._rango_camara = self._previa_camara = None
        self._mostrando_detalle = detalle
        self.resultado, self.fila, self._inicial = resultado, fila, inicial
        self._dibujar()

    def ajustar_intervalo(self) -> None:
        """Encuadra los extremos visibles sin alterarlos ni ejecutar otra resolución."""
        rango = self._intervalo_visible()
        if rango is not None:
            self._rango_camara = self._previa_camara = None
            self._reencuadres += 1
            if self._mostrando_detalle:
                self._rango_detalle = rango
                self._dibujar()
            else:
                self.captura.definir_rango(rango)

    def restablecer_vista(self) -> None:
        """Recupera el encuadre base sin modificar la función, el intervalo ni los resultados."""
        self._rango_camara = self._previa_camara = None
        self._revision_camara += 1
        self._reencuadres += 1
        if self.previa is not None:
            self.estado.set_text(self.previa["mensaje"])
        self._dibujar()

    def _intervalo_visible(self) -> tuple[float, float] | None:
        if self._mostrando_detalle:
            entrada = self.resultado["resultado"].get("entrada")
            return intervalo_desde_captura(entrada) if entrada else None
        return intervalo_desde_captura(self.captura.capturar())

    def cancelar_seleccion(self) -> None:
        """Invalida clics y descarta los extremos del borrador antes de cambiar de contexto."""
        self._revision_seleccion += 1
        self.seleccion.cancelar()

    def editar_rango_busqueda(self) -> None:
        """Actualiza el muestreo cuando cambia el rango del modo exploratorio."""
        if self.disponible() and self.captura.vista.en_busqueda:
            self.cancelar_seleccion()
            self._rango_camara = self._previa_camara = None
            try:
                self.captura.definir_rango(rango_grafica(self._captura_rango()), sincronizar=False)
            except ValueError:
                pass
            self.actualizar()

    def dibujar_borrador(self, puntos: list[float]) -> None:
        """Actualiza las marcas editables dentro del único nodo Plotly."""
        self._puntos_borrador = puntos
        self._dibujar()

    def cerrar(self) -> None:
        """Revoca un muestreo en curso e impide publicar en un cliente desmontado."""
        self._cerrada = True
        self.coordinador.cerrar()
        cancelar_actualizacion(self.tarea)
        self._solicitud = None

    def reabrir(self) -> None:
        """Recupera la curva para la captura vigente después de reconectar."""
        self._cerrada = False
        self.coordinador.reabrir()
        self.actualizar()

    def disponible(self) -> bool:
        """Indica si la gráfica sigue montada y admite eventos."""
        return not self._cerrada and not self.nodo.is_deleted

    async def _ejecutar_muestreo(self, solicitud: dict, revision: int, *, es_camara: bool) -> None:
        try:
            previa = await self.coordinador.ejecutar(solicitud)
        except Exception:
            _registro.exception("No se pudo preparar la gráfica de métodos cerrados")
            previa = {"mensaje": "No se pudo dibujar la función. Revisa la expresión y el rango."}
        if previa is None or not self.disponible() or self._revision_camara != revision:
            return
        if es_camara:
            self._previa_camara = previa
        else:
            self.previa = previa
        self.estado.set_text(previa["mensaje"])
        self._dibujar()

    def _dibujar(self) -> None:
        if not self.disponible():
            return
        self.ajuste.set_enabled(self._intervalo_visible() is not None)
        rango, muestra = calcular_encuadre(
            self._captura_rango(), self.resultado,
            (self.previa, self._previa_camara), (self._rango_camara, self._rango_detalle),
        )
        figura, respuesta = preparar_figura_cerrados(self.resultado, self.fila, muestra, {
            "inicial": self._inicial, "captura": self.captura.capturar(), "identidad": self.identidad,
            "uirevision": f"{self._revision}:{self._reencuadres}", "puntos_borrador": self._puntos_borrador,
            "rango": rango,
        })
        self.respuesta = respuesta
        self.nodo.update_figure(figura)

    def _captura_rango(self) -> dict:
        captura = self.captura.captura_grafica()
        if self.captura.vista.en_busqueda:
            captura.update(self.captura.vista.exploracion.capturar_rango())
        return captura

    def _encuadrar_busqueda(self, evento) -> None:
        datos = getattr(evento, "args", None)
        if not self.disponible() or not isinstance(datos, dict) or datos.get("identidad") != self.identidad:
            return
        rango_base = rango_base_cerrados(self._captura_rango(), self.resultado, self._rango_detalle)
        relayout = interpretar_relayout_x(datos, rango_base)
        if relayout is None:
            return
        if relayout["tipo"] == "invalido":
            self.estado.set_text(relayout["mensaje"])
        elif relayout["tipo"] == "restablecer":
            self.restablecer_vista()
        elif relayout["rango"] != (self._rango_camara or rango_base):
            self._rango_camara = relayout["rango"]
            self._programar_muestreo({**self._captura_rango(), "x_min": self._rango_camara[0], "x_max": self._rango_camara[1]}, es_camara=True)
