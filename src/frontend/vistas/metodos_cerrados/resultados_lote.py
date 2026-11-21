"""Estados de lote y adaptación del registro seleccionado a la salida común."""
from nicegui import ui

from src.frontend.componentes.raices.resultados.informe_continuidad_raices import mostrar_informe_continuidad
from src.frontend.controladores.raices.biseccion.presentacion.presentacion_criterio import titulo_estado
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION
from src.frontend.controladores.raices.regla_falsa.presentacion.presentacion_ampliada import titulo_configurado

_ESTADOS = {"NO_APTO": "Candidato no apto", "PRESUPUESTO_AGOTADO": "Pendiente por presupuesto"}


def datos_detalle(registro: dict, metodo: str) -> dict | None:
    """Adapta un registro resuelto sin calcular otra vez ni copiar sus iteraciones."""
    if metodo == BISECCION:
        respuesta = registro["respuesta"]
        datos = {"resultado": respuesta, "aviso_grafica": "", "muestra": None} if respuesta is not None else None
    else:
        datos = registro["datos"]
    if datos is None:
        return None
    return {"metodo": metodo, **datos, "informe_continuidad": registro.get("informe_continuidad")}


def mostrar_lote(lote: dict, metodo: str, intervalos: dict, al_abrir, al_volver) -> ui.button:
    """Muestra metadatos y acciones explícitas para abrir el detalle o restaurar el cálculo."""
    for aviso in lote["advertencias"]:
        ui.label(aviso).classes("text-sm texto-secundario")
    ui.label(f"Reserva de evaluaciones: {lote['evaluaciones_reservadas']} de {lote['presupuesto_evaluaciones']}. "
             "Es una cota conservadora, no un consumo medido.").classes("text-sm texto-secundario")
    ui.label(f"Filas generadas: {lote['filas_generadas']}").classes("texto-secundario")
    if metodo == BISECCION:
        ui.label(f"Unidad angular: {lote['unidad_angular']}").classes("texto-secundario")
        if lote["presupuesto_agotado"]:
            ui.label("El presupuesto se agotó. Puedes resolver uno por uno los candidatos pendientes.").classes(
                "texto-advertencia")
    for registro in lote["resultados"]:
        _mostrar_registro(lote, registro, metodo, intervalos[registro["identificador"]], al_abrir)
    boton = ui.button("Volver al cálculo principal", color=None, on_click=lambda: al_volver(lote)).classes(
        "boton-discreto").props("ripple=false")
    boton.set_visibility(False)
    return boton


def _mostrar_registro(lote: dict, registro: dict, metodo: str, intervalo: str, al_abrir) -> None:
    datos = datos_detalle(registro, metodo)
    identificador = registro["identificador"]
    with ui.column().classes("w-full min-w-0 gap-1"):
        ui.label(f"{identificador} · {_titulo(datos, registro)}").classes("texto-principal")
        ui.label(intervalo).classes("break-all text-sm texto-secundario")
        ui.label(registro["mensaje"]).classes("text-sm texto-secundario")
        if datos is not None:
            boton = ui.button(f"Abrir {identificador}", color=None).classes("boton-discreto").props("ripple=false")
            boton.on_click(lambda: al_abrir(lote, metodo, registro, boton))
        elif registro.get("informe_continuidad") is not None:
            with ui.expansion(f"Continuidad de {identificador}").classes("w-full"):
                mostrar_informe_continuidad(registro["informe_continuidad"], "break-all texto-principal")


def _titulo(datos: dict | None, registro: dict) -> str:
    if datos is None:
        return _ESTADOS.get(registro["estado"], "Error al resolver")
    respuesta = datos["resultado"]
    if datos["metodo"] == BISECCION:
        return titulo_estado(respuesta)
    return titulo_configurado(respuesta, datos.get("ampliado"))
