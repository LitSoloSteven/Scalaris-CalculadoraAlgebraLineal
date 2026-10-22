"""Actualización cancelable y confirmación del estado de las figuras."""
from __future__ import annotations

import asyncio
import json
import logging
from nicegui import run

from src.ai.huellas import calcular_huella
from src.frontend.controladores.geometria import ControladorGeometria
from src.frontend.controladores.sesion_matricial import actualizar_contexto
from ._estados_geometria import aplicar_estado_carga

registro = logging.getLogger(__name__)
ERROR_RENDERIZADO = {
    "codigo": "renderizado_fallido",
    "mensaje": "No pudimos dibujar la figura. Revisa los valores e inténtalo de nuevo.",
}


def limpiar_estado_figura(vista) -> None:
    """Descarta el resultado y la figura para permitir un nuevo intento."""
    vista.ultimo_hash_entrada = None
    vista.ultimo_resultado = None
    vista._primer_dibujo = True
    vista._elemento_plotly = None
    vista._clave_figura = None


def refrescar_contexto(vista, carga: dict | None = None) -> None:
    """Registra la entrada resuelta y notifica a Glosa del cambio de contexto."""
    if carga is not None:
        vista._huella_resultado = calcular_huella({"escena": vista.escena, "carga": carga})
    actualizar_contexto(vista)


async def ejecutar_controlador_geometria(vista, carga: dict) -> dict | None:
    """Delega la escena al controlador en un trabajador de NiceGUI."""
    controladores = {
        'rectas-planos': ControladorGeometria.procesar_rectas_planos,
        'vectores': ControladorGeometria.procesar_vectores,
        'combinacion': ControladorGeometria.procesar_combinacion,
    }
    controlador = controladores.get(vista.escena)
    if controlador is None:
        return None
    return await run.io_bound(controlador, json.dumps(carga))


async def renderizar_figura_actualizada(vista, resultado: dict, clave: tuple) -> bool:
    """Reutiliza la figura compatible o construye su contenedor inicial."""
    if vista._primer_dibujo or vista._elemento_plotly is None or vista._clave_figura != clave:
        return await vista._construir_figura(resultado, vista.escena)
    figura = await vista._obtener_solo_figura(resultado, vista.escena)
    if figura is None:
        vista._renderizar_error(ERROR_RENDERIZADO)
        return False
    vista._elemento_plotly.update_figure(figura)
    vista._registrar_cuadros(resultado)
    return True


def finalizar_actualizacion_figura(vista, resultado: dict, carga: dict, hash_entrada: int, clave: tuple) -> None:
    """Confirma el resultado solo después de dibujar la figura satisfactoriamente."""
    vista._ejecutar_javascript('window.scalaris?.geometria?.marcarInvalido(null);')
    vista._clave_figura = clave
    vista.ultimo_resultado = resultado
    vista.ultimo_hash_entrada = hash_entrada
    vista._construir_deslizador(resultado, vista.escena)
    vista._renderizar_resumen(resultado, vista.escena)
    if vista.contenedor_resumen and vista.panel_ia:
        with vista.contenedor_resumen:
            vista.panel_ia.renderizar_sugerencias_en_linea()
    vista._primer_dibujo = False
    refrescar_contexto(vista, carga)


async def _procesar_carga(vista, carga: dict, hash_entrada: int) -> None:
    aplicar_estado_carga(vista)
    resultado = await ejecutar_controlador_geometria(vista, carga)
    # NiceGUI puede absorber CancelledError y devolver None desde io_bound.
    if asyncio.current_task().cancelling():
        raise asyncio.CancelledError
    if not resultado:
        limpiar_estado_figura(vista)
        vista._renderizar_error(ERROR_RENDERIZADO)
        refrescar_contexto(vista, carga)
        return
    if resultado.get("estado") == "ERROR":
        limpiar_estado_figura(vista)
        vista._renderizar_error(resultado)
        refrescar_contexto(vista, carga)
        return
    clave = (vista.escena, resultado.get("numero_variables"))
    if not await renderizar_figura_actualizada(vista, resultado, clave):
        limpiar_estado_figura(vista)
        refrescar_contexto(vista)
        return
    finalizar_actualizacion_figura(vista, resultado, carga, hash_entrada, clave)


async def actualizar_figura(vista) -> None:
    """Actualiza una entrada distinta y descarta resultados cancelados o fallidos."""
    try:
        carga = vista._construir_carga()
        if carga is None:
            limpiar_estado_figura(vista)
            vista._mostrar_estado_vacio()
            return
        hash_entrada = hash(json.dumps(carga, sort_keys=True))
        if hash_entrada != vista.ultimo_hash_entrada:
            await _procesar_carga(vista, carga, hash_entrada)
    except asyncio.CancelledError:
        vista.ultimo_hash_entrada = None
        raise
    except Exception:
        limpiar_estado_figura(vista)
        registro.exception("No se pudo dibujar la figura geométrica")
        vista._renderizar_error(ERROR_RENDERIZADO)
        refrescar_contexto(vista)
