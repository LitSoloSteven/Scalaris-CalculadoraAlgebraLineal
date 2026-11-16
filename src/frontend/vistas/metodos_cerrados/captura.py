"""Controles y borradores de los métodos cerrados."""
from nicegui import ui

from src.backend.resolutores.raices.limites_raices import LIMITE_ITERACIONES_DEFECTO, LONGITUD_MAXIMA_EXPRESION
from src.backend.resolutores.raices.unidades_angulares import UNIDADES_ANGULARES, UNIDAD_ANGULAR_DEFECTO
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.componentes.previa_expresion_raices import PreviaExpresion
from src.frontend.componentes.selector_opciones import SelectorOpciones
from src.frontend.controladores.biseccion.captura_criterio import texto_estimacion
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS
from src.frontend.controladores.metodos_cerrados.adaptadores import (
    BISECCION, METODOS, REGLA_FALSA, captura_del_metodo, criterio_inicial, guia_parada, parametros_iniciales,
)
from src.frontend.controladores.rango_exploracion_raices import LONGITUD_CAMPO_GRAFICA, RANGO_GRAFICA_DEFECTO
from src.frontend.vistas.biseccion.ejemplos import EJEMPLOS as EJEMPLOS_BISECCION
from src.frontend.vistas.biseccion.estado_captura import transaccion
from src.frontend.vistas.regla_falsa.ejemplos import EJEMPLOS as EJEMPLOS_REGLA_FALSA

_EJEMPLOS = {
    BISECCION: {nombre: datos for grupo in EJEMPLOS_BISECCION.values() for nombre, datos in grupo},
    REGLA_FALSA: dict(EJEMPLOS_REGLA_FALSA),
}
_CAMPOS = {
    "expresion": "expresion", "extremo_izquierdo": "inferior", "extremo_derecho": "superior",
    "unidad_angular": "unidad", "limite_iteraciones": "limite",
}
_ETIQUETAS_CRITERIO = {tipo: datos[0] for tipo, datos in CRITERIOS.items()}


