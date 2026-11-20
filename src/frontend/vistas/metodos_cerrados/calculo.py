"""Vigencia de las solicitudes individuales de los métodos cerrados."""
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion
from src.frontend.controladores.calculo_raices import ConfiguracionCalculoRaices, resolver_calculo_raices
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.metodos_cerrados.adaptadores import METODOS, resolver_presentacion
from src.frontend.controladores.sesion_matricial import notificar_edicion

_CONFIGURACION = ConfiguracionCalculoRaices(
    mensaje_carga="Calculando la raíz en el intervalo…",
    mensaje_error="No se pudo completar el cálculo. Revisa la función y vuelve a intentarlo.",
    mensaje_registro="No se pudo presentar el cálculo de métodos cerrados",
)


class CalculoIndividual:
    """Usa una plaza de cálculo por método y retira la espera cuando deja de corresponder."""

    def __init__(self, vista):
        self.vista = vista
        self._trabajos = {metodo: CoordinadorTrabajosRaices(resolver_presentacion) for metodo in METODOS}

    async def resolver(self) -> None:
        """Calcula y publica exclusivamente la captura manual vigente."""
        vista = self.vista
        if not vista._cerrada and not vista.en_busqueda and not vista.ocupado:
            vista.presentacion.individual = None
            await resolver_calculo_raices(vista, resolver_presentacion, _CONFIGURACION, ejecutar=self._ejecutar)

    def revocar(self) -> None:
        """Retira la espera y su estado de carga sin liberar trabajos reales en curso."""
        vista = self.vista
        notificar_edicion(vista)
        for trabajador in self._trabajos.values():
            trabajador.invalidar()
        tarea, vista.tarea_calculo = vista.tarea_calculo, None
        cancelar_actualizacion(tarea)
        vista.ocupado = False
        if not vista.boton_resolver.is_deleted:
            vista.boton_resolver.enable()
            vista.boton_resolver.props(remove="loading")

    def cerrar(self) -> None:
        """Revoca la espera y bloquea nuevas publicaciones hasta reconectar."""
        self.revocar()
        for trabajador in self._trabajos.values():
            trabajador.cerrar()

    def reabrir(self) -> None:
        """Acepta cálculos de la sesión reconectada."""
        for trabajador in self._trabajos.values():
            trabajador.reabrir()

    async def _ejecutar(self, captura: dict) -> dict | None:
        return await self._trabajos[captura["metodo"]].ejecutar(captura)
