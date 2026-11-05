"""Controles de captura y ejemplos identificados para la búsqueda de raíces."""
from nicegui import ui

from src.backend.resolutores.raices.contrato_biseccion import D_MAXIMO, LONGITUD_MAXIMA_EXPRESION, LIMITE_ITERACIONES_DEFECTO
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.controladores.biseccion.controlador import LIMITE_ITERACIONES_INTERFAZ
from .selector_criterio import construir_selector
from .selector_unidad import construir_selector_unidad

GUIA_CONTINUIDAD = "La garantía requiere continuidad en todo [a, b]. Un cambio de signo y una gráfica muestreada no demuestran continuidad."


def construir_captura(vista) -> None:
    """Monta campos etiquetados, tolerancia reactiva, ayuda y acciones compartidas."""
    with ui.column().classes("panel-tarjeta biseccion-captura w-full gap-4 p-6"):
        ui.label("Método de bisección").classes("text-2xl font-bold texto-principal")
        ui.label("Acota una raíz y observa cómo se reduce su intervalo.").classes("texto-secundario")
        vista.expresion = ui.input("Función f(x)", placeholder="Ejemplo: x^2 - 2").classes("w-full matriz-entrada").props(
            f'maxlength={LONGITUD_MAXIMA_EXPRESION} autocomplete=off spellcheck=false')
        construir_selector_unidad(vista)
        with ui.element("div").classes("biseccion-campos"):
            vista.inferior = _campo_extremo("Extremo inferior a")
            vista.superior = _campo_extremo("Extremo superior b")
        construir_selector(vista)
        _construir_ayuda(vista)
        _mostrar_ejemplos(vista)
        with ui.row().classes("w-full gap-3"):
            crear_boton_limpieza(vista, lambda: not vista.contenedor_resultados.is_deleted, lambda: list(vista._campos_captura()))
            vista.boton_resolver = ui.button("Calcular raíz", icon="calculate", color=None, on_click=vista.resolver).classes("boton-principal flex-1").props("ripple=false")


def _campo_extremo(etiqueta: str):
    return ui.input(etiqueta, placeholder="0").classes("w-full matriz-entrada").props('inputmode=decimal maxlength=64 autocomplete=off')


def _ejercicio(expresion: str, inferior: str, superior: str, **preferencias) -> dict:
    return {"expresion": expresion, "extremo_izquierdo": inferior, "extremo_derecho": superior, **preferencias}


EJEMPLOS = (
    ("Raíz de 2", _ejercicio("x^2 - 2", "1", "2")),
    ("Polinomio del Excel", _ejercicio("x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10", "0.6", "1")),
    ("Potencia décima", _ejercicio("x^10 - 1", "0", "1.3")),
    ("Cero en un extremo", _ejercicio("x² − 4", "2", "3", criterio={"tipo": "decimales", "parametro": 4},
                                      limite_iteraciones=LIMITE_ITERACIONES_DEFECTO)),
    ("Tres iteraciones", _ejercicio("x² − 2", "1", "2", criterio={"tipo": "iteraciones", "parametro": 3},
                                    limite_iteraciones=LIMITE_ITERACIONES_DEFECTO)),
    ("Posible discontinuidad", _ejercicio("1/(x² − 0.2)", "0", "1", criterio={"tipo": "decimales", "parametro": 4},
                                          limite_iteraciones=LIMITE_ITERACIONES_DEFECTO)),
    ("Seno en grados", _ejercicio("2sin(x) − 1", "0", "60", unidad_angular="grados",
                                 criterio={"tipo": "decimales", "parametro": 4},
                                 limite_iteraciones=LIMITE_ITERACIONES_DEFECTO)),
)


def _mostrar_ejemplos(vista) -> None:
    with ui.row().classes("w-full gap-2 items-center"):
        ui.label("Cargar ejemplo").classes("text-sm texto-secundario")
        for etiqueta, captura in EJEMPLOS:
            ui.button(etiqueta, color=None, on_click=lambda captura=captura: vista.cargar_captura(captura)).classes(
                "boton-discreto").props("ripple=false")


def _construir_ayuda(vista) -> None:
    with ui.expansion("Sintaxis y límites", icon="help_outline").classes("w-full texto-secundario"):
        ui.label("Usa x, +, −, *, /, ^ o ** y paréntesis. Se admiten 2x, 3sin(x), 2(x+1), (x+1)(x-1), x² y x³. "
                 "La potencia precede al signo: -x² = -(x²).").classes("text-sm")
        ui.label("Funciones: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, sqrt y abs. "
                 "ln y log son naturales; log10 y log2 usan base 10 y 2. Constantes: pi y e. "
                 "La unidad trigonométrica elegida se conserva al calcular y explorar.").classes("text-sm")
        ui.label(f"Aritmética aproximada de punto flotante de Python; d entre 0 y {D_MAXIMO}. No se redondean las iteraciones para calcular. Una precisión dentro de este rango puede no ser alcanzable para tu intervalo.").classes("text-sm")
        ui.label(GUIA_CONTINUIDAD).classes("text-sm")
        vista.limite = ui.number("Límite de iteraciones", value=LIMITE_ITERACIONES_DEFECTO, min=1,
                                 max=LIMITE_ITERACIONES_INTERFAZ, step=1).classes("w-full matriz-entrada")
    with ui.expansion("Cómo leer el resultado", icon="help_outline").classes("w-full texto-secundario"):
        ui.label("El criterio solicitado fija la condición del cálculo. El motivo de parada indica qué ocurrió. "
                 "Un cero evaluado en un extremo produce cero filas. El conteo fijo y los límites pueden dejar una aproximación provisional.").classes("text-sm")
        ui.label("Ante una sospecha de discontinuidad, interpreta el punto medio como provisional. "
                 "Si una evaluación falla, la tabla conserva las filas válidas anteriores al fallo.").classes("text-sm")
        ui.label("Activa Modo examen para ver el signo de f(a)·f(c) y el extremo que cambió en cada fila. "
                 "Una fila que detiene el cálculo no cambia los extremos. El lote tiene su propio control.").classes("text-sm")
        ui.label("Los ejemplos y los recientes solo cargan los datos. Pulsa Calcular raíz para obtener un resultado vigente.").classes("text-sm")
