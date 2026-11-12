"""Vista de Scalaris para resolver ecuaciones con el método de la secante."""
from nicegui import ui

from src.backend.resolutores.raices.secante import EntradaSecante, ResultadoSecante, secante
from src.backend.resolutores.raices.unidades_angulares import UNIDADES_ANGULARES
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.controladores.captura_real import entero_capturado, real_capturado
from src.frontend.navegacion import ruta_de


class VistaSecante:
    """Captura dos aproximaciones iniciales y muestra el resultado y su tabla."""

    def __init__(self) -> None:
        self.ultimo_resultado: ResultadoSecante | None = None
        self.panel_ia = None

    def construir(self) -> None:
        """Monta la página, sus controles y la navegación común de Scalaris."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("secante"))

        with ui.column().classes("vista-raiz w-full mx-auto p-4 gap-5").style("max-width: 1180px"):
            with ui.column().classes("w-full gap-2"):
                ui.label("Método de la secante").classes("text-2xl font-bold texto-principal")
                ui.label(
                    "Método abierto para aproximar raíces de ecuaciones no lineales. "
                    "Utiliza dos valores iniciales y no necesita un intervalo con cambio de signo."
                ).classes("texto-secundario")

            with ui.element("div").classes("grid grid-cols-1 lg:grid-cols-2 gap-5 w-full"):
                with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                    ui.label("Datos de entrada").classes("text-lg font-semibold texto-principal")
                    self.expresion = ui.input(
                        "Función f(x)", value="x^2 - 2", placeholder="Ejemplo: x^3 - x - 2"
                    ).classes("w-full matriz-entrada").props("maxlength=512 autocomplete=off spellcheck=false")
                    with ui.element("div").classes("grid grid-cols-1 sm:grid-cols-2 gap-3 w-full"):
                        self.x_anterior = ui.input("Primera aproximación x₀", value="1").classes(
                            "w-full matriz-entrada"
                        ).props("inputmode=decimal")
                        self.x_actual = ui.input("Segunda aproximación x₁", value="2").classes(
                            "w-full matriz-entrada"
                        ).props("inputmode=decimal")
                    with ui.element("div").classes("grid grid-cols-1 sm:grid-cols-2 gap-3 w-full"):
                        self.tolerancia = ui.input("Tolerancia", value="0.000001").classes(
                            "w-full matriz-entrada"
                        ).props("inputmode=decimal")
                        self.limite = ui.input("Límite de iteraciones", value="100").classes(
                            "w-full matriz-entrada"
                        ).props("inputmode=numeric")
                    self.unidad_angular = ui.select(
                        {unidad: unidad.capitalize() for unidad in UNIDADES_ANGULARES},
                        value="radianes",
                        label="Unidad trigonométrica",
                    ).classes("w-full matriz-entrada")
                    with ui.row().classes("items-center gap-2 w-full"):
                        ui.button("Cargar ejemplo", icon="science", color=None, on_click=self.cargar_ejemplo).props(
                            "outline"
                        )
                        self.boton_resolver = ui.button(
                            "Calcular raíz", icon="calculate", color=None, on_click=self.resolver
                        ).classes("boton-principal").props("ripple=false")

                with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                    ui.label("Resultado").classes("text-lg font-semibold texto-principal")
                    self.estado = ui.label(
                        "Introduce la función y dos aproximaciones iniciales para comenzar."
                    ).classes("texto-secundario").props("role=status aria-live=polite aria-atomic=true")
                    self.contenedor_resultado = ui.column().classes("w-full gap-3")
                    ui.separator()
                    ui.label("Fórmula del método").classes("font-semibold texto-principal")
                    ui.markdown(
                        r"\[x_{n+1}=x_n-\frac{f(x_n)(x_n-x_{n-1})}{f(x_n)-f(x_{n-1})}\]"
                    )
                    ui.label(
                        "En cada paso se traza una recta secante entre los dos últimos puntos. "
                        "La nueva aproximación reemplaza al punto más antiguo."
                    ).classes("text-sm texto-secundario")

            with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                ui.label("Procedimiento e iteraciones").classes("text-lg font-semibold texto-principal")
                ui.label(
                    "La tabla conserva los valores internos del cálculo; las cifras no se redondean antes de iterar."
                ).classes("text-sm texto-secundario")
                self.contenedor_tabla = ui.column().classes("w-full min-w-0")

            ui.label(
                "Nota: al ser un método abierto, puede converger o divergir según la función y los valores iniciales. "
                "No se exige que f(x₀) y f(x₁) tengan signos opuestos."
            ).classes("text-sm texto-secundario")

        self.panel_ia.construir()
        self._enlazar_cambios()

    def _enlazar_cambios(self) -> None:
        """Retira resultados antiguos cuando el usuario modifica los datos."""
        for campo in (
            self.expresion, self.x_anterior, self.x_actual,
            self.tolerancia, self.limite, self.unidad_angular,
        ):
            campo.on_value_change(self._datos_modificados)

    def _datos_modificados(self) -> None:
        """Invalida la salida anterior para no mostrar resultados de otra captura."""
        self.ultimo_resultado = None
        self.contenedor_resultado.clear()
        self.contenedor_tabla.clear()
        self.estado.set_text("Datos modificados. Calcula de nuevo para obtener un resultado vigente.")

    def cargar_ejemplo(self) -> None:
        """Restaura el ejercicio x² − 2 con aproximaciones iniciales 1 y 2."""
        self.expresion.value = "x^2 - 2"
        self.x_anterior.value = "1"
        self.x_actual.value = "2"
        self.tolerancia.value = "0.000001"
        self.limite.value = "100"
        self.unidad_angular.value = "radianes"
        self._datos_modificados()

    def resolver(self) -> None:
        """Valida la captura, ejecuta el motor y presenta el resultado completo."""
        try:
            entrada = EntradaSecante(
                expresion=self.expresion.value or "",
                x_anterior=real_capturado(self.x_anterior.value, "La primera aproximación"),
                x_actual=real_capturado(self.x_actual.value, "La segunda aproximación"),
                tolerancia=real_capturado(self.tolerancia.value, "La tolerancia"),
                limite_iteraciones=entero_capturado(self.limite.value, "El límite de iteraciones"),
                unidad_angular=self.unidad_angular.value,
            )
        except ValueError as error:
            ui.notify(str(error), type="negative")
            return

        self.ultimo_resultado = secante(entrada)
        resultado = self.ultimo_resultado
        self.contenedor_resultado.clear()
        self.contenedor_tabla.clear()

        if resultado.estado == "EXITO":
            self.estado.set_text("Cálculo completado.")
        elif resultado.estado == "LIMITE_ITERACIONES":
            self.estado.set_text("Se alcanzó el límite de iteraciones.")
        elif resultado.estado == "ESTANCAMIENTO":
            self.estado.set_text("El cálculo se estancó.")
        else:
            self.estado.set_text("No se pudo completar el cálculo.")

        with self.contenedor_resultado:
            ui.label(resultado.mensaje).classes(
                "texto-acento" if resultado.estado == "EXITO" else "texto-advertencia"
            )
            if resultado.aproximacion is not None:
                ui.label("Raíz aproximada").classes("text-sm texto-secundario")
                ui.label(_numero(resultado.aproximacion)).classes("text-2xl font-bold texto-principal")
                with ui.element("div").classes("grid grid-cols-2 gap-3 w-full"):
                    _metrica("Residuo |f(x)|", _numero(resultado.residuo))
                    _metrica("Iteraciones", str(resultado.iteraciones_totales))
            ui.label(f"Diagnóstico: {resultado.codigo_diagnostico}").classes("text-xs texto-secundario")

        if resultado.iteraciones:
            filas = [
                {
                    "i": fila.i,
                    "x_anterior": _numero(fila.x_anterior),
                    "x_actual": _numero(fila.x_actual),
                    "f_anterior": _numero(fila.f_anterior),
                    "f_actual": _numero(fila.f_actual),
                    "x_siguiente": _numero(fila.x_siguiente),
                    "f_siguiente": _numero(fila.f_siguiente),
                    "error": _numero(fila.error_absoluto),
                }
                for fila in resultado.iteraciones
            ]
            columnas = [
                {"name": "i", "label": "n", "field": "i", "align": "left"},
                {"name": "x_anterior", "label": "xₙ₋₁", "field": "x_anterior"},
                {"name": "x_actual", "label": "xₙ", "field": "x_actual"},
                {"name": "f_anterior", "label": "f(xₙ₋₁)", "field": "f_anterior"},
                {"name": "f_actual", "label": "f(xₙ)", "field": "f_actual"},
                {"name": "x_siguiente", "label": "xₙ₊₁", "field": "x_siguiente"},
                {"name": "f_siguiente", "label": "f(xₙ₊₁)", "field": "f_siguiente"},
                {"name": "error", "label": "|Δx|", "field": "error"},
            ]
            with self.contenedor_tabla:
                ui.table(columns=columnas, rows=filas, row_key="i").classes("w-full").props("dense wrap-cells")
        else:
            with self.contenedor_tabla:
                ui.label("No se necesitaron iteraciones: una aproximación inicial ya era una raíz.").classes(
                    "texto-secundario"
                )


def _metrica(etiqueta: str, valor: str) -> None:
    """Renderiza una métrica del resultado."""
    with ui.column().classes("gap-1"):
        ui.label(etiqueta).classes("text-sm texto-secundario")
        ui.label(valor).classes("font-semibold texto-principal")


def _numero(valor: float | None) -> str:
    """Presenta valores finitos sin alterar la precisión utilizada por el motor."""
    return "—" if valor is None else f"{valor:.10g}"
