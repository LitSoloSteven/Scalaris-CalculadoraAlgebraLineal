"""Composición de la captura, la gráfica previa y la solución de raíces."""
from nicegui import ui

from src.frontend.componentes.aplicacion.base.simbolos import habilitar_simbolos
from src.frontend.componentes.aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.aplicacion.controles.selector_opciones import SelectorOpciones, estilizar_desplegable
from src.frontend.componentes.captura.ecuaciones.limpieza_captura import crear_boton_limpieza
from src.frontend.componentes.glosa.panel.panel_ia import PanelIA
from src.frontend.componentes.raices.captura.campo_funcion_real import crear_campo_funcion
from src.frontend.componentes.raices.captura.estructura_metodos_raices import montar_estructura_metodos_raices
from src.frontend.controladores.compartido.sesion.actualizacion_cancelable import cancelar_actualizacion
from src.frontend.controladores.compartido.sesion.sesion_matricial import actualizar_contexto
from src.frontend.controladores.raices.metodos_abiertos import LONGITUD_MAXIMA_NUMERICA, resolver_captura
from src.frontend.navegacion import ruta_de
from src.frontend.vistas.raices.metodos_abiertos.grafica.figura import (
    crear_figura_metodos_abiertos,
    rango_ventana_resultado,
)
from src.frontend.vistas.raices.metodos_abiertos.grafica.vista_previa import PanelVistaPrevia
from src.frontend.vistas.raices.metodos_abiertos.salida.contexto import construir_contexto, construir_senales
from src.frontend.vistas.raices.metodos_abiertos.salida.salida import SalidaMetodosAbiertos

_TOLERANCIA_POR_DEFECTO = "1e-6"
_LIMITE_POR_DEFECTO = "100"


