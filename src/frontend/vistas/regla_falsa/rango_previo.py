"""Sincronización explícita del rango visual con la búsqueda de intervalos."""
from nicegui import ui

from src.frontend.componentes.captura_exploracion_raices import campos_rango
from src.frontend.componentes.sincronizacion_rango_raices import sincronizar_rango as sincronizar_paneles
from src.frontend.controladores.rango_exploracion_raices import rango_grafica
from src.frontend.vistas.biseccion.estado_captura import transaccion


def construir_rango(panel) -> None:
    """Monta el rango compartido con la exploración y una copia voluntaria de a/b."""
    ui.label("El rango visible se comparte con Buscar intervalo; no cambia los extremos a y b.").classes(
        "text-sm texto-secundario")
    panel.minimo, panel.maximo = campos_rango("gráfico", "regla-falsa-campos")
    for campo in (panel.minimo, panel.maximo):
        campo.on_value_change(lambda: sincronizar_rango(panel, panel))
        campo.on("keydown.enter", panel.actualizar)
    ui.button("Ajustar al intervalo", color=None, on_click=lambda: usar_intervalo(panel)).classes("boton-discreto")


def sincronizar_rango(panel, origen) -> None:
    """Copia ambos límites entre búsqueda y previa sin editar el ejercicio ni recalcularlo."""
    vista = panel.vista
    if vista._cargando_captura:
        return
    sincronizar_paneles(vista, (origen.minimo.value, origen.maximo.value), transaccion)


def usar_intervalo(panel) -> None:
    """Ajusta el rango a extremos válidos solo por acción expresa, sin calcular."""
    valores = panel.vista.inferior.value, panel.vista.superior.value
    try:
        rango_grafica({"x_min": valores[0], "x_max": valores[1]})
    except ValueError:
        panel.estado.set_text("Introduce extremos a < b para ajustar el gráfico.")
        return
    with transaccion(panel.vista):
        panel.minimo.set_value(valores[0])
        panel.maximo.set_value(valores[1])
    sincronizar_rango(panel, panel)
