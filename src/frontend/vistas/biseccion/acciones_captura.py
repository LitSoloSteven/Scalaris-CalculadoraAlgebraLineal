"""Ayuda, opciones avanzadas y acciones secundarias de la captura."""
from nicegui import ui

from src.backend.resolutores.raices.contrato_biseccion import D_MAXIMO, LIMITE_ITERACIONES_DEFECTO
from src.frontend.componentes.limpieza_captura import crear_boton_limpieza
from src.frontend.controladores.biseccion.catalogo_criterios import CRITERIOS
from src.frontend.controladores.biseccion.controlador import LIMITE_ITERACIONES_INTERFAZ
from .captura import GUIA_CONTINUIDAD
from .ejemplos import EJEMPLOS


def desplegable(titulo: str):
    """Crea una sección nativa operable con teclado y sin transición."""
    seccion = ui.element("details").classes("biseccion-desplegable w-full")
    with seccion, ui.element("summary").classes("texto-principal"):
        ui.label(titulo)
    return seccion


def construir_acciones(vista) -> None:
    """Monta ayuda, catálogo y limpieza para ambas tareas."""
    with desplegable("Ejemplos"):
        _construir_ejemplos(vista)
    with desplegable("Ayuda"):
        _construir_ayuda()
    with ui.row().classes("w-full gap-3"):
        crear_boton_limpieza(vista, lambda: not vista.contenedor_resultados.is_deleted,
                             animar=False, campo_foco=vista.expresion)


def _construir_ejemplos(vista) -> None:
    for grupo, ejercicios in EJEMPLOS.items():
        ui.label(grupo).classes("text-sm font-semibold texto-secundario")
        with ui.row().classes("w-full gap-2"):
            for etiqueta, captura in ejercicios:
                ui.button(etiqueta, color=None, on_click=lambda captura=captura: vista.cargar_captura(
                    captura)).classes("boton-discreto").props("ripple=false")


def construir_limite(vista) -> None:
    """Monta el límite vigente dentro de Avanzado."""
    vista.limite = ui.number("Límite de iteraciones", value=LIMITE_ITERACIONES_DEFECTO, min=1,
                             max=LIMITE_ITERACIONES_INTERFAZ, step=1).classes("w-full matriz-entrada")


def mostrar_recientes(vista) -> None:
    """Lista los ejercicios de esta sesión con su configuración restaurable."""
    vista.recientes.clear()
    with vista.recientes:
        ui.label("Recientes de esta sesión:").classes("text-sm texto-secundario")
        for indice, calculo in enumerate(vista.historial, 1):
            captura = calculo["captura"]
            criterio = captura.get("criterio", {"tipo": "decimales", "parametro": captura["decimales"]})
            etiqueta = f"{CRITERIOS[criterio['tipo']][0]} · {criterio['parametro']} · {captura.get('unidad_angular', 'radianes')}"
            ui.button(f"{indice} · {calculo['titulo']} · {etiqueta}", color=None,
                      on_click=lambda captura=captura: vista.cargar_captura(captura)).classes(
                          "boton-discreto").tooltip(str(captura["expresion"]))


def _construir_ayuda() -> None:
    textos = (
        "Usa x, +, −, *, /, ^ o ** y paréntesis. Se admiten 2x, 3sin(x), 2(x+1), (x+1)(x-1), x² y x³. "
        "La potencia precede al signo: -x² = -(x²).",
        "Funciones: sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, exp, sqrt y abs. "
        "ln y log son naturales; log10 y log2 usan base 10 y 2. Constantes: pi y e.",
        "La unidad se aplica a sin, cos y tan, y a los resultados de asin, acos y atan. "
        "Las funciones hiperbólicas y la constante pi conservan su valor.",
        f"La aritmética de punto flotante es aproximada. d va de 0 a {D_MAXIMO}. "
        "La precisión alcanzable depende del intervalo. Las iteraciones usan los valores internos.",
        "El criterio solicita una condición de parada. El motivo de parada indica qué ocurrió. "
        "Un cero evaluado en un extremo produce cero filas. El conteo fijo y los límites pueden dejar una aproximación provisional.",
        "Interpreta como provisional el punto medio ante una sospecha de discontinuidad. "
        "Si una evaluación falla, la tabla conserva las filas válidas anteriores.",
        "En Modo examen puedes ver el signo de f(a)·f(c) y el extremo actualizado en cada fila. "
        "El lote tiene su propio control.",
        "La exploración evalúa la función en una malla con separación h. Un paso menor toma más muestras.",
        GUIA_CONTINUIDAD,
        "Los ejemplos y los recientes cargan los datos. Pulsa Calcular raíz para obtener un resultado.",
    )
    for texto in textos:
        ui.label(texto).classes("block text-sm texto-secundario")
