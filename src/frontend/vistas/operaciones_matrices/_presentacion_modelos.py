"""Adaptadores de comprobación económica y reducción de transformaciones."""
from dataclasses import replace
from nicegui import ui

from src.frontend import textos
from src.frontend.componentes.presentacion_analisis import adaptar_analisis, montar_pasos_analisis
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor
from src.frontend.componentes.reproductor_pasos.textos import limpiar_latex_plano
from src.frontend.controladores.agrupacion_trazas import agrupar_traza
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def adaptar_pasos_modelo(resultado: dict, herramienta: str) -> tuple:
    """Convierte la reducción y comprobación originales en una secuencia con fases."""
    reduccion = [_adaptar_reduccion(paso, indice) for indice, paso in enumerate(resultado.get("pasos_reduccion", []))]
    comprobacion = [dict(paso) for paso in resultado.get("traza_comprobacion", [])]
    if herramienta == "leontief":
        for indice, paso in enumerate(comprobacion):
            paso["fase"] = 0 if indice == 0 else (2 if indice == len(comprobacion) - 1 else 1)
    else:
        for paso in comprobacion:
            paso["fase"] = 2
    fuente = reduccion + comprobacion
    grupos, posiciones = agrupar_traza(fuente, _identificar_fase)
    pasos, _ = adaptar_analisis({"traza": fuente})
    adaptados = tuple(replace(paso, indice_grupo=posiciones[indice], meta_explicar={
        **paso.meta_explicar, "operacion": limpiar_latex_plano(paso.descripcion)}) for indice, paso in enumerate(pasos))
    fases = tuple(GrupoReproductor(grupo["titulo"], textos.RESULTADO_CUENTA_PASOS.format(
        cantidad=len(grupo["indices_pasos"])), grupo["tipo"], tuple(grupo["indices_pasos"])) for grupo in grupos)
    return adaptados, fases


def _adaptar_reduccion(paso: dict, indice: int) -> dict:
    descripcion = paso["descripcion"]
    return {"descripcion": descripcion, "explicacion": descripcion, "detalle_latex": paso["matriz"],
            "tipo": clasificar_paso(descripcion)["tipo"], "fase": 0 if indice == 0 else 1}


def _identificar_fase(paso: dict, indice: int) -> tuple:
    fase = paso.get("fase", 1)
    return fase, textos.MODELOS_FASES[fase], "operacion"


def montar_pasos_modelo(vista):
    """Monta ayuda, leyenda, índice, acción de Glosa e interpretación del modelo."""
    resultado = vista.ultimo_resultado
    if not resultado or resultado.get("estado") == "ERROR":
        return None
    herramienta = vista.herramienta_modelo
    titulo = textos.MODELOS_COMPROBACION if herramienta == "leontief" else textos.MODELOS_REDUCCION
    reproductor = montar_pasos_analisis(adaptar_pasos_modelo(resultado, herramienta), vista.panel_ia, herramienta,
                                      {"titulo": titulo, "lineas_ayuda": textos.MODELOS_AYUDA,
                                       "tipos_leyenda": textos.MODELOS_LEYENDA})
    with ui.expansion(textos.RESULTADO_INTERPRETACION, icon="help_outline").classes("w-full panel-tarjeta"):
        ui.label(textos.LEONTIEF_INTERPRETACION if herramienta == "leontief" else
                 textos.TRANSFORMACIONES_INTERPRETACION).classes("texto-secundario")
    return reproductor
