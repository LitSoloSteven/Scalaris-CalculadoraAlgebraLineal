"""Requisitos por método y guía bajo demanda para métodos cerrados."""
from nicegui import ui

from src.backend.resolutores.raices.biseccion.contratos.contrato_biseccion import D_MAXIMO
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA

REQUISITOS_METODO = {
    BISECCION: (
        "Requisito de Bisección: f(x) continua en [a, b] y cambio de signo f(a)·f(b) < 0."
    ),
    REGLA_FALSA: (
        "Requisito de Regla falsa: f(x) continua en [a, b], cambio de signo f(a)·f(b) < 0 "
        "y f(b) distinto de f(a)."
    ),
}

_BLOQUES_AYUDA = (
    (
        "Expresión y funciones",
        (
            "Usa x, +, −, *, /, ^ o ** y paréntesis. Se admiten 2x, 3sin(x), 2(x+1), "
            "(x+1)(x-1), x² y x³. La potencia precede al signo: -x² = -(x²).",
            "Funciones: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, abs, "
            "sqrt (√), cbrt (∛) y raiz4 (∜). ln y log son naturales; log10 y log2 usan "
            "base 10 y 2. Constantes: pi y e.",
        ),
    ),
    (
        "Unidades y precisión",
        (
            "La unidad se aplica a sin, cos y tan, y a los resultados de asin, acos y atan. "
            "Las funciones hiperbólicas y la constante pi conservan su valor.",
            f"La aritmética de punto flotante es aproximada. El parámetro d va de 0 a {D_MAXIMO}. "
            "La precisión alcanzable depende del intervalo y las iteraciones usan valores internos.",
        ),
    ),
    (
        "Continuidad y parada",
        (
            "La garantía requiere continuidad en todo [a, b]. Un cambio de signo y una "
            "gráfica muestreada no demuestran continuidad.",
            "El criterio solicita una condición de parada y el motivo indica qué ocurrió. "
            "Un cero evaluado en un extremo produce cero filas.",
            "La exploración evalúa la función en una malla con separación h. En Bisección, "
            "el punto medio se marca provisional ante sospecha de discontinuidad.",
        ),
    ),
)


def construir_ayuda_cerrados() -> None:
    """Construye la guía estructurada de sintaxis, precisión y continuidad."""
    with ui.column().classes("w-full min-w-0 gap-3"):
        for titulo, parrafos in _BLOQUES_AYUDA:
            with ui.column().classes("metodos-cerrados-ayuda-grupo w-full min-w-0 gap-1"):
                ui.label(titulo).classes("metodos-cerrados-ayuda-titulo text-sm font-semibold texto-principal")
                for texto in parrafos:
                    ui.label(texto).classes("block text-sm texto-secundario")