class VistaMetodosAbiertos:
    """Orquesta la captura, la gráfica dinámica, Glosa y la presentación de la solución."""

    def __init__(self):
        self.salida = SalidaMetodosAbiertos(self._actualizar_figura, self)
        self.previa = self.grafica = self.resultados = self.contenedor_reproductor = self.panel_ia = None
        self._cargando_ejemplo = self._cerrada = False

    @property
    def ultimo_resultado(self):
        """Devuelve el último resultado calculado para los consumidores de la vista."""
        return self.salida.resultado

    @property
    def fila_activa(self):
        """Devuelve la iteración que está seleccionada en la gráfica."""
        return self.salida.fila_activa

    @property
    def reproductor(self):
        """Expone el reproductor de pasos que presenta el procedimiento actual."""
        return self.salida.reproductor

    @property
    def tabla_iteraciones(self):
        """Devuelve la tabla de iteraciones creada para el resultado actual."""
        return self.salida.tabla.tabla

    def construir(self) -> None:
        """Monta la página, Glosa y conecta sus controles de entrada."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("metodos_abiertos"))
        regiones = montar_estructura_metodos_raices(
            "Métodos abiertos",
            "Resuelve f(x) = 0 con Newton-Raphson o el método de la secante.",
            self._construir_captura,
            self._construir_grafica,
        )
        self.resultados, self.contenedor_reproductor = regiones.resultados, regiones.procedimiento
        self._conectar_eventos()
        _vincular_ciclo_vida(self)
        self.panel_ia.construir()
        self.previa.programar()

    def _construir_captura(self) -> None:
        self.metodo = SelectorOpciones(
            (("newton", "Newton-Raphson", "Newton-Raphson"),
             ("secante", "Secante", "Secante")),
            "newton", self._cambio_metodo, "Método de resolución",
        ).classes("metodos-abiertos-metodo")
        self.expresion = crear_campo_funcion(valor="x^3 - x - 2", ejemplo=None)
        _construir_campos(self)
        _construir_acciones(self)

    def _construir_grafica(self) -> None:
        self.previa = PanelVistaPrevia(lambda: self.expresion.value, self._actualizar_figura_previa)
        self.previa.construir()
        self.grafica = self.previa.grafica

    def _conectar_eventos(self) -> None:
        self.x1.set_visibility(False)
        self.expresion.on_value_change(self._editar_expresion)
        for campo in (self.x0, self.x1, self.tolerancia, self.limite):
            campo.on("keydown.enter", self.calcular)
            campo.on_value_change(self._editar_campo)

    def _cambio_metodo(self, _evento) -> None:
        self.x1.set_visibility(self.metodo.value == "secante")
        if not self._cargando_ejemplo:
            self._reiniciar_selector_ejemplo()
        self.invalidar_resultado()

    def _editar_campo(self, _=None) -> None:
        if not self._cargando_ejemplo:
            self._reiniciar_selector_ejemplo()
        self.invalidar_resultado()

    def invalidar_resultado(self, _=None) -> None:
        """Retira el resultado anterior cuando cambia cualquier dato de entrada."""
        self.salida.limpiar(self.resultados, self.contenedor_reproductor)
        if self.previa is not None:
            self.previa.establecer_titulo("Gráfica previa")
        self._actualizar_figura(None)

    def _editar_expresion(self, _) -> None:
        if not self._cargando_ejemplo:
            self._reiniciar_selector_ejemplo()
        self.invalidar_resultado()
        if self.previa is not None:
            self.previa.reiniciar_encuadre()
            self.previa.programar()

    def calcular(self) -> None:
        """Resuelve la captura vigente y presenta los valores calculados."""
        self.invalidar_resultado()
        datos = resolver_captura(self._captura_actual())
        self.salida.mostrar(datos, self.resultados, self.contenedor_reproductor)
        if self.previa is not None:
            self.previa.establecer_titulo("Gráfica del resultado")
            self.previa.ajustar_rango_base(rango_ventana_resultado(datos, self.salida.fila_activa))
        self._actualizar_figura(self.salida.fila_activa)
        actualizar_contexto(self)

    def _captura_actual(self) -> dict[str, str]:
        return {
            "metodo": self.metodo.value, "expresion": self.expresion.value,
            "x0": self.x0.value, "x1": self.x1.value,
            "tolerancia": self.tolerancia.value, "limite_iteraciones": self.limite.value,
        }

    def _actualizar_figura(self, fila: dict | None) -> None:
        if self.grafica is None or self.grafica.is_deleted:
            return
        opciones = (
            {"rango_camara": self.previa.rango_camara, "identidad": self.previa.identidad,
             "revision_vista": self.previa.revision_vista}
            if self.previa is not None else None
        )
        figura = crear_figura_metodos_abiertos(
            self.previa.respuesta if self.previa is not None else None,
            self.ultimo_resultado, fila, opciones_vista=opciones,
        )
        self.grafica.update_figure(figura)

    def _actualizar_figura_previa(self) -> None:
        self._actualizar_figura(self.fila_activa)

    def cargar_ejemplo(self, evento) -> None:
        """Carga una captura breve para cada método y estado numérico habitual."""
        self._actualizar_etiqueta_ejemplo(evento.value)
        if evento.value not in _EJEMPLOS_DATOS:
            return
        metodo, expresion, x0, x1 = _EJEMPLOS_DATOS[evento.value]
        self._cargando_ejemplo = True
        try:
            self.metodo.set_value(metodo)
            self.expresion.set_value(expresion)
            self.x0.set_value(x0)
            self.x1.set_value(x1)
            self.previa.reiniciar_encuadre()
            self.previa.programar()
        finally:
            self._cargando_ejemplo = False

    def _reiniciar_selector_ejemplo(self) -> None:
        if getattr(self, "selector_ejemplos", None) is not None and self.selector_ejemplos.value is not None:
            self.selector_ejemplos.set_value(None)
        self._actualizar_etiqueta_ejemplo(None)

    def _actualizar_etiqueta_ejemplo(self, valor) -> None:
        if getattr(self, "selector_ejemplos", None) is None:
            return
        if valor:
            self.selector_ejemplos.props(remove="label")
        else:
            self.selector_ejemplos.props('label="Ejemplos"')

    def esta_completamente_vacio(self) -> bool:
        """Indica si la función o los puntos iniciales deben conservarse al limpiar."""
        return not any(str(campo.value or "").strip() for campo in (self.expresion, self.x0, self.x1))

    def limpiar_todo(self) -> None:
        """Restablece la captura, el resultado y las marcas de la gráfica."""
        self._cargando_ejemplo = True
        try:
            self.metodo.set_value("newton")
            self._reiniciar_selector_ejemplo()
            for campo, valor in ((self.expresion, ""), (self.x0, ""), (self.x1, ""),
                                 (self.tolerancia, _TOLERANCIA_POR_DEFECTO), (self.limite, _LIMITE_POR_DEFECTO)):
                campo.set_value(valor)
            self.invalidar_resultado()
            self.previa.reiniciar_encuadre()
            self.previa.programar()
        finally:
            self._cargando_ejemplo = False

    def limpiar(self) -> None:
        """Conserva el nombre esperado por el control compartido de limpieza."""
        self.limpiar_todo()

    def obtener_contexto_ia(self):
        """Entrega a Glosa el contexto de la captura, resultado y paso vigentes."""
        return construir_contexto(self)

    def obtener_senales_ia(self):
        """Emite señales de método, estado y diagnósticos para sugerencias de Glosa."""
        return construir_senales(self)


def _construir_campos(vista: VistaMetodosAbiertos) -> None:
    with ui.row().classes("metodos-raices-campos w-full"):
        vista.x0 = _crear_campo_numerico("Punto inicial x0", "1.5")
        vista.x1 = _crear_campo_numerico("Segundo punto x1", "2")
        vista.tolerancia = _crear_campo_numerico("Tolerancia ε", _TOLERANCIA_POR_DEFECTO)
        vista.limite = _crear_campo_numerico("Máximo de iteraciones", _LIMITE_POR_DEFECTO, "entero")


def _construir_acciones(vista: VistaMetodosAbiertos) -> None:
    with ui.row().classes("metodos-raices-acciones w-full flex-wrap items-center"):
        ui.button("Calcular raíz", on_click=vista.calcular).classes(
            "boton-principal metodos-raices-calcular").props("ripple=false")
        vista.limpieza = crear_boton_limpieza(
            vista, lambda: not vista.resultados.is_deleted,
            lambda: [vista.expresion, vista.x0, vista.x1, vista.tolerancia, vista.limite],
            campo_foco=vista.expresion,
        )
        vista.limpieza.boton.classes(remove="flex-1 py-3", add="metodos-raices-limpieza")
        vista.selector_ejemplos = estilizar_desplegable(
            ui.select(_EJEMPLOS, label="Ejemplos", on_change=vista.cargar_ejemplo),
            "metodos-raices-ejemplos min-w-56",
        )


def _vincular_ciclo_vida(vista: VistaMetodosAbiertos) -> None:
    def _cerrar() -> None:
        vista._cerrada = True
        if vista.panel_ia is not None:
            cancelar_actualizacion(getattr(vista.panel_ia, "_tarea_actualizacion", None))
            vista.panel_ia.foco_explicacion = None
            vista.panel_ia.contexto_adjuntado = ""

    def _reabrir() -> None:
        if vista._cerrada and vista.resultados is not None and not vista.resultados.is_deleted:
            vista._cerrada = False
            if vista.panel_ia is not None:
                vista.panel_ia.limpiar_foco_explicacion()
                vista.panel_ia.limpiar_contexto()
                vista.panel_ia.programar_actualizacion_contexto()

    cliente = ui.context.client
    cliente.on_disconnect(_cerrar)
    cliente.on_delete(_cerrar)
    cliente.on_connect(_reabrir)


def _crear_campo_numerico(etiqueta: str, valor: str, perfil: str = "real"):
    campo = ui.input(etiqueta, value=valor).props(
        f"maxlength={LONGITUD_MAXIMA_NUMERICA} autocomplete=off").classes("matriz-entrada min-w-0 flex-1")
    habilitar_simbolos(campo, perfil)
    return campo


_EJEMPLOS = {
    "n1": "Newton: x³ − x − 2", "n2": "Newton: x³ − 2x − 5",
    "s1": "Secante: x³ − x − 2", "s2": "Secante: x³ − 2x − 5",
    "dn": "Derivada nula", "sn": "Denominador nulo",
}
_EJEMPLOS_DATOS = {
    "n1": ("newton", "x^3 - x - 2", "1.5", "2"),
    "n2": ("newton", "x^3 - 2*x - 5", "2", "3"),
    "s1": ("secante", "x^3 - x - 2", "1", "2"),
    "s2": ("secante", "x^3 - 2*x - 5", "2", "3"),
    "dn": ("newton", "x^2 + 1", "0", "2"),
    "sn": ("secante", "1", "1", "2"),
}
