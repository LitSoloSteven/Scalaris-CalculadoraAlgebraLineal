"""Presentacion de comprobaciones preparadas por el backend sin reinterpretar sus datos."""
from nicegui import ui
from src.frontend.componentes.datos_desarrollo import es_traza_producto, agrupar_filas_producto
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos import textos
from src.frontend.componentes.reproductor_pasos.textos import formatear_descripcion_html


def mostrar_desarrollo(traza: list[dict], titulo: str = "Ver desarrollo de la comprobacion") -> None:
    """Muestra identidad, sustitucion, desarrollo y conclusion en una expansion accesible."""
    if not traza:
        return
    if es_traza_producto(traza):
        _mostrar_producto(traza, titulo)
        return
    _mostrar_resumen_plano(traza)
    _crear_detalle_diferido(titulo, lambda: _mostrar_pasos(traza[1:-1]))


def _mostrar_resumen_plano(traza: list[dict]) -> None:
    """Conserva planteamiento y conclusión visibles sin montar los pasos intermedios."""
    _mostrar_paso(traza[0])
    if len(traza) > 1:
        _mostrar_paso(traza[-1])
    if any(str(paso.get("descripcion", "")).startswith("Propiedad por comprobar:") for paso in traza):
        ui.label(textos.COMPROBACION_PROPIEDAD).classes("font-bold texto-principal")
        renderizar_latex(textos.COMPROBACION_CELDA_GUIA)
        conclusion = next((paso for paso in traza if str(paso.get("descripcion", "")).startswith(
            "Comprobacion exacta de ")), None)
        if conclusion and conclusion is not traza[-1]:
            renderizar_latex(conclusion["detalle_latex"])


def _mostrar_producto(traza: list[dict], titulo: str) -> None:
    """Presenta el veredicto y la igualdad antes del detalle diferido por filas."""
    ui.label(textos.COMPROBACION_PROPIEDAD).classes("font-bold texto-principal")
    ui.html(formatear_descripcion_html(traza[0]["detalle_latex"])).classes("texto-principal")
    es_inversa = traza[0]["detalle_latex"] == "AA^{-1}=I"
    ui.label(textos.COMPROBACION_CONTEXTO_INVERSA if es_inversa else
             textos.COMPROBACION_CONTEXTO_PRODUCTO).classes("texto-secundario")
    coincide = traza[-1]["descripcion"].endswith(": coincide")
    ui.label(textos.COMPROBACION_CORRECTA if coincide else textos.COMPROBACION_INCORRECTA).classes(
        "distintivo-exito" if coincide else "distintivo-error").props('role="status"')
    renderizar_latex(traza[-1]["detalle_latex"])
    renderizar_latex(textos.COMPROBACION_CELDA_GUIA)
    _crear_detalle_diferido(titulo, lambda: _mostrar_filas(traza))


def _mostrar_filas(traza: list[dict]) -> None:
    """Crea una expansión por fila, sin componer todavía sus fórmulas."""
    for fila, detalles in agrupar_filas_producto(traza).items():
        formula = r"\begin{array}{l}" + r" \\ ".join(detalles) + r"\end{array}"
        _crear_detalle_diferido(textos.COMPROBACION_FILA.format(fila=fila),
                               lambda contenido=formula: renderizar_latex(contenido))


def _crear_detalle_diferido(titulo: str, renderizar) -> None:
    """Monta contenido una sola vez al abrir una expansión que aún existe."""
    with ui.expansion(titulo, icon="fact_check").classes("w-full panel-tarjeta") as expansion:
        destino = ui.column().classes("w-full min-w-0")
    cargado = False

    def cargar(evento) -> None:
        """Ignora cierres y aperturas repetidas del mismo detalle."""
        nonlocal cargado
        if not evento.value or cargado or destino.is_deleted:
            return
        with destino:
            renderizar()
        cargado = True

    expansion.on_value_change(cargar)


def _mostrar_pasos(traza: list[dict]) -> None:
    """Presenta en orden una traza que no tiene estructura de producto."""
    for paso in traza:
        _mostrar_paso(paso)


def _mostrar_paso(paso: dict) -> None:
    """Normaliza los textos y omite la explicación cuando repite la descripción."""
    descripcion = formatear_descripcion_html(paso.get("descripcion", ""))
    explicacion = formatear_descripcion_html(paso.get("explicacion", ""))
    ui.html(descripcion).classes("font-bold texto-principal")
    if paso.get("detalle_latex"):
        renderizar_latex(paso["detalle_latex"])
    if " ".join(explicacion.split()) != " ".join(descripcion.split()):
        ui.html(explicacion).classes("texto-secundario")
