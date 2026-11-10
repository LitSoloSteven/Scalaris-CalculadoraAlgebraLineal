"""Borrador editable para confirmar dos extremos elegidos en el gráfico."""
from math import isfinite

from src.frontend.componentes.borrador_intervalo_raices import construir_borrador, confirmar_borrador, siguiente_extremo

from src.frontend.controladores.biseccion.captura_criterio import real_capturado
from src.frontend.controladores.seleccion_muestra_raices import puntos_borrador
from .modos_captura import MODO_BUSQUEDA


class SeleccionGrafico:
    """Permite cargar un intervalo con puntero o mediante dos campos de texto."""

    def __init__(self, vista):
        self.vista = vista
        self.activa = False

    def construir(self) -> None:
        """Monta la acción de inicio, la alternativa editable y el estado del borrador."""
        construir_borrador(self, "Marca dos puntos dentro de los ejes o escribe los extremos.", self._dibujar_borrador)

    def enlazar(self, grafico) -> None:
        """Proyecta pulsaciones del nodo estable y conserva la entrada manual como alternativa."""
        grafico.on("pointerdown", js_handler="evento => window.scalaris.graficoBiseccion?.iniciar(evento)")
        grafico.on("click", js_handler="evento => window.scalaris.graficoBiseccion?.marcar(evento)")
        grafico.on("biseccion_abscisa", self._marcar, args=["detail"])

    def iniciar(self) -> None:
        """Inicia una selección vacía y enfoca su primer extremo editable."""
        if self.vista.modos.value != MODO_BUSQUEDA:
            return
        self.activa = True
        self.vista.vista_previa.panel.classes(add="biseccion-seleccion-activa")
        for campo in self.campos:
            campo.set_value("")
        self.estado.set_text("")
        self.region.set_visibility(True)
        self.campos[0].run_method("focus")

    def _marcar(self, evento) -> None:
        if not self.activa or self.vista.modos.value != MODO_BUSQUEDA:
            return
        previa = self.vista.vista_previa.respuesta
        if not previa or previa["estado"] != "EXITO" or not isinstance(evento.args, dict):
            return
        abscisa = _abscisa_finita(evento.args.get("detail"))
        if abscisa is None:
            return
        campo = siguiente_extremo(self.campos)
        campo.set_value(str(abscisa))
        if self.campos[1].value:
            self._ordenar_extremos(abscisa)

    def _ordenar_extremos(self, abscisa: float) -> None:
        primero, segundo = self.campos
        try:
            anterior = real_capturado(primero.value, "El extremo a")
        except ValueError as error:
            self.estado.set_text(str(error))
            return
        if anterior > abscisa:
            valor = primero.value
            primero.set_value(segundo.value)
            segundo.set_value(valor)

    def _dibujar_borrador(self) -> None:
        if not self.activa:
            return
        puntos = puntos_borrador(tuple(campo.value for campo in self.campos))
        self.vista.vista_previa.compartido.borrador(puntos)

    def confirmar(self) -> None:
        """Valida el borrador y carga ambos extremos sin iniciar un cálculo."""
        if not self.activa or self.vista.modos.value != MODO_BUSQUEDA:
            return
        confirmar_borrador(self)

    def cancelar(self, *, devolver_foco: bool = False) -> None:
        """Descarta la selección sin modificar el rango ni la captura."""
        if self.activa:
            self.vista.vista_previa.compartido.borrador([])
            self.vista.vista_previa.panel.classes(remove="biseccion-seleccion-activa")
            self.activa = False
        if not self.region.is_deleted:
            self.region.set_visibility(False)
        if devolver_foco and not self.inicio.is_deleted:
            self.inicio.run_method("focus")


def _abscisa_finita(valor) -> float | None:
    if type(valor) not in (int, float):
        return None
    try:
        abscisa = float(valor)
    except OverflowError:
        return None
    return abscisa if isfinite(abscisa) else None
