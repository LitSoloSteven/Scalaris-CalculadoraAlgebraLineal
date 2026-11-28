"""Presentación del estado y las métricas del método abierto."""
from typing import Any

from nicegui import ui

from src.frontend.componentes.reproductor_pasos import renderizar_latex
from src.frontend.controladores.raices.compartido.formato.formato_funcion_real import formatear_expresion

_ESTADOS_VISUALES = {
    "EXITO": ("Convergió", "distintivo-exito", "check_circle"),
    "LIMITE_ITERACIONES": ("Límite alcanzado", "distintivo-advertencia", "schedule"),
    "DIVERGENCIA": ("Divergencia", "distintivo-advertencia", "trending_up"),
    "DERIVADA_NULA": ("Derivada nula", "distintivo-error", "warning"),
    "DENOMINADOR_NULO": ("Denominador nulo", "distintivo-error", "warning"),
}
_ETIQUETAS_METODO = {"newton": "Newton-Raphson", "secante": "Secante"}


def mostrar_resumen(datos: dict, panel_ia: Any = None) -> None:
    """Muestra raíz, residuo, estado, derivada y sugerencias en paneles claros."""
    estado = datos.get("estado")
    etiqueta_estado, clase_estado, icono_estado = _estado_visual(estado)
    metodo = _ETIQUETAS_METODO.get(datos.get("metodo"), "Método abierto")
    with ui.card().classes(
            "metodos-abiertos-resumen panel-tarjeta w-full metodos-abiertos-entrada metodos-abiertos-entrada-1"):
        _mostrar_cabecera(metodo, etiqueta_estado, clase_estado, icono_estado)
        if datos.get("raiz") is not None:
            _mostrar_raiz_y_metricas(datos, estado)
        rol = "status" if estado == "EXITO" else "alert"
        clase_mensaje = (
            "metodos-abiertos-mensaje texto-acento" if estado == "EXITO"
            else "metodos-abiertos-mensaje texto-advertencia"
        )
        ui.label(datos.get("mensaje", "")).classes(clase_mensaje).props(f"role={rol} aria-live=polite")
        _mostrar_derivada(datos)
        _mostrar_advertencias(datos.get("advertencias", ()))
        if panel_ia is not None:
            panel_ia.renderizar_sugerencias_en_linea()


def _estado_visual(estado: str | None) -> tuple[str, str, str]:
    return _ESTADOS_VISUALES.get(estado or "", ("Revisar cálculo", "distintivo-error", "error_outline"))


def _mostrar_cabecera(metodo: str, etiqueta_estado: str, clase_estado: str, icono_estado: str) -> None:
    with ui.row().classes("metodos-abiertos-resumen-cabecera w-full items-center justify-between gap-3 flex-wrap"):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            ui.label("Resultado").classes("text-lg font-semibold texto-principal")
            ui.label(metodo).classes("metodos-abiertos-metodo-etiqueta text-xs")
        with ui.element("div").classes(f"metodos-abiertos-distintivo {clase_estado}"):
            ui.icon(icono_estado, size="xs")
            ui.label(etiqueta_estado).classes("text-xs font-semibold")


def _mostrar_raiz_y_metricas(datos: dict, estado: str | None) -> None:
    with ui.row().classes("metodos-abiertos-resumen-cuerpo w-full items-stretch gap-5"):
        with ui.column().classes("metodos-abiertos-raiz-bloque min-w-0"):
            etiqueta = "Raíz aproximada" if estado == "EXITO" else "Aproximación actual"
            ui.label(etiqueta).classes("text-sm texto-secundario")
            ui.label(f"{datos['raiz']:.9g}").classes("metodos-abiertos-raiz texto-principal")
        with ui.row().classes("metodos-abiertos-metricas flex-1"):
            residuo = datos.get("residuo")
            _mostrar_metrica("Residuo |f(x)|", "Sin dato" if residuo is None else f"{residuo:.3g}")
            _mostrar_metrica("Iteraciones", str(datos.get("iteraciones_totales", 0)))
            iniciales = _puntos_iniciales(datos)
            if iniciales:
                _mostrar_metrica("Puntos iniciales", iniciales, destacada=True)


def _puntos_iniciales(datos: dict) -> str:
    entrada = datos.get("entrada") or {}
    x0 = entrada.get("x0")
    if x0 in (None, ""):
        return ""
    if datos.get("metodo") == "secante" and entrada.get("x1") not in (None, ""):
        return f"x₀ = {x0}, x₁ = {entrada['x1']}"
    return f"x₀ = {x0}"


def _mostrar_metrica(etiqueta: str, valor: str, *, destacada: bool = False) -> None:
    clase = "metodos-abiertos-metrica metodos-abiertos-metrica-destacada" if destacada else "metodos-abiertos-metrica"
    with ui.element("div").classes(clase):
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
        with ui.row().classes("metodos-abiertos-aviso items-start gap-2 w-full"):
            ui.icon("warning_amber", size="xs").classes("texto-advertencia")
            ui.label(aviso).classes("text-sm texto-advertencia flex-1 min-w-0")
