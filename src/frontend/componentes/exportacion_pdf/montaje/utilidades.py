"""Adaptación de resultados numéricos y escenas al contrato compartido de PDF."""
from src.frontend.controladores.captura_contexto import capturar_bases, capturar_romanos
from src.frontend.controladores.exportacion_pdf.vigencia import EnlacePDF
from .boton import renderizar_boton_pdf
from .integracion import identificador_raiz


def _entrada(vista, herramienta: str) -> dict:
    if herramienta == 'bases':
        return capturar_bases(vista, vista.entrada_valor.value or '')
    if herramienta == 'romanos':
        return capturar_romanos(vista.entrada_a.value, vista.entrada_b.value,
                                vista.pestanas_operacion.value or 'suma')
    return {'escena': vista.escena, 'carga': vista._construir_carga()}


def _resultado(vista, herramienta: str):
    if herramienta == 'bases':
        return vista.resultados_completos if vista.tiene_resultado else None
    return vista.ultimo_resultado


def montar_utilidad_pdf(vista, herramienta: str) -> None:
    """Monta un único exportador con identidad del resultado y revisión de entradas."""
    contenedor = getattr(vista, 'contenedor_exportacion_pdf', None)
    if contenedor is None or contenedor.is_deleted:
        return
    original = _resultado(vista, herramienta)
    resultado = {'estado': 'EXITO'} if herramienta == 'romanos' else original

    def leer_estado() -> tuple:
        """Comprueba la identidad nativa sin reemplazar el resultado de la herramienta."""
        actual = resultado if _resultado(vista, herramienta) is original else None
        return (contenedor, actual, getattr(vista, '_revision_captura', 0),
                getattr(vista, '_identificador_calculo', 0))

    enlace = EnlacePDF(vista, lambda: _entrada(vista, herramienta),
                       identificador_raiz(contenedor), leer_estado)
    acciones = vista.contenedor_acciones_pdf
    acciones.clear()
    with acciones:
        control = renderizar_boton_pdf(herramienta, resultado, enlace)
    vista.actualizar_exportacion_pdf = control.actualizar