class CapturaMetodosCerrados:
    """Monta un formulario y conserva un borrador de parada por método."""

    def __init__(self, vista, metodo: str):
        self.vista = vista
        self._metodo = metodo
        self._cargando_captura = False
        self._preferencias = {}
        self._cero_preferido = None

    def construir(self) -> None:
        """Monta campos, acciones y ayuda con un único destino para el envío."""
        with ui.element("form").classes("w-full column gap-3").on("submit.prevent", self.vista.resolver):
            opciones = tuple((metodo, nombre, nombre) for metodo, nombre in METODOS.items())
            self.metodo = SelectorOpciones(opciones, self._metodo, self._cambiar_metodo, "Método de resolución")
            self.expresion = ui.input("Función f(x)", placeholder="Ejemplo: x^2 - 2").classes(
                "matriz-entrada w-full").props(f"maxlength={LONGITUD_MAXIMA_EXPRESION} autocomplete=off spellcheck=false")
            self.previa_expresion = PreviaExpresion()
            with ui.row().classes("metodos-raices-campos w-full"):
                self.inferior = _campo("Extremo inferior a")
                self.superior = _campo("Extremo superior b")
                self.unidad = ui.select({valor: valor.capitalize() for valor in UNIDADES_ANGULARES},
                                        value=UNIDAD_ANGULAR_DEFECTO,
                                        label="Unidad trigonométrica").classes("matriz-entrada min-w-0")
            self._construir_parada()
            self._construir_acciones()
            self._construir_opciones()
        self._conectar()
        self.actualizar_guia()

    def _construir_parada(self) -> None:
        with ui.row().classes("metodos-raices-campos w-full"):
            self.criterio = ui.select(_ETIQUETAS_CRITERIO, value=criterio_inicial(self._metodo),
                                      label="Criterio de parada").classes("matriz-entrada min-w-0")
            iniciales = parametros_iniciales(self._metodo)
            self.parametros_criterio = {}
            for tipo, (_, etiqueta, _) in CRITERIOS.items():
                campo = _campo(etiqueta, iniciales[tipo])
                campo.bind_visibility_from(self.criterio, "value", backward=lambda actual, tipo=tipo: actual == tipo)
                self.parametros_criterio[tipo] = campo
        self.guia = ui.label().classes("text-sm texto-secundario").props("aria-live=polite")
        self.estimacion = ui.label().classes("text-sm texto-secundario")

    def _construir_acciones(self) -> None:
        with ui.row().classes("metodos-raices-acciones w-full flex-wrap items-center"):
            self.boton_resolver = ui.button("Calcular raíz", icon="calculate", color=None).classes(
                "boton-principal metodos-raices-calcular").props("type=submit ripple=false")
            limpieza = crear_boton_limpieza(self.vista, lambda: not self.expresion.is_deleted,
                                            animar=False, campo_foco=self.expresion)
            limpieza.boton.classes(add="metodos-raices-limpieza", remove="flex-1 py-3")
            self.ejemplos = ui.select(list(_EJEMPLOS[self._metodo]), label="Ejemplos",
                                      on_change=self._cargar_ejemplo).classes(
                                          "selector-controles metodos-raices-ejemplos min-w-56")

    def _construir_opciones(self) -> None:
        with ui.expansion("Avanzado").classes("w-full"):
            with ui.row().classes("metodos-raices-campos w-full"):
                self.limite = _campo("Límite de iteraciones", str(LIMITE_ITERACIONES_DEFECTO))
                minimo, maximo = RANGO_GRAFICA_DEFECTO
                self.minimo = _campo("Mínimo de la gráfica", str(minimo))
                self.maximo = _campo("Máximo de la gráfica", str(maximo))
        with ui.expansion("Sintaxis y continuidad").classes("w-full"):
            ui.label("Usa x como variable, ^ para potencias y paréntesis en funciones como sin(x) o ln(x).")
            ui.label("La garantía requiere continuidad en todo [a, b]. El muestreo no demuestra continuidad.")

    def _conectar(self) -> None:
        for campo in (self.expresion, self.inferior, self.superior, self.unidad):
            campo.on_value_change(self._editar_ejercicio)
        for campo in (self.criterio, self.limite):
            campo.on_value_change(self._editar)
        for tipo, campo in self.parametros_criterio.items():
            campo.on_value_change(lambda tipo=tipo: self._editar() if self.criterio.value == tipo else None)
        for campo in (self.minimo, self.maximo):
            campo.on_value_change(self._editar_rango)

    def capturar(self) -> dict:
        """Devuelve el ejercicio y exclusivamente el criterio seleccionado."""
        datos = {clave: getattr(self, atributo).value for clave, atributo in _CAMPOS.items()}
        tipo = self.criterio.value
        datos.update(metodo=self._metodo, criterio={"tipo": tipo, "parametro": self.parametros_criterio[tipo].value})
        if self._cero_preferido is not None:
            datos["cero_preferido"] = self._cero_preferido
        return datos

    def captura_grafica(self) -> dict:
        """Obtiene solo los campos que determinan el muestreo de la curva."""
        return {"expresion": self.expresion.value, "unidad_angular": self.unidad.value,
                "x_min": self.minimo.value, "x_max": self.maximo.value}

    def definir_rango(self, rango: tuple[float, float]) -> None:
        """Actualiza ambos extremos visuales sin cambiar la solicitud matemática."""
        with transaccion(self):
            for campo, valor in zip((self.minimo, self.maximo), rango):
                campo.set_value(str(valor))
        self._editar_rango()

    def restaurar(self, captura: dict) -> None:
        """Restaura los campos presentes sin ejecutar el cálculo."""
        with transaccion(self):
            for clave, atributo in _CAMPOS.items():
                if clave in captura:
                    getattr(self, atributo).set_value(captura[clave])
            criterio = captura.get("criterio")
            if criterio is None and "tolerancia" in captura:
                criterio = {"tipo": "residuo", "parametro": captura["tolerancia"]}
            if criterio is not None:
                self.criterio.set_value(criterio["tipo"])
                self.parametros_criterio[criterio["tipo"]].set_value(str(criterio["parametro"]))
            if any(clave in captura for clave in ("expresion", "extremo_izquierdo", "extremo_derecho",
                                                 "unidad_angular", "cero_preferido")):
                self._cero_preferido = captura.get("cero_preferido")

    def reflejar_intervalo(self, entrada: dict) -> None:
        """Muestra los extremos normalizados por el motor sin editar la solicitud."""
        with transaccion(self):
            self.inferior.set_value(str(entrada["extremo_izquierdo"]))
            self.superior.set_value(str(entrada["extremo_derecho"]))

    def actualizar_guia(self) -> None:
        """Publica la condición activa y la estimación de Bisección cuando esté disponible."""
        captura = self.capturar()
        self.guia.set_text(guia_parada(captura))
        estimacion = texto_estimacion(captura_del_metodo(captura), mostrar_error=False) if self._metodo == BISECCION else ""
        self.estimacion.set_text(estimacion)

    def _cambiar_metodo(self, evento) -> None:
        if evento.value == self._metodo:
            return
        parametros = {tipo: campo.value for tipo, campo in self.parametros_criterio.items()}
        self._preferencias[self._metodo] = self.criterio.value, parametros, self.limite.value
        self._metodo = evento.value
        opcion, parametros, limite = self._preferencias.get(
            self._metodo, (criterio_inicial(self._metodo), parametros_iniciales(self._metodo), str(LIMITE_ITERACIONES_DEFECTO)))
        with transaccion(self):
            self.criterio.set_value(opcion)
            for tipo, valor in parametros.items():
                self.parametros_criterio[tipo].set_value(valor)
            self.limite.set_value(limite)
            self.ejemplos.set_options(list(_EJEMPLOS[self._metodo]), value=None)
            self._cero_preferido = None
        self._editar()

    def _cargar_ejemplo(self, evento) -> None:
        datos = _EJEMPLOS[self._metodo].get(evento.value)
        if datos is not None:
            self.vista.cargar_captura(datos)

    def _editar_ejercicio(self) -> None:
        if not self._cargando_captura:
            self._cero_preferido = None
            self._editar()

    def _editar(self) -> None:
        if not self._cargando_captura:
            self.vista.editar_captura()

    def _editar_rango(self) -> None:
        if not self._cargando_captura:
            self.vista.actualizar_grafica()


def _campo(etiqueta: str, valor: str = ""):
    return ui.input(etiqueta, value=valor).classes("matriz-entrada min-w-0").props(
        f"inputmode=decimal maxlength={LONGITUD_CAMPO_GRAFICA} autocomplete=off")
