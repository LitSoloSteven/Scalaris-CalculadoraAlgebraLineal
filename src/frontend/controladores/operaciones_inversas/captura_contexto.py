"""Datos de entrada de inversa reutilizables entre contexto y señales."""
from typing import Any
from src.ai.contexto import describir_matriz, sanear_cadena_usuario
from src.ai.huellas import calcular_huella
from src.frontend.controladores.memo_captura import reutilizar_captura
from src.frontend.sugerencias import primera_celda_invalida


def _clave(vista: Any) -> tuple:
    panel = vista.panel_matriz_cuadrada
    return id(panel), panel.dimension


def describir_captura(vista: Any) -> tuple[dict, str]:
    """Devuelve descriptor y huella de los datos de la revisión; no expone controles."""
    def _construir():
        datos = vista.panel_matriz_cuadrada.obtener_datos_matriz()
        descripcion = describir_matriz([[sanear_cadena_usuario(valor or '', 32) for valor in fila] for fila in datos])
        return descripcion, calcular_huella({'datos': datos})
    return reutilizar_captura(vista, 'descripcion', _clave(vista), _construir)


def localizar_invalida(vista: Any) -> Any:
    """Devuelve la primera celda inválida mediante el validador de dominio existente."""
    def _construir():
        datos = vista.panel_matriz_cuadrada.obtener_datos_matriz()
        elementos = [(f'A[{fila+1},{columna+1}]', valor, (fila, columna))
                     for fila, valores in enumerate(datos) for columna, valor in enumerate(valores)]
        return primera_celda_invalida(elementos)
    return reutilizar_captura(vista, 'invalida', _clave(vista), _construir)
