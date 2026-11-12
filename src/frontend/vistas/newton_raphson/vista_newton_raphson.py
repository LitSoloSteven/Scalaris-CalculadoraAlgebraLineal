"""Vista de Scalaris para resolver ecuaciones con Newton-Raphson."""
from nicegui import ui

from src.backend.resolutores.raices.newton_raphson import (
    EntradaNewtonRaphson,
    ResultadoNewtonRaphson,
    newton_raphson,
)
from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.controladores.captura_real import entero_capturado, real_capturado
from src.frontend.controladores.graficas_metodos_abiertos import crear_figura_newton_raphson
from src.frontend.navegacion import ruta_de


class VistaNewtonRaphson:
    """Captura f(x), f'(x) y x₀; presenta la aproximación y la traza."""

    def __init__(self) -> None:
        self.ultimo_resultado: ResultadoNewtonRaphson | None = None
        self.panel_ia = None

    def construir(self) -> None:
        """Monta la página con la navegación, los campos y el resultado."""
        self.panel_ia = PanelIA(self)
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("newton_raphson"))

        with ui.column().classes("vista-raiz w-full mx-auto p-4 gap-5").style("max-width: 1180px"):
            with ui.column().classes("w-full gap-2"):
                ui.label("Método de Newton-Raphson").classes("text-2xl font-bold texto-principal")
                ui.label(
                    "Método abierto que utiliza la función, su derivada y una aproximación inicial "
                    "para acercarse a una raíz de una ecuación no lineal."
                ).classes("texto-secundario")

            with ui.element("div").classes("grid grid-cols-1 lg:grid-cols-2 gap-5 w-full"):
                with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                    ui.label("Datos de entrada").classes("text-lg font-semibold texto-principal")
                    self.expresion = ui.input(
                        "Función f(x)", value="x^2 - 2", placeholder="Ejemplo: x^3 - x - 2"
                    ).classes("w-full matriz-entrada").props("maxlength=512 autocomplete=off spellcheck=false")
                    self.derivada = ui.input(
                        "Derivada f'(x)", value="2*x", placeholder="Ejemplo: 3*x^2 - 1"
                    ).classes("w-full matriz-entrada").props("maxlength=512 autocomplete=off spellcheck=false")
                    ui.label(
                        "Introduce la derivada correcta de la función; el programa evalúa f'(x), no la obtiene automáticamente."
                    ).classes("text-xs texto-secundario")
                    self.inicial = ui.input(
                        "Aproximación inicial x₀", value="1.5"
                    ).classes("w-full matriz-entrada").props("inputmode=decimal")
                    with ui.element("div").classes("grid grid-cols-1 sm:grid-cols-2 gap-3 w-full"):
                        self.tolerancia = ui.input("Tolerancia", value="0.000001").classes(
                            "w-full matriz-entrada"
                        ).props("inputmode=decimal")
                        self.limite = ui.input("Límite de iteraciones", value="100").classes(
                            "w-full matriz-entrada"
                        ).props("inputmode=numeric")
                    with ui.row().classes("items-center gap-2 w-full"):
                        ui.button(
                            "Cargar ejemplo", icon="science", color=None, on_click=self.cargar_ejemplo
                        ).props("outline")
                        self.boton_resolver = ui.button(
                            "Calcular raíz", icon="calculate", color=None, on_click=self.resolver
                        ).classes("boton-principal").props("ripple=false")

                with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                    ui.label("Resultado").classes("text-lg font-semibold texto-principal")
                    self.estado = ui.label(
                        "Introduce la función, su derivada y un valor inicial para comenzar."
                    ).classes("texto-secundario").props("role=status aria-live=polite aria-atomic=true")
                    self.contenedor_resultado = ui.column().classes("w-full gap-3")
                    ui.separator()
                    ui.label("Fórmula del método").classes("font-semibold texto-principal")
                    ui.markdown(r"\[x_{n+1}=x_n-\frac{f(x_n)}{f'(x_n)}\]")
                    ui.label(
                        "La derivada indica la pendiente de la tangente a la curva. "
                        "El siguiente valor se obtiene donde esa tangente corta el eje x."
                    ).classes("text-sm texto-secundario")

            with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Gráfica de la función").classes("text-lg font-semibold texto-principal")
                    self.opcion_grafica = ui.switch("Mostrar gráfica", value=True)
                self.estado_grafica = ui.label(
                    "La gráfica aparecerá después de realizar el cálculo."
                ).classes("text-sm texto-secundario").props("role=status aria-live=polite")
                self.contenedor_grafica = ui.column().classes("w-full min-w-0")
                self.contenedor_grafica.bind_visibility_from(self.opcion_grafica, "value")
                self.opcion_grafica.on_value_change(self._alternar_grafica)
                ui.label(
                    "La curva muestra f(x), las aproximaciones y la última recta tangente. "
                    "Los huecos del dominio no se conectan."
                ).classes("text-xs texto-secundario")

            with ui.column().classes("panel-tarjeta w-full p-6 gap-4"):
                ui.label("Procedimiento e iteraciones").classes("text-lg font-semibold texto-principal")
                ui.label(
                    "En cada fila se muestra f(xₙ), f'(xₙ), la nueva aproximación y el error absoluto."
                ).classes("text-sm texto-secundario")
                self.contenedor_tabla = ui.column().classes("w-full min-w-0")

            ui.label(
                "Nota: el método puede no converger si la aproximación inicial es inadecuada "
                "o si la derivada se anula durante el proceso."
            ).classes("text-sm texto-secundario")

        self.panel_ia.construir()
        self._enlazar_cambios()

    def _enlazar_cambios(self) -> None:
        """Invalida el resultado anterior cuando se modifica cualquier entrada."""
        for campo in (self.expresion, self.derivada, self.inicial, self.tolerancia, self.limite):
            campo.on_value_change(self._datos_modificados)

    def _datos_modificados(self) -> None:
        """Evita mostrar una solución que corresponde a datos anteriores."""
        self.ultimo_resultado = None
        self.contenedor_resultado.clear()
        self.contenedor_tabla.clear()
        self.contenedor_grafica.clear()
        self.estado_grafica.set_text("La gráfica aparecerá después de realizar el cálculo.")
        self.estado.set_text("Datos modificados. Calcula de nuevo para obtener un resultado vigente.")

    def _alternar_grafica(self, evento=None) -> None:
        """Muestra u oculta la gráfica sin volver a ejecutar Newton-Raphson."""
        if self.opcion_grafica.value:
            self._actualizar_grafica()

    def _actualizar_grafica(self) -> None:
        """Dibuja la curva y la última recta tangente del resultado vigente."""
        self.contenedor_grafica.clear()
        if self.ultimo_resultado is None:
            self.estado_grafica.set_text("Calcula una raíz para generar la gráfica.")
            return
        try:
            figura = crear_figura_newton_raphson(self.ultimo_resultado)
        except (ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError):
            self.estado_grafica.set_text("No se pudo dibujar la función con el rango actual.")
            return
        self.estado_grafica.set_text(
            "Curva de la función, puntos de aproximación y última recta tangente."
        )
        with self.contenedor_grafica:
            ui.plotly(figura).classes("w-full")


    def cargar_ejemplo(self) -> None:
        """Carga f(x)=x²−2, f'(x)=2x y x₀=1.5."""
        self.expresion.value = "x^2 - 2"
        self.derivada.value = "2*x"
        self.inicial.value = "1.5"
        self.tolerancia.value = "0.000001"
        self.limite.value = "100"
        self._datos_modificados()

    def resolver(self) -> None:
        """Convierte los valores de captura y ejecuta el motor Newton-Raphson."""
        try:
            entrada = EntradaNewtonRaphson(
                expresion=self.expresion.value or "",
                derivada=self.derivada.value or "",
                aproximacion_inicial=real_capturado(self.inicial.value, "La aproximación inicial"),
                tolerancia=real_capturado(self.tolerancia.value, "La tolerancia"),
                limite_iteraciones=entero_capturado(self.limite.value, "El límite de iteraciones"),
            )
        except ValueError as error:
            ui.notify(str(error), type="negative")
            return

        self.ultimo_resultado = newton_raphson(entrada)
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
                    "x_actual": _numero(fila.x_actual),
                    "valor_funcion": _numero(fila.valor_funcion),
                    "valor_derivada": _numero(fila.valor_derivada),
                    "x_siguiente": _numero(fila.x_siguiente),
                    "valor_siguiente": _numero(fila.valor_siguiente),
                    "error_absoluto": _numero(fila.error_absoluto),
                }
                for fila in resultado.iteraciones
            ]
            columnas = [
                {"name": "i", "label": "n", "field": "i", "align": "left"},
                {"name": "x_actual", "label": "xₙ", "field": "x_actual"},
                {"name": "valor_funcion", "label": "f(xₙ)", "field": "valor_funcion"},
                {"name": "valor_derivada", "label": "f'(xₙ)", "field": "valor_derivada"},
                {"name": "x_siguiente", "label": "xₙ₊₁", "field": "x_siguiente"},
                {"name": "valor_siguiente", "label": "f(xₙ₊₁)", "field": "valor_siguiente"},
                {"name": "error_absoluto", "label": "|Δx|", "field": "error_absoluto"},
            ]
            with self.contenedor_tabla:
                ui.table(columns=columnas, rows=filas, row_key="i").classes("w-full").props("dense wrap-cells")
        else:
            with self.contenedor_tabla:
                ui.label("No se necesitaron iteraciones: la aproximación inicial ya era una raíz.").classes(
                    "texto-secundario"
                )
        self._actualizar_grafica()


def _metrica(etiqueta: str, valor: str) -> None:
    """Renderiza una métrica del resultado."""
    with ui.column().classes("gap-1"):
        ui.label(etiqueta).classes("text-sm texto-secundario")
        ui.label(valor).classes("font-semibold texto-principal")


def _numero(valor: float | None) -> str:
    """Presenta valores finitos sin alterar la precisión interna del cálculo."""
    return "—" if valor is None else f"{valor:.10g}"
