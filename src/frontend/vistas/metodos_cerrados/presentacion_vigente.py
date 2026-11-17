"""Selección entre el cálculo individual y el detalle de un candidato."""
from dataclasses import dataclass

from src.ai.huellas import calcular_huella
from src.frontend.controladores.sesion_matricial import actualizar_contexto


@dataclass
class ResultadoIndividual:
    """Conserva el sobre y la posición del procedimiento al inspeccionar un lote."""

    datos: dict
    paso: int = 0
    velocidad: str | None = None


class PresentacionVigente:
    """Publica una sola salida y restaura sus marcas después de consultar un candidato."""

    def __init__(self, vista):
        self.vista = vista
        self.individual = None

    def publicar(self, datos: dict, *, puntero: bool = False) -> None:
        """Registra y muestra el cálculo individual que servirá de regreso desde el lote."""
        self.individual = ResultadoIndividual(datos)
        self._mostrar(datos, puntero=puntero)

    def descartar(self) -> None:
        """Elimina la solución individual y retira la presentación actual."""
        self.individual = None
        self.retirar()

    def retirar(self, *, notificar: bool = True) -> None:
        """Retira el resultado, sus marcas y cualquier foco explícito anterior."""
        vista = self.vista
        vista.ultimo_resultado = vista.ultimo_ampliado = vista.interruptor_examen = None
        vista.candidato_activo = vista._huella_resultado = None
        vista.salida.retirar()
        vista.grafica.mostrar(None)
        if not vista._cerrada:
            vista.panel_ia.limpiar_foco_explicacion()
            vista.panel_ia.limpiar_contexto()
            if notificar:
                actualizar_contexto(vista)

    def mostrar_detalle(self, datos: dict | None, candidato: str | None) -> None:
        """Abre el candidato vigente o recupera el estado del cálculo principal."""
        vista = self.vista
        if vista._cerrada or vista.contenedor_resultados.is_deleted:
            return
        reproductor = vista.salida.reproductor
        if vista.candidato_activo is None and self.individual is not None and reproductor is not None:
            self.individual.paso = reproductor.indice_actual
            self.individual.velocidad = reproductor.velocidad
        self.retirar(notificar=False)
        if datos is not None:
            vista.candidato_activo = candidato
            self._mostrar(datos)
        elif self.individual is not None:
            self._restaurar_individual()
        else:
            vista.continuidad.actualizar()
            actualizar_contexto(vista)

    def _restaurar_individual(self) -> None:
        self._mostrar(self.individual.datos, velocidad=self.individual.velocidad)
        reproductor = self.vista.salida.reproductor
        if reproductor is not None:
            reproductor.ir_a(self.individual.paso)

    def _mostrar(self, datos: dict, *, puntero: bool = False, velocidad: str | None = None) -> None:
        vista = self.vista
        vista.ultimo_resultado, vista.ultimo_ampliado = datos["resultado"], datos.get("ampliado")
        vista._huella_resultado = calcular_huella(vista.capturar())
        vista.salida.mostrar(datos, puntero=puntero, velocidad=velocidad)
        vista.continuidad.actualizar()
        if vista.salida.reproductor is None or not vista.salida.reproductor.pasos:
            actualizar_contexto(vista)
