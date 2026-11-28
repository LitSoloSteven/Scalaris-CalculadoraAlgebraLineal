"""Requisitos por método, secciones secundarias y guía bajo demanda."""
from collections.abc import Callable

from nicegui import ui

from src.backend.resolutores.raices.biseccion.contratos.contrato_biseccion import D_MAXIMO
from src.backend.resolutores.raices.compartido.limites_raices import LIMITE_ITERACIONES_DEFECTO
from src.frontend.componentes.raices.captura.estructura_metodos_raices import crear_seccion_plegable
from src.frontend.controladores.raices.compartido.formato.rango_exploracion_raices import RANGO_GRAFICA_DEFECTO
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
            _construir_bloque_ayuda(titulo, parrafos)


def _construir_bloque_ayuda(titulo: str, parrafos: tuple[str, ...]) -> None:
    with ui.column().classes("metodos-cerrados-ayuda-grupo w-full min-w-0 gap-1"):
        ui.label(titulo).classes("metodos-cerrados-ayuda-titulo text-sm font-semibold texto-principal")
        for texto in parrafos:
            ui.label(texto).classes("block text-sm texto-secundario")


def construir_secciones_secundarias(captura, crear_campo: Callable) -> None:
    """Monta Avanzado, Sintaxis bajo demanda y el contenedor de recientes."""
    with ui.column().classes("metodos-cerrados-secundarias w-full min-w-0 gap-3"):
        captura.seccion_avanzado = crear_seccion_plegable(
            "Avanzado",
            icono="tune",
            subtitulo="Límite de iteraciones y rango de la gráfica",
        )
        _poblar_avanzado(captura, crear_campo)
        captura.seccion_sintaxis = crear_seccion_plegable(
            "Sintaxis y continuidad",
            icono="menu_book",
            subtitulo="Funciones admitidas y criterio del intervalo",
        )
        _conectar_sintaxis_bajo_demanda(captura)
        captura.contenedor_historial = ui.column().classes("w-full min-w-0")


def _poblar_avanzado(captura, crear_campo: Callable) -> None:
    with captura.seccion_avanzado, ui.row().classes("metodos-raices-campos w-full"):
        captura.limite = crear_campo("Límite de iteraciones", str(LIMITE_ITERACIONES_DEFECTO), "entero")
        minimo, maximo = RANGO_GRAFICA_DEFECTO
        captura.minimo = crear_campo("Mínimo de la gráfica", str(minimo))
        captura.maximo = crear_campo("Máximo de la gráfica", str(maximo))


def _conectar_sintaxis_bajo_demanda(captura) -> None:
    def _al_abrir(evento) -> None:
        if evento.value and not captura._ayuda_montada and not captura.seccion_sintaxis.is_deleted:
            captura._ayuda_montada = True
            with captura.seccion_sintaxis:
                construir_ayuda_cerrados()

    captura.seccion_sintaxis.on_value_change(_al_abrir)
