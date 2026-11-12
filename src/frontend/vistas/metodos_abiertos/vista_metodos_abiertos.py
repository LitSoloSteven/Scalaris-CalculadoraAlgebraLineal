"""Vista mínima de Newton-Raphson y secante con selección sobre la gráfica y captura manual."""
import math

import plotly.graph_objects as go
from nicegui import ui

from src.frontend.componentes.estructura_aplicacion import crear_estructura_aplicacion
from src.frontend.componentes.figura_funcion_real import crear_figura_previa
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.controladores.captura_real import real_capturado
from src.frontend.controladores.metodos_abiertos import calcular
from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from src.frontend.navegacion import ruta_de
from src.frontend.tema import PALETA_GRAFICOS


class VistaMetodosAbiertos:
    """Grafica primero, permite fijar puntos con clics o texto, y calcula iteraciones."""

    def __init__(self) -> None:
        self.metodo = "newton"
        self._marcas: list[tuple[float, float, str]] = []
        self.grafica = None
        self.resultado = None
        self.estado = None

    def construir(self) -> None:
        """Monta la herramienta completa."""
        crear_estructura_aplicacion(self, ruta_activa=ruta_de("metodos_abiertos"))

        with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-4 vista-raiz"):
            ui.label("Métodos abiertos").classes("text-2xl font-bold texto-principal")
            ui.label("Grafica, elige el punto en la curva o escríbelo, y después calcula.").classes("texto-secundario")

            # Fila de configuración superior
            with ui.row().classes("w-full gap-3 flex-wrap"):
                ui.select(
                    {"newton": "Newton-Raphson", "secante": "Secante"},
                    value="newton",
                    label="Método",
                    on_change=lambda e: self._cambiar_metodo(e.value),
                ).classes("w-48")
                self.expresion = ui.input("f(x)", value="x^2 - 2").classes("flex-1 min-w-0 matriz-entrada")
                self.minimo = ui.input("x mínimo", value="-5").classes("w-32 matriz-entrada")
                self.maximo = ui.input("x máximo", value="5").classes("w-32 matriz-entrada")

            # Fila de parámetros del método
            with ui.row().classes("w-full gap-3 flex-wrap items-center"):
                self.tolerancia = ui.input("Tolerancia", value="1e-6").classes("w-36 matriz-entrada")
                self.limite = ui.input("Límite de iteraciones", value="100").classes("w-44 matriz-entrada")
                
                self.input_x0 = ui.input("Punto x0", value="").classes("w-36 matriz-entrada").props("inputmode=decimal")
                self.input_x1 = ui.input("Punto x1", value="").classes("w-36 matriz-entrada").props("inputmode=decimal")
                self.input_x1.set_visibility(False)

                self.input_x0.on("blur", self._sincronizar_desde_inputs)
                self.input_x1.on("blur", self._sincronizar_desde_inputs)

                ui.button("Graficar", icon="show_chart", color=None,
                          on_click=self.graficar).classes("boton-principal").props("ripple=false")

            self.estado = ui.label("Escribe f(x) y pulsa Graficar.").classes(
                "texto-secundario").props("role=status aria-live=polite")

            self.grafica = ui.plotly(go.Figure()).classes("w-full h-80")
            self.grafica.on("plotly_click", self._clic)

            ui.button("Calcular", icon="calculate", color=None,
                      on_click=self.calcular).classes("boton-principal mt-2").props("ripple=false")

            self.resultado = ui.column().classes("w-full gap-4 mt-4")

    def _cambiar_metodo(self, metodo: str) -> None:
        self.metodo = metodo
        self.input_x1.set_visibility(metodo == "secante")
        self.input_x0.set_value("")
        self.input_x1.set_value("")
        self._marcas.clear()
        self._actualizar_marcas()
        self.resultado.clear()
        self.estado.set_text("Haz clic en la curva o escribe el punto. Luego presiona Calcular.")

    def graficar(self) -> None:
        """Dibuja la curva y prepara una traza vacía para las marcas."""
        respuesta = preparar_vista_previa({
            "expresion": self.expresion.value,
            "x_min": self.minimo.value,
            "x_max": self.maximo.value,
            "unidad_angular": "radianes",
        })
        if respuesta["estado"] != "EXITO":
            self.estado.set_text(respuesta["mensaje"])
            return

        figura = crear_figura_previa(respuesta)
        
        # Forzar el rango del eje X para que no haga zoom a los valores válidos
        try:
            min_x = float(self.minimo.value)
            max_x = float(self.maximo.value)
            figura.update_xaxes(range=[min_x, max_x], autorange=False)
        except ValueError:
            pass

        # Permitir clics en la línea
        figura.update_layout(clickmode='event')
        if figura.data:
            figura.data[0].mode = 'lines+markers'
            figura.data[0].marker = dict(size=0, opacity=0)

        figura.add_trace(go.Scatter(
            x=[], y=[], mode="markers+text", textposition="top center",
            name="Puntos elegidos",
            marker=dict(color=PALETA_GRAFICOS[1], size=12),
        ))
        self.grafica.update_figure(figura)
        
        self._sincronizar_desde_inputs()
        self.estado.set_text("Haz clic en la curva o escribe los puntos. Luego presiona Calcular.")
        self.resultado.clear()

    def _clic(self, evento) -> None:
        """Toma la x real del clic, actualiza las marcas y los campos de texto."""
        if not evento.args or not isinstance(evento.args, dict):
            return
            
        puntos = evento.args.get("points") or []
        if not puntos:
            return
            
        x = puntos[0].get("x")
        y = puntos[0].get("y")
        
        try:
            x = float(x)
            y = float(y) if y is not None else 0.0
        except (ValueError, TypeError):
            return

        if self.metodo == "newton":
            self._marcas = [(x, y, "x0")]
            self.input_x0.set_value(f"{x:.6g}")
        else:
            if len(self._marcas) >= 2:
                self._marcas = []
                self.input_x0.set_value("")
                self.input_x1.set_value("")
            
            self._marcas.append((x, y, "x0" if not self._marcas else "x1"))
            if len(self._marcas) == 1:
                self.input_x0.set_value(f"{x:.6g}")
            else:
                self.input_x1.set_value(f"{x:.6g}")

        self._actualizar_marcas()
        self.estado.set_text("Punto fijado. Pulsa Calcular.")
        self.resultado.clear()

    def _sincronizar_desde_inputs(self) -> None:
        """Lee los campos de texto y actualiza los marcadores en la gráfica."""
        try:
            x0 = real_capturado(self.input_x0.value, "x0")
        except ValueError:
            self._marcas = []
            self._actualizar_marcas()
            return

        self._marcas = [(x0, 0.0, "x0")]
        
        if self.metodo == "secante" and self.input_x1.value:
            try:
                x1 = real_capturado(self.input_x1.value, "x1")
                self._marcas.append((x1, 0.0, "x1"))
            except ValueError:
                pass

        self._actualizar_marcas()

    def _actualizar_marcas(self) -> None:
        if self.grafica is None or self.grafica.is_deleted:
            return
        xs = [m[0] for m in self._marcas]
        ys = [m[1] for m in self._marcas]
        textos = [m[2] for m in self._marcas]
        self.grafica.run_plot_method(
            "restyle", {"x": [xs], "y": [ys], "text": [textos]}, [1]
        )

    def calcular(self) -> None:
        """Ejecuta el método usando los valores de los campos de texto."""
        try:
            x0 = real_capturado(self.input_x0.value, "x0")
            x1 = None
            if self.metodo == "secante":
                x1 = real_capturado(self.input_x1.value, "x1")
        except ValueError as error:
            self.estado.set_text(str(error))
            return

        respuesta = calcular({
            "metodo": self.metodo,
            "expresion": self.expresion.value,
            "x0": x0,
            "x1": x1,
            "tolerancia": self.tolerancia.value,
            "limite_iteraciones": self.limite.value,
            "unidad_angular": "radianes",
        })

        self.resultado.clear()
        with self.resultado:
            if respuesta["estado"] == "ERROR":
                with ui.row().classes("items-center gap-2 px-4 py-2 distintivo-error w-fit"):
                    ui.icon("warning", size="sm")
                    ui.label(respuesta.get("mensaje", "")).classes("font-bold")
                ui.label("El método se detuvo de forma segura porque el siguiente valor de x cayó fuera del dominio de la función o la derivada se hizo cero.").classes("text-sm texto-secundario")
            else:
                with ui.row().classes("items-center gap-2 px-4 py-2 distintivo-exito w-fit"):
                    ui.icon("check", size="sm")
                    ui.label(respuesta.get("mensaje", "")).classes("font-bold")
                
                if respuesta.get("raiz") is not None:
                    ui.label(f"Raíz aproximada: {respuesta['raiz']:.12g}").classes("font-mono texto-principal text-lg mt-2")

            # Mostrar la fórmula matemática usando MathJax
            if self.metodo == "newton":
                renderizar_latex(r"x_{i+1} = x_i - \frac{f(x_i)}{f'(x_i)}")
                columna_derivada = "f'(x)"
            else:
                renderizar_latex(r"x_{i+1} = x_i - f(x_i)\frac{x_i - x_{i-1}}{f(x_i) - f(x_{i-1})}")
                columna_derivada = "Pendiente"

            if respuesta.get("iteraciones"):
                ui.table(
                    columns=[
                        {"name": "i", "label": "i", "field": "i", "align": "left"},
                        {"name": "x", "label": "x_i", "field": "x", "align": "left"},
                        {"name": "fx", "label": "f(x_i)", "field": "fx", "align": "left"},
                        {"name": "derivada", "label": columna_derivada, "field": "derivada", "align": "left"},
                        {"name": "error", "label": "Error", "field": "error", "align": "left"},
                    ],
                    rows=[
                        {
                            "i": fila["i"], 
                            "x": f"{fila['x']:.12g}",
                            "fx": f"{fila['fx']:.12g}",
                            "derivada": "—" if fila.get("derivada") is None else f"{fila['derivada']:.6g}",
                            "error": "—" if fila["error"] is None else f"{fila['error']:.6g}"
                        }
                        for fila in respuesta["iteraciones"]
                    ],
                    row_key="i",
                ).classes("w-full").props("flat bordered")
            
            self.estado.set_text(respuesta.get("mensaje", ""))