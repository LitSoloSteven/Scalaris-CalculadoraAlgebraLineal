"""Montaje del detalle compartido por un cálculo individual y un candidato de lote."""
from .procedimiento import PanelProcedimiento
from .resultado import mostrar_resultado


def presentar_detalle(vista, datos: dict) -> None:
    """Monta resumen, tabla y secante del mismo resultado sin editar la captura matemática."""
    vista.ultimo_resultado = datos["resultado"]
    vista.ultimo_ampliado = datos.get("ampliado")
    vista.continuidad.region.set_visibility(False)
    mostrar_resultado(vista, vista.ultimo_resultado, vista.ultimo_ampliado)
    vista.detalle_procedimiento = PanelProcedimiento(vista, datos)
    vista.detalle_procedimiento.reproductor.velocidad = vista.velocidad_procedimiento or "Normal"
    vista.detalle_procedimiento.construir()
    vista.reproductor_pasos = vista.detalle_procedimiento.reproductor


def captura_contexto(vista) -> dict:
    """Acota la captura pedagógica al resultado abierto del lote, sin incluir otros candidatos."""
    panel = getattr(vista, "resolucion_multiple", None)
    if panel is None or panel.activo is None or vista.ultimo_resultado is None:
        return vista.capturar()
    return {**vista.ultimo_resultado["entrada"], "criterio": vista.ultimo_ampliado["criterio"],
            "identificador_candidato": panel.activo}
