"""Restauración de ejercicios de aplicación sin reutilizar resultados anteriores."""
import asyncio
import copy

import pytest

from src.frontend import textos_transformaciones as textos
from src.frontend.controladores.operaciones_matrices.contexto_modelos import capturar_modelo
from src.frontend.vistas.operaciones_matrices.carga_modelos import cargar_captura_modelo
from src.frontend.vistas.operaciones_matrices.transferencia_modelos import _cargar_matriz
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize("tipo,filas,columnas", [("vector", 2, 3), ("punto", 3, 2)])
def test_restaurar_recupera_modo_dimensiones_y_coordenadas(monkeypatch, tipo, filas, columnas):
    """Una captura completa sustituye también el tipo, los nombres y el vector ocultos."""
    async def comprobar(vista, cliente):
        """Carga desde otro modo y comprueba una copia independiente sin cálculo."""
        captura = {"matriz_transformacion": [["1/3"] * columnas for _ in range(filas)],
                   "nombres_variables": [f"variable {indice}" for indice in range(columnas)],
                   "vector_original": ["-2/7"] * columnas, "tipo_objeto": tipo,
                   "modo_transformacion": textos.MODO_APLICACION}
        original = copy.deepcopy(captura)
        cargar_captura_modelo(vista, captura)
        assert (vista.filas, vista.columnas) == (filas, columnas)
        assert vista.selector_modo.value == textos.MODO_APLICACION
        assert vista.selector_tipo_objeto.value == tipo
        assert capturar_modelo(vista) == original
        assert vista.ultimo_resultado is None
        assert vista.contenedor_historial.parent_slot.parent.visible
        vista.entradas_vector_original[0].set_value("99")
        assert captura == original
        cargar_captura_modelo(vista, original)
        assert capturar_modelo(vista) == original
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))


def test_transferir_solo_matriz_restablece_analisis_y_limpia_vector(monkeypatch):
    """Recibir A no atribuye un vector antiguo a una transferencia sin coordenadas."""
    async def comprobar(vista, cliente):
        """Alterna carga completa y recepción matricial con dimensiones diferentes."""
        cargar_captura_modelo(vista, {"matriz_transformacion": [["1", "0"]],
                                    "vector_original": ["5", "7"], "tipo_objeto": "punto"})
        _cargar_matriz(vista, [["1"], ["2"], ["3"]])
        assert vista.modo_transformacion == textos.MODO_ANALISIS
        assert vista.tipo_objeto == "vector"
        assert [entrada.value for entrada in vista.entradas_vector_original] == [""]
        assert capturar_modelo(vista)["matriz_transformacion"] == [["1"], ["2"], ["3"]]
        assert vista.ultimo_resultado is None
    asyncio.run(construir_pagina(monkeypatch, "transformaciones", comprobar))
