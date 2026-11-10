"""Borrador accesible a partir de puntos reales de una muestra vigente."""
from math import isfinite
from src.frontend.componentes.borrador_intervalo_raices import construir_borrador, confirmar_borrador
from src.frontend.controladores.captura_real import real_capturado
from src.frontend.controladores.seleccion_muestra_raices import abscisa_muestreada


class SeleccionGrafico:
    """Carga extremos solo al confirmar; el puntero no ejecuta el método."""

    def __init__(self, vista):
        self.vista = vista
        self.activa = False

    def construir(self) -> None:
        """Monta campos equivalentes al puntero, confirmación, cancelación y Escape."""
        construir_borrador(self, "Selecciona dos puntos de la curva, no el fondo del gráfico, o escribe los extremos.",
                           self._dibujar_borrador)
        self.vista.vista_previa.grafica.on("plotly_click", self._marcar)

    def iniciar(self) -> None:
        """Abre un borrador vacío sin modificar los extremos capturados."""
        if not self.vista.vista_previa._montada():
            return
        self.activa = True
        for campo in self.campos:
            campo.set_value("")
        self.estado.set_text("Escribe a < b o selecciona dos puntos de la curva.")
        self.region.set_visibility(True)
        self.campos[0].run_method("focus")

    def _marcar(self, evento) -> None:
        panel = self.vista.vista_previa
        if not self.activa or not panel._montada() or not panel.respuesta or panel.respuesta["estado"] != "EXITO":
            return
        abscisa = abscisa_muestreada(evento.args, panel.respuesta["muestra"], panel.identidad)
        if abscisa is None:
            return
        primero, segundo = self.campos
        if segundo.value:
            primero.set_value("")
            segundo.set_value("")
        if not primero.value:
            primero.set_value(str(abscisa))
            return
        try:
            anterior = real_capturado(primero.value, "El extremo a")
        except ValueError:
            primero.set_value(str(abscisa))
            return
        inferior, superior = sorted((anterior, abscisa))
        primero.set_value(str(inferior))
        segundo.set_value(str(superior))

    def _dibujar_borrador(self) -> None:
        if not self.activa:
            return
        puntos = []
        for campo in self.campos:
            try:
                punto = real_capturado(campo.value, "El extremo")
            except ValueError:
                continue
            if isfinite(punto):
                puntos.append(punto)
        self.vista.vista_previa.dibujar_borrador(puntos)

    def confirmar(self) -> None:
        """Valida los campos y carga el intervalo sin iniciar un cálculo ni alterar el rango."""
        if not self.activa or not self.vista.vista_previa._montada():
            return
        confirmar_borrador(self)

    def cancelar(self, *, devolver_foco: bool = False) -> None:
        """Descarta los marcadores y devuelve el foco cuando la cancelación es explícita."""
        if self.activa:
            self.vista.vista_previa.dibujar_borrador([])
        self.activa = False
        if not self.region.is_deleted:
            self.region.set_visibility(False)
        if devolver_foco and not self.inicio.is_deleted:
            self.inicio.run_method("focus")
