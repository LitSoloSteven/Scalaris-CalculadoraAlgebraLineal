"""Presentación de estados, resúmenes y tablas separados por identificador."""
from nicegui import ui

from src.frontend.componentes.copia_resultado import renderizar_copia_resultado
from src.frontend.controladores.biseccion.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.biseccion.presentacion_criterio import datos_copia_biseccion, texto_resumen, titulo_estado
from src.frontend.controladores.biseccion.salidas_biseccion import texto_copia_biseccion
from .modo_examen import crear_control_examen_lote
from .continuidad_intervalo import mostrar_informe
from .procedimiento import mostrar_traza


def mostrar_resultados_multiples(lote: dict, al_consultar, al_volver, al_montar) -> None:
    """Compone el lote actual sin sobrescribir el resultado individual ni su contexto de Glosa."""
    for aviso in lote["advertencias"]:
        ui.label(aviso).classes("text-sm texto-secundario")
    ui.label(f"Unidad angular: {lote['unidad_angular']} · Filas generadas: {lote['filas_generadas']}").classes(
        "biseccion-numero texto-secundario")
    ui.label(f"Reserva de evaluaciones: {lote['evaluaciones_reservadas']} de {lote['presupuesto_evaluaciones']}. "
             "Es una cota conservadora, no el número de evaluaciones efectivas.").classes(
                 "biseccion-numero text-sm texto-secundario")
    if lote["presupuesto_agotado"]:
        ui.label("El presupuesto se agotó. Los candidatos pendientes están identificados; puedes resolverlos uno por uno.").classes(
            "texto-advertencia").props("role=status")
    _montar_detalle(lote["resultados"], al_consultar, al_volver, al_montar)


def _montar_detalle(registros: tuple, al_consultar, al_volver, al_montar) -> None:
    acciones = ui.row().classes("w-full gap-2")
    detalle = ui.column().classes("w-full gap-2")
    examen = {}

    def consultar(registro: dict) -> None:
        """Abre solo el registro elegido y sincroniza la gráfica."""
        al_montar(None)
        detalle.clear()
        al_consultar(registro["respuesta"])
        with detalle:
            paso = lambda actual: al_consultar(registro["respuesta"], actual)
            al_montar(_mostrar_registro(registro, examen, paso))

    def volver() -> None:
        """Retira el detalle y muestra el cálculo principal en la gráfica."""
        al_montar(None)
        detalle.clear()
        al_volver()

    with acciones:
        for registro in registros:
            respuesta = registro["respuesta"]
            titulo = titulo_estado(respuesta) if respuesta is not None else _titulo_pendiente(registro)
            icono = "check_circle" if registro["estado"] == "EXITO" else "info"
            ui.button(f"{registro['identificador']} · {titulo}", icon=icono, color=None,
                      on_click=lambda _, dato=registro: consultar(dato)).classes("boton-discreto").props(
                          f'aria-label="{registro["identificador"]} · {titulo}"')
        ui.button("Volver al cálculo principal", color=None, on_click=volver).classes("boton-discreto")


def _titulo_pendiente(registro: dict) -> str:
    return {"NO_APTO": "Candidato no apto", "PRESUPUESTO_AGOTADO": "Pendiente por presupuesto"}.get(
        registro["estado"], "Error al resolver")


def _mostrar_registro(registro: dict, preferencias: dict, al_mostrar_paso):
    respuesta = registro["respuesta"]
    if registro.get("informe_continuidad") is not None:
        mostrar_informe(registro["informe_continuidad"])
    if respuesta is None:
        ui.label(registro["mensaje"]).classes("texto-advertencia")
        return
    resumen = texto_resumen(respuesta, DECIMALES_PRESENTACION_DEFECTO)
    for linea in resumen.splitlines():
        ui.label(linea).classes("biseccion-numero text-sm texto-principal")
    examen = None
    reproductor = None
    if respuesta.get("iteraciones"):
        clave = registro["identificador"]
        examen = crear_control_examen_lote()
        examen.set_value(preferencias.get(clave, False))
        examen.on_value_change(lambda evento: preferencias.update({clave: evento.value}))
        reproductor = mostrar_traza(respuesta, examen, al_mostrar_paso, "biseccion-lote")
    _mostrar_copia(registro, resumen, examen)
    return reproductor


def _mostrar_copia(registro: dict, resumen: str, examen: ui.checkbox | None) -> None:
    respuesta = registro["respuesta"]

    def _generar() -> dict:
        texto = texto_copia_biseccion(respuesta, DECIMALES_PRESENTACION_DEFECTO, True) if examen and examen.value else resumen
        return datos_copia_biseccion(respuesta["estado"], f"{registro['identificador']}\n{texto}", lote=True)

    @ui.refreshable
    def copiar() -> None:
        """Actualiza únicamente la acción de copia del candidato."""
        renderizar_copia_resultado(_generar)

    copiar()
    if examen is not None:
        examen.on_value_change(lambda: copiar.refresh())
