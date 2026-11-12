"""Presentación del estado y las métricas del método abierto."""
from nicegui import ui

from src.frontend.controladores.formato_funcion_real import formatear_expresion
from src.frontend.componentes.reproductor_pasos import renderizar_latex


def mostrar_resumen(datos: dict) -> None:
    """Muestra raíz, residuo, estado y derivada cuando el método es Newton."""
    estado = datos.get("estado")
    clase_estado = _clase_estado(estado)
    etiqueta_estado = "Convergió" if estado == "EXITO" else "Revisar cálculo"
    with ui.card().classes(
            "metodos-abiertos-resumen panel-tarjeta w-full metodos-abiertos-entrada metodos-abiertos-entrada-1"):
        _mostrar_cabecera(etiqueta_estado, clase_estado)
        if datos.get("raiz") is not None:
            _mostrar_raiz_y_metricas(datos, estado)
        ui.label(datos.get("mensaje", "")).classes(
            "metodos-abiertos-mensaje texto-acento" if estado == "EXITO" else
            "metodos-abiertos-mensaje texto-advertencia").props("role=status aria-live=polite")
        _mostrar_derivada(datos)
        _mostrar_advertencias(datos.get("advertencias", ()))


def _clase_estado(estado: str | None) -> str:
    if estado == "EXITO":
        return "distintivo-exito"
    if estado in {"LIMITE_ITERACIONES", "DIVERGENCIA"}:
        return "distintivo-advertencia"
    return "distintivo-error"


def _mostrar_cabecera(etiqueta_estado: str, clase_estado: str) -> None:
    with ui.row().classes("metodos-abiertos-resumen-cabecera w-full items-center justify-between gap-3"):
        ui.label("Resultado del método").classes("text-lg font-semibold texto-principal")
        ui.badge(etiqueta_estado, color=None).classes(clase_estado)


def _mostrar_raiz_y_metricas(datos: dict, estado: str | None) -> None:
    with ui.row().classes("metodos-abiertos-resumen-cuerpo w-full items-center gap-5"):
        with ui.column().classes("metodos-abiertos-raiz-bloque min-w-0"):
            etiqueta = "Raíz aproximada" if estado == "EXITO" else "Aproximación actual"
            ui.label(etiqueta).classes("text-sm texto-secundario")
            ui.label(f"{datos['raiz']:.9g}").classes("metodos-abiertos-raiz texto-principal")
        with ui.row().classes("metodos-abiertos-metricas flex-1"):
            residuo = datos.get("residuo")
            _mostrar_metrica("Residuo", "Sin dato" if residuo is None else f"{residuo:.3g}")
            _mostrar_metrica("Iteraciones", str(datos.get("iteraciones_totales", 0)))


def _mostrar_metrica(etiqueta: str, valor: str) -> None:
    with ui.element("div").classes("metodos-abiertos-metrica"):
        ui.label(etiqueta).classes("text-sm texto-secundario")
        ui.label(valor).classes("metodos-abiertos-metrica-valor texto-principal")


def _mostrar_derivada(datos: dict) -> None:
    if datos.get("metodo") != "newton" or not datos.get("derivada_expresion"):
        return
    with ui.column().classes("metodos-abiertos-derivada w-full gap-1"):
        ui.label("Derivada de la función").classes("text-sm texto-secundario")
        try:
            latex = formatear_expresion(datos["derivada_expresion"], etiqueta="f'(x)")["latex"]
            renderizar_latex(latex, vigilar_region=True)
        except ValueError:
            ui.label(f"f'(x) = {datos['derivada_expresion']}").classes("texto-principal")


def _mostrar_advertencias(avisos) -> None:
    for aviso in avisos:
        ui.label(aviso).classes("text-sm texto-advertencia")
