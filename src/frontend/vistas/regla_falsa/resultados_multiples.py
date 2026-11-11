"""Lista de estados del lote con apertura explícita por identificador estable."""
from nicegui import ui

from src.frontend.controladores.regla_falsa.presentacion_ampliada import titulo_configurado


def mostrar_resultados_multiples(lote: dict, al_abrir) -> None:
    """Presenta reservas y estados reales; las acciones transportan el identificador del dominio."""
    for aviso in lote["advertencias"]:
        ui.label(aviso).classes("text-sm texto-secundario")
    ui.label(f"Reserva de evaluaciones: {lote['evaluaciones_reservadas']} de {lote['presupuesto_evaluaciones']}. "
             "Es una cota conservadora, no un consumo medido. El muestreo de la gráfica se realiza aparte.").classes(
                 "regla-falsa-numero text-sm texto-secundario")
    ui.label(f"Filas generadas: {lote['filas_generadas']}").classes("regla-falsa-numero texto-secundario")
    with ui.column().classes("w-full min-w-0 gap-2"):
        for registro in lote["resultados"]:
            _mostrar_registro(registro, al_abrir)


def _mostrar_registro(registro: dict, al_abrir) -> None:
    datos = registro["datos"]
    titulo = titulo_configurado(datos["resultado"], datos["ampliado"]) if datos else {
        "NO_APTO": "Candidato no apto", "PRESUPUESTO_AGOTADO": "Pendiente por presupuesto",
    }.get(registro["estado"], "Error al resolver")
    ui.label(f"{registro['identificador']} · {titulo}").classes("regla-falsa-numero texto-principal")
    ui.label(registro["mensaje"]).classes("text-sm texto-secundario")
    if datos is not None:
        ui.button(f"Abrir {registro['identificador']}", color=None,
                  on_click=lambda: al_abrir(registro["identificador"])).classes("boton-discreto").props("ripple=false")
