"""Redimensionado real de capturas con conservación de valores y límites de botones."""
import asyncio
import pytest
from tests.comun_construccion_vistas import construir_pagina


@pytest.mark.parametrize('herramienta', ['leontief', 'transformaciones'])
def test_modelos_conservan_coeficientes_y_campos_auxiliares(monkeypatch, herramienta):
    """Los modelos conservan la intersección sin resucitar valores eliminados."""
    async def comprobar(vista, cliente):
        """Amplía y reduce usando los manejadores reales de cada modelo."""
        vista.entradas_coeficientes[0][0].set_value('1/1001')
        es_leontief = herramienta == 'leontief'
        nombres = vista.entradas_sectores if es_leontief else vista.entradas_variables
        nombres[0].set_value('Producción')
        if es_leontief:
            vista.entradas_demanda[0].set_value('2/3')
        ajustar = vista._ajustar_tamano if es_leontief else vista._ajustar_columnas
        await ajustar(1)
        assert vista.entradas_coeficientes[0][0].value == '1/1001'
        nombres = vista.entradas_sectores if es_leontief else vista.entradas_variables
        assert nombres[0].value == 'Producción'
        assert nombres[-1].value == ''
        nombres[-1].set_value('Eliminar')
        await ajustar(-1)
        await ajustar(1)
        nombres = vista.entradas_sectores if es_leontief else vista.entradas_variables
        assert nombres[-1].value == ''
        if es_leontief:
            assert vista.entradas_demanda[0].value == '2/3'
        else:
            await vista._ajustar_filas(1)
            assert vista.entradas_coeficientes[0][0].value == '1/1001'
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('herramienta', ['inversa', 'determinantes'])
def test_matriz_cuadrada_preserva_interseccion_y_union_de_selectores(monkeypatch, herramienta):
    """El cambio n×n anima una sola unión de fila y columna y respeta el mínimo."""
    async def comprobar(vista, cliente):
        """Reconstruye el panel sin alterar el valor exacto de una celda existente."""
        panel = vista.panel_matriz_cuadrada if herramienta == 'inversa' else vista.panel_matriz
        panel.celdas[0][0].set_value('7/13')
        await panel._redimensionar_asincrono(1)
        assert panel.dimension == 4
        assert panel.celdas[0][0].value == '7/13'
        await panel._redimensionar_asincrono(-3)
        assert panel.dimension == 1 and not panel.boton_reducir.enabled
        assert panel.boton_aumentar.enabled
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_ecuaciones_textuales_conservan_valores_y_actualizan_limites(monkeypatch):
    """La entrada textual participa en el mismo protocolo sin registrar navegación matricial."""
    async def comprobar(vista, cliente):
        """Amplía, retira y regresa al mínimo con botones correctamente habilitados."""
        vista.entradas_ecuaciones[0].set_value('x+y=3')
        await vista._cambiar_ecuaciones_animadas(1)
        assert vista.entradas_ecuaciones[0].value == 'x+y=3'
        assert vista.entradas_ecuaciones[-1]._props['data-ecuaciones-indice'] == str(vista.num_ecuaciones - 1)
        while vista.num_ecuaciones > 1:
            await vista._cambiar_ecuaciones_animadas(-1)
        assert not vista.boton_quitar_ecuacion.enabled
        assert vista.boton_agregar_ecuacion.enabled
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


@pytest.mark.parametrize('herramienta', ['leontief', 'transformaciones'])
def test_cargar_ejemplos_actualiza_botones_previamente_limitados(monkeypatch, herramienta):
    """Los ejemplos no conservan el estado deshabilitado de una dimensión anterior."""
    async def comprobar(vista, cliente):
        """Carga un ejemplo mayor tras llegar al mínimo editable."""
        if herramienta == 'leontief':
            from src.frontend.vistas.operaciones_matrices._ejemplos_leontief import EJEMPLOS_LEONTIEF
            assert not vista.boton_reducir.enabled
            ejemplo = next(dato for dato in EJEMPLOS_LEONTIEF if len(dato['matriz_coeficientes']) > 2)
            vista._cargar_ejemplo(ejemplo)
            assert vista.boton_reducir.enabled
        else:
            from src.frontend.vistas.operaciones_matrices._ejemplos_transformaciones import EJEMPLOS_TRANSFORMACIONES
            await vista._ajustar_filas(-1)
            assert not vista.boton_quitar_fila.enabled
            vista._cargar_ejemplo(EJEMPLOS_TRANSFORMACIONES[0])
            assert vista.boton_quitar_fila.enabled
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('herramienta', ['vectores', 'visualizador'])
def test_vectores_animados_conservan_datos_y_rehabilitan_controles_nuevos(monkeypatch, herramienta):
    """El panel compartido mantiene datos, dimensión y estado de los botones recreados."""
    async def comprobar(vista, cliente):
        """Comprueba las dos direcciones y las acciones de composición de la familia."""
        panel = vista.panel_combinacion if herramienta == 'vectores' else vista.panel_vectores
        nombre = next(iter(panel.vectores))
        panel.vectores[nombre]['celdas'][0] = '5/17'
        await panel.ajustar_dimension(1)
        assert panel.dimension == 4
        assert panel.vectores[nombre]['celdas'][0] == '5/17'
        await panel.ajustar_dimension(-1)
        cantidad = len(panel.vectores)
        if cantidad < panel.maximo_vectores:
            await panel._agregar_vector_animado()
            nuevo = list(panel.vectores)[-1]
            assert len(panel.vectores) == cantidad + 1
            orientacion = panel.vectores[nuevo].get('boton_orientacion')
            assert orientacion is None or orientacion.enabled
            await panel._eliminar_vector_animado(nuevo)
            assert len(panel.vectores) == cantidad
        assert panel.vectores[nombre]['celdas'][0] == '5/17'
    parametros = {'escena': 'vectores'} if herramienta == 'visualizador' else None
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar, parametros))
