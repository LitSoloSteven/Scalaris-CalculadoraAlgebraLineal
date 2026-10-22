"""Conservación del interior y recuperación de cuadrículas rectangulares."""
import asyncio
import pytest
from tests.comun_construccion_vistas import construir_pagina


def _preparar(vista, herramienta):
    if herramienta == 'sistemas':
        panel = vista.cuadricula
        panel.cargar_datos([['1/3', '2'], ['3', '4']], ['7/11', '5'])
        return panel, lambda: panel.entradas_coeficientes, lambda dimensiones: panel._aplicar_tamano(*dimensiones)
    panel = vista.panel_captura_matrices
    panel.cargar_datos({'A': [['1/3', '2'], ['3', '4']]})
    return panel, lambda: panel.matrices['A']['entradas'], lambda dimensiones: panel._aplicar_tamano('A', dimensiones)


@pytest.mark.parametrize('herramienta', ['sistemas', 'matrices'])
def test_cada_borde_preserva_interior_valores_y_coordenadas(monkeypatch, herramienta):
    """Filas y columnas cambian en ambas direcciones sin recrear celdas interiores."""
    async def _comprobar(vista, cliente):
        panel, entradas, aplicar = _preparar(vista, herramienta)
        interior = entradas()[0][0]
        for dimensiones in ((3, 2), (3, 3), (2, 3), (2, 2)):
            aplicar(dimensiones)
            assert entradas()[0][0] is interior and interior.value == '1/3'
            assert len(entradas()) == dimensiones[0]
            assert all(len(fila) == dimensiones[1] for fila in entradas())
            if herramienta == 'sistemas':
                independiente = panel.entradas_independientes[0]
                assert independiente.value == '7/11'
                assert independiente._props['data-ecuaciones-columna'] == str(dimensiones[1])
                hijos = panel.filas_interfaz[0].default_slot.children
                assert hijos[-1] is independiente
                assert hijos[dimensiones[1] - 1] is entradas()[0][-1]
        interior.set_value('-13/17')
        cache = panel._cache_coeficientes if herramienta == 'sistemas' else panel.matrices['A']['cache']
        assert cache[(0, 0)] == '-13/17'
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))


@pytest.mark.parametrize('herramienta', ['sistemas', 'matrices'])
def test_borde_retirado_no_reaparece_al_ampliar(monkeypatch, herramienta):
    """La poda mantiene vacías las coordenadas retiradas y conserva el interior exacto."""
    async def _comprobar(vista, cliente):
        _, entradas, aplicar = _preparar(vista, herramienta)
        aplicar((1, 2))
        aplicar((1, 1))
        aplicar((2, 1))
        aplicar((2, 2))
        assert [[celda.value for celda in fila] for fila in entradas()] == [['1/3', ''], ['', '']]
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))


@pytest.mark.parametrize('herramienta', ['sistemas', 'matrices'])
def test_registro_parcial_y_salto_no_unitario_reconstruyen_sin_perder_datos(monkeypatch, herramienta):
    """Una estructura incompleta activa el respaldo completo en lugar de omitir celdas."""
    async def _comprobar(vista, cliente):
        panel, entradas, aplicar = _preparar(vista, herramienta)
        filas = panel.filas_interfaz if herramienta == 'sistemas' else panel.matrices['A']['filas_interfaz']
        filas.pop()
        aplicar((3, 2))
        assert entradas()[0][0].value == '1/3'
        assert len(entradas()) == 3
        aplicar((6, 5))
        assert len(entradas()) == 6 and all(len(fila) == 5 for fila in entradas())
        assert entradas()[0][0].value == '1/3'
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))


def test_redimension_homogenea_conserva_b_general_y_solo_lectura(monkeypatch):
    """Añadir coeficientes y filas en Ax=0 conserva el b general que se restaura después."""
    async def _comprobar(vista, cliente):
        panel, entradas, aplicar = _preparar(vista, 'sistemas')
        panel.establecer_modo_homogeneo(True)
        interior = entradas()[0][0]
        aplicar((2, 3))
        aplicar((3, 3))
        assert entradas()[0][0] is interior
        assert all(celda._props['readonly'] for celda in panel.entradas_independientes)
        assert panel.obtener_datos_matriz()[1] == ['0', '0', '0']
        panel.establecer_modo_homogeneo(False)
        assert panel.obtener_datos_matriz()[1] == ['7/11', '5', '0']
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', _comprobar))


@pytest.mark.parametrize('herramienta', ['sistemas', 'matrices'])
def test_fallo_creando_borde_permite_reconstruir_en_el_siguiente_cambio(monkeypatch, herramienta):
    """Una excepción no borra el caché y la dimensión siguiente repara el registro parcial."""
    from src.frontend.componentes import redimension_ecuaciones, redimension_captura_matrices
    async def _comprobar(vista, cliente):
        _, entradas, aplicar = _preparar(vista, herramienta)
        modulo, nombre = ((redimension_ecuaciones, 'crear_coeficiente') if herramienta == 'sistemas'
                          else (redimension_captura_matrices, 'crear_celda_matriz'))
        original = getattr(modulo, nombre)
        def _fallar(*argumentos):
            raise RuntimeError('fallo simulado')
        monkeypatch.setattr(modulo, nombre, _fallar)
        with pytest.raises(RuntimeError, match='fallo simulado'):
            aplicar((3, 2))
        monkeypatch.setattr(modulo, nombre, original)
        aplicar((2, 2))
        assert len(entradas()) == 2 and entradas()[0][0].value == '1/3'
    asyncio.run(construir_pagina(monkeypatch, herramienta, _comprobar))
