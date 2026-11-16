"""Composición interna del cálculo individual de Bisección y Regla falsa."""
from nicegui import ui

from src.frontend.componentes.estructura_metodos_raices import montar_estructura_metodos_raices
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion
from src.frontend.controladores.biseccion.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.calculo_raices import ConfiguracionCalculoRaices, resolver_calculo_raices
from src.frontend.controladores.coordinacion_trabajos_raices import CoordinadorTrabajosRaices
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, METODOS, resolver_presentacion
from src.frontend.controladores.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO
from src.frontend.controladores.sesion_matricial import notificar_edicion
from .captura import CapturaMetodosCerrados
from .grafica import GraficaMetodosCerrados
from .salida import SalidaMetodosCerrados

_CONFIGURACION = ConfiguracionCalculoRaices(
    mensaje_carga="Calculando la raíz en el intervalo…",
    mensaje_error="No se pudo completar el cálculo. Revisa la función y vuelve a intentarlo.",
    mensaje_registro="No se pudo presentar el cálculo de métodos cerrados",
)
_MENSAJE_INICIAL = "Escribe la función y los extremos del intervalo."


class VistaMetodosCerrados:
    """Conecta la captura común con un cálculo vigente y una sola gráfica."""

    def __init__(self, metodo: str = BISECCION):
        self.captura = CapturaMetodosCerrados(self, metodo)
        self.grafica = GraficaMetodosCerrados(self.captura)
        self.salida = SalidaMetodosCerrados(self)
        self._trabajos = {metodo: CoordinadorTrabajosRaices(resolver_presentacion) for metodo in METODOS}
        self.tarea_calculo = self.ultimo_resultado = self.ultimo_ampliado = self.interruptor_examen = None
        self.ocupado = self.modo_examen = self._cerrada = False
        self._revision_captura = 0
        self._precision_visual = DECIMALES_PRESENTACION_DEFECTO

    @property
    def boton_resolver(self):
        """Expone el botón asociado a la solicitud individual."""
        return self.captura.boton_resolver

    @property
    def parametros_criterio(self) -> dict:
        """Expone los borradores que el diagnóstico puede seleccionar."""
        return self.captura.parametros_criterio

    def construir(self) -> None:
        """Monta la vista dentro de la página que la consume."""
        regiones = montar_estructura_metodos_raices(
            "Métodos cerrados", "Resuelve f(x) = 0 en un intervalo con Bisección o Regla falsa.",
            self._montar_captura, self.grafica.construir,
        )
        self.contenedor_resultados = regiones.resultados
        self.contenedor_procedimiento = regiones.procedimiento
        cliente = ui.context.client
        cliente.on_disconnect(self.cerrar)
        cliente.on_delete(self.cerrar)
        cliente.on_connect(self._reabrir)

    def _montar_captura(self) -> None:
        self.captura.construir()
        self.estado = ui.label(_MENSAJE_INICIAL).classes("text-sm texto-secundario").props("role=status")

    def capturar(self) -> dict:
        """Entrega una instantánea cruda de la solicitud y su método."""
        return self.captura.capturar()

    async def resolver(self) -> None:
        """Publica el cálculo individual solo si su método y captura siguen vigentes."""
        if not self._cerrada:
            await resolver_calculo_raices(
                self, resolver_presentacion, _CONFIGURACION, ejecutar=self._ejecutar,
            )

    async def _ejecutar(self, captura: dict) -> dict | None:
        return await self._trabajos[captura["metodo"]].ejecutar(captura)

    def editar_captura(self) -> None:
        """Revoca el cálculo anterior después de editar campos o cambiar de método."""
        if self._cerrada:
            return
        self._revocar()
        self._retirar_resultado()
        self.estado.set_text(_MENSAJE_INICIAL)
        self.captura.actualizar_guia()
        self.actualizar_grafica()

    def actualizar_grafica(self) -> None:
        """Programa la fórmula y la curva para los campos visibles."""
        if not self._cerrada:
            self.captura.previa_expresion.programar(self.captura.expresion.value or "")
            self.grafica.actualizar()

    def cargar_captura(self, captura: dict) -> None:
        """Restaura un ejercicio o una propuesta sin lanzar el cálculo."""
        self.captura.restaurar(captura)
        self.editar_captura()

    def esta_completamente_vacio(self) -> bool:
        """Indica si limpiar retiraría datos del ejercicio o del rango visual."""
        captura = self.capturar()
        rango = self.captura.captura_grafica()
        return (not any(str(captura[clave] or "").strip() for clave in
                        ("expresion", "extremo_izquierdo", "extremo_derecho"))
                and (rango["x_min"], rango["x_max"]) == tuple(map(str, RANGO_GRAFICA_DEFECTO)))

    def limpiar_todo(self) -> None:
        """Vacía el ejercicio y el encuadre, y conserva las preferencias del método."""
        self.captura.ejemplos.set_value(None)
        self.captura.restaurar(dict.fromkeys(("expresion", "extremo_izquierdo", "extremo_derecho"), ""))
        self.editar_captura()
        self.captura.definir_rango(RANGO_GRAFICA_DEFECTO)

    def cerrar(self) -> None:
        """Revoca ambos trabajos y detiene la reproducción al desconectar el cliente."""
        if self._cerrada:
            return
        self._cerrada = True
        self._revocar()
        for trabajador in self._trabajos.values():
            trabajador.cerrar()
        if not self.contenedor_resultados.is_deleted:
            self._retirar_resultado()
        self.grafica.cerrar()
        self.captura.previa_expresion.cerrar()

    def _reabrir(self) -> None:
        if self._cerrada and not self.contenedor_resultados.is_deleted:
            self._cerrada = False
            for trabajador in self._trabajos.values():
                trabajador.reabrir()
            self.estado.set_text(_MENSAJE_INICIAL)
            self.grafica.reabrir()
            self.captura.previa_expresion.reabrir(self.captura.expresion.value or "")

    def _revocar(self) -> None:
        notificar_edicion(self)
        for trabajador in self._trabajos.values():
            trabajador.invalidar()
        tarea, self.tarea_calculo = self.tarea_calculo, None
        cancelar_actualizacion(tarea)
        self.ocupado = False
        if not self.boton_resolver.is_deleted:
            self.boton_resolver.enable()
            self.boton_resolver.props(remove="loading")

    def _retirar_resultado(self) -> None:
        self.ultimo_resultado = self.ultimo_ampliado = self.interruptor_examen = None
        self.salida.retirar()
        self.grafica.mostrar(None)

    def _publicar(self, datos: dict, _huella: str, *, puntero: bool = False) -> None:
        respuesta = datos["resultado"]
        entrada = respuesta.get("entrada") or {}
        if entrada.get("intervalo_invertido"):
            self.captura.reflejar_intervalo(entrada)
            self.captura.actualizar_guia()
        self.ultimo_resultado, self.ultimo_ampliado = respuesta, datos.get("ampliado")
        self.estado.set_text("Resultado disponible." if respuesta["estado"] != "ERROR" else "Revisa el diagnóstico del cálculo.")
        self.salida.mostrar(datos, puntero=puntero)
