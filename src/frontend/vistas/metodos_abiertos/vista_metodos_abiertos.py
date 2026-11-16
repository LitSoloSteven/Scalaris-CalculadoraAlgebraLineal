"""Composición de la captura, la gráfica previa y la solución de raíces."""
from nicegui import ui

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.controladores.metodos_abiertos import LONGITUD_MAXIMA_NUMERICA, resolver_captura
from src.frontend.navegacion import ruta_de
from .figura import crear_figura_metodos_abiertos
from .salida import SalidaMetodosAbiertos
from .vista_previa import PanelVistaPrevia

_TOLERANCIA_POR_DEFECTO = "1e-6"
_LIMITE_POR_DEFECTO = "100"


class VistaMetodosAbiertos:
    """Orquesta la captura y delega la presentación de la solución."""

    def __init__(self):
        self.salida = SalidaMetodosAbiertos(self._actualizar_figura)
        self.previa = None
        self.grafica = None
        self.resultados = None
        self.contenedor_reproductor = None

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
        """Monta la página y conecta sus controles de entrada."""
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("metodos_abiertos"))
        self._construir_captura()
        self._construir_grafica_y_salida()
        self._conectar_eventos()
        self.previa.programar()

    def _construir_captura(self) -> None:
        with ui.column().classes(
                "metodos-abiertos-vista vista-raiz w-full max-w-6xl mx-auto p-4 gap-4"):
            self._construir_encabezado()
            with ui.card().classes(
                    "metodos-abiertos-captura panel-tarjeta w-full metodos-abiertos-entrada metodos-abiertos-entrada-2"):
                self.metodo = SelectorOpciones(
                    (("newton", "Newton-Raphson", "Newton-Raphson"),
                     ("secante", "Secante", "Secante")),
                    "newton", self._cambio_metodo, "Método de resolución",
                ).classes("metodos-abiertos-metodo")
                self.expresion = ui.input("Función f(x)", value="x^3 - x - 2").props(
                    "maxlength=512 autocomplete=off").classes("matriz-entrada w-full")
                self._construir_campos()
                self._construir_acciones()

    def _construir_encabezado(self) -> None:
        with ui.column().classes(
                "metodos-abiertos-encabezado metodos-abiertos-entrada metodos-abiertos-entrada-1"):
            ui.label("Métodos abiertos").classes("text-2xl font-bold texto-principal")
            ui.label("Resuelve f(x) = 0 con Newton-Raphson o el método de la secante.").classes(
                "text-sm texto-secundario")

    def _construir_campos(self) -> None:
        with ui.row().classes("metodos-abiertos-campos w-full"):
            self.x0 = self._crear_campo_numerico("Punto inicial x0", "1.5")
            self.x1 = self._crear_campo_numerico("Segundo punto x1", "2")
            self.tolerancia = self._crear_campo_numerico(
                "Tolerancia ε", _TOLERANCIA_POR_DEFECTO)
            self.limite = self._crear_campo_numerico(
                "Máximo de iteraciones", _LIMITE_POR_DEFECTO)

    @staticmethod
    def _crear_campo_numerico(etiqueta: str, valor: str):
        return ui.input(etiqueta, value=valor).props(
            f"maxlength={LONGITUD_MAXIMA_NUMERICA} autocomplete=off").classes(
            "matriz-entrada min-w-0 flex-1")

    def _construir_acciones(self) -> None:
        with ui.row().classes("metodos-abiertos-acciones w-full flex-wrap items-center"):
            ui.button("Calcular raíz", on_click=self.calcular).classes(
                "boton-principal metodos-abiertos-calcular").props("ripple=false")
            self.limpieza = crear_boton_limpieza(
                self, lambda: not self.resultados.is_deleted,
                lambda: [self.expresion, self.x0, self.x1, self.tolerancia, self.limite],
                campo_foco=self.expresion,
            )
            self.limpieza.boton.classes(remove="flex-1 py-3")
            self.limpieza.boton.classes(add="metodos-abiertos-boton-limpieza")
            self.selector_ejemplos = ui.select(
                _EJEMPLOS, label="Ejemplos", on_change=self.cargar_ejemplo,
            ).classes("selector-controles metodos-abiertos-ejemplos min-w-56")

    def _construir_grafica_y_salida(self) -> None:
        with ui.column().classes(
                "metodos-abiertos-vista vista-raiz w-full max-w-6xl mx-auto p-4 gap-4"):
            with ui.column().classes(
                    "metodos-abiertos-previa w-full min-w-0 metodos-abiertos-entrada metodos-abiertos-entrada-3"):
                self.previa = PanelVistaPrevia(
                    lambda: self.expresion.value, self._actualizar_figura_previa,
                )
                self.previa.construir()
            self.grafica = self.previa.grafica
            self.resultados = ui.column().classes("metodos-abiertos-resultados w-full min-w-0")
            self.contenedor_reproductor = ui.column().classes("w-full min-w-0")

    def _conectar_eventos(self) -> None:
        self.x1.set_visibility(False)
        self.expresion.on_value_change(self._editar_expresion)
        for campo in (self.x0, self.x1, self.tolerancia, self.limite):
            campo.on("keydown.enter", self.calcular)
            campo.on_value_change(self.invalidar_resultado)

    def _cambio_metodo(self, evento) -> None:
        """Actualiza los campos según el método y retira el cálculo vigente."""
        self.x1.set_visibility(self.metodo.value == "secante")
        self.invalidar_resultado()

    def invalidar_resultado(self, _=None) -> None:
        """Retira el resultado anterior cuando cambia cualquier dato de entrada."""
        self.salida.limpiar(self.resultados, self.contenedor_reproductor)
        self._actualizar_figura(None)

    def _editar_expresion(self, _) -> None:
        """Revoca el resultado y programa un nuevo muestreo de la función."""
        self.invalidar_resultado()
        self.previa.programar()

    def calcular(self) -> None:
        """Resuelve la captura vigente y presenta los valores calculados."""
        self.invalidar_resultado()
        datos = resolver_captura(self._captura_actual())
        self.salida.mostrar(datos, self.resultados, self.contenedor_reproductor)
        self._actualizar_figura(self.salida.fila_activa)

    def _captura_actual(self) -> dict[str, str]:
        return {
            "metodo": self.metodo.value, "expresion": self.expresion.value,
            "x0": self.x0.value, "x1": self.x1.value,
            "tolerancia": self.tolerancia.value, "limite_iteraciones": self.limite.value,
        }

    def _actualizar_figura(self, fila: dict | None) -> None:
        if self.grafica is None or self.grafica.is_deleted:
            return
        figura = crear_figura_metodos_abiertos(
            self.previa.respuesta, self.ultimo_resultado, fila,
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
        self.metodo.set_value(metodo)
        self.expresion.set_value(expresion)
        self.x0.set_value(x0)
        self.x1.set_value(x1)
        self.previa.programar()

    def _actualizar_etiqueta_ejemplo(self, valor) -> None:
        if valor:
            self.selector_ejemplos.props(remove="label")
        else:
            self.selector_ejemplos.props('label="Ejemplos"')

    def esta_completamente_vacio(self) -> bool:
        """Indica si la función o los puntos iniciales deben conservarse al limpiar."""
        campos = (self.expresion, self.x0, self.x1)
        return not any(str(campo.value or "").strip() for campo in campos)

    def limpiar_todo(self) -> None:
        """Restablece la captura, el resultado y las marcas de la gráfica."""
        self.metodo.set_value("newton")
        self.selector_ejemplos.set_value(None)
        self._actualizar_etiqueta_ejemplo(None)
        self.expresion.set_value("")
        self.x0.set_value("")
        self.x1.set_value("")
        self.tolerancia.set_value(_TOLERANCIA_POR_DEFECTO)
        self.limite.set_value(_LIMITE_POR_DEFECTO)
        self.invalidar_resultado()
        self.previa.programar()

    def limpiar(self) -> None:
        """Conserva el nombre esperado por el control compartido de limpieza."""
        self.limpiar_todo()


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
