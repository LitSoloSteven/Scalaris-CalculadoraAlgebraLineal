"""Estados, datos extremos y ciclo de vida de las vistas matriciales."""
import asyncio
from fractions import Fraction
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from nicegui import run, ui

from src.frontend.controladores import sesion_matricial
from src.frontend.controladores.operaciones_inversas.vista_previa import preparar_presentacion_previa
from src.frontend.controladores.sistemas_lineales.presentacion_solucion import formatear_elemento_solucion
from src.frontend.vistas.mixin_sesion_matricial import MixinSesionMatricial
from tests.comun_construccion_vistas import construir_pagina
from tests.comun_sesion_matricial import ejecutar_calculo_sesion


def etiquetas(vista) -> set[str]:
    """Devuelve los textos visibles dentro del contenedor de resultados montado."""
    return {elemento.text for elemento in vista.contenedor_resultados.descendants() if isinstance(elemento, ui.label)}


@pytest.mark.parametrize('herramienta', ['sistemas', 'inversa'])
def test_captura_vacia_y_limpieza_retiro_de_estado(monkeypatch, herramienta):
    """Ambas vistas comparten limpieza y retiran resultado, huella y reproductor."""
    async def comprobar(vista, cliente):
        """Comprueba vacio, ceros escritos y limpieza del contexto de la sesion."""
        assert vista.esta_completamente_vacio()
        assert 'Listo para' in ' '.join(etiquetas(vista))
        if herramienta == 'sistemas':
            vista.cuadricula.entradas_coeficientes[0][0].set_value('0')
        else:
            vista.panel_matriz_cuadrada.celdas[0][0].set_value('0')
        assert not vista.esta_completamente_vacio()
        vista.ultimo_resultado = {'estado': 'EXITO'}
        vista._huella_resultado = 'huella'
        detenido = []
        vista.reproductor_pasos = SimpleNamespace(detener=lambda: detenido.append(True))
        vista.limpiar_todo()
        assert detenido == [True]
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert vista.reproductor_pasos is None and vista.esta_completamente_vacio()
        assert vista.obtener_contexto_ia().estado.vacio
        assert type(vista).confirmar_limpieza is MixinSesionMatricial.confirmar_limpieza
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('datos,estado,texto', [
    ([['1001/1000']], 'EXITO', 'Matriz invertible'),
    ([['0']], 'SINGULAR', 'Matriz singular: no tiene inversa'),
    ([['1/0']], 'ERROR', 'Error'),
])
def test_estados_inversa_y_fracciones_exactas(monkeypatch, datos, estado, texto):
    """El renderer conserva exito exacto, singularidad y errores de celda."""
    async def comprobar(vista, cliente):
        """Calcula los datos reales y comprueba resultado, carga y contexto."""
        vista.panel_matriz_cuadrada.cargar_matriz(datos)
        vista.panel_matriz_cuadrada.celdas[0][0].set_value(datos[0][0])
        boton = ui.button('Calcular')
        await vista.calcular(boton)
        assert vista.ultimo_resultado['estado'] == estado
        assert boton._props['loading'] == 'false'
        if estado == 'EXITO':
            assert vista.ultimo_resultado['inversa'].datos == [[Fraction(1000, 1001)]]
            assert texto in etiquetas(vista)
        elif estado == 'SINGULAR':
            assert texto in etiquetas(vista)
        else:
            assert vista.ultimo_resultado['celda_error'] == [0, 0]
            assert any('cero' in etiqueta.lower() for etiqueta in etiquetas(vista))
    asyncio.run(construir_pagina(monkeypatch, 'inversa', comprobar))


@pytest.mark.parametrize('coeficientes,independientes,estado', [
    ([['1001/1000']], ['1'], 'SOLUCION_UNICA'),
    ([['0']], ['0'], 'SOLUCIONES_INFINITAS'),
    ([['0']], ['1'], 'SIN_SOLUCION'),
    ([['1/0']], ['1'], 'ERROR'),
])
def test_estados_sistema_montado(monkeypatch, coeficientes, independientes, estado):
    """La captura real presenta clasificaciones y errores sin perder precision."""
    async def comprobar(vista, cliente):
        """Comprueba los cuatro estados de la resolucion y el boton de carga."""
        vista.cuadricula.cargar_datos(coeficientes, independientes)
        vista.cuadricula.entradas_coeficientes[0][0].set_value(coeficientes[0][0])
        boton = ui.button('Resolver')
        await vista.resolver_sistema(boton)
        assert vista.ultimo_resultado['estado'] == estado
        assert boton._props['loading'] == 'false'
        assert etiquetas(vista)
        if estado == 'SOLUCION_UNICA':
            assert vista.ultimo_resultado['solucion'] == ['1000/1001']
    asyncio.run(construir_pagina(monkeypatch, 'sistemas', comprobar))


def test_inversa_cincuenta_por_cincuenta_y_vista_previa_limitada(monkeypatch):
    """Una matriz 50x50 conserva fracciones y muestra orientacion para su vista previa."""
    async def comprobar(vista, cliente):
        """Invierte una diagonal extrema y verifica ambos productos exactos."""
        datos = [['1001/1000' if fila == columna else '0' for columna in range(50)] for fila in range(50)]
        vista.panel_matriz_cuadrada.cargar_matriz(datos)
        vista._confirmar_calculo_grande = AsyncMock(return_value=True)
        await vista._actualizar_vista_previa()
        assert any('8×8' in elemento.text for elemento in vista.contenedor_vista_previa.descendants() if isinstance(elemento, ui.label))
        await vista.calcular(ui.button('Calcular'))
        resultado = vista.ultimo_resultado
        assert resultado['estado'] == 'EXITO' and resultado['dimension'] == 50
        assert all(resultado['inversa'].datos[indice][indice] == Fraction(1000, 1001) for indice in range(50))
        assert len(resultado['comprobaciones']) == 3
        assert all(comprobacion['coincide'] for comprobacion in resultado['comprobaciones'])
        assert vista.historial[0]['datos'] == datos
        assert vista.obtener_contexto_ia().resultado['inversa_omitida'] is True
    asyncio.run(construir_pagina(monkeypatch, 'inversa', comprobar))


@pytest.mark.parametrize('herramienta', ['sistemas', 'inversa'])
def test_respuesta_pendiente_descartada_tras_edicion(monkeypatch, herramienta):
    """Una respuesta del trabajador no se vincula a los datos editados mientras esperaba."""
    async def comprobar(vista, cliente):
        """Edita las celdas dentro del trabajador y exige descartar el resultado viejo."""
        if herramienta == 'sistemas':
            vista.cuadricula.cargar_datos([['2']], ['1'])
        else:
            vista.panel_matriz_cuadrada.cargar_matriz([['2']])
        async def trabajador(funcion, *argumentos):
            """Conserva el calculo real y simula una edicion durante su espera."""
            resultado = funcion(*argumentos)
            if herramienta == 'sistemas':
                vista.cuadricula.entradas_coeficientes[0][0].set_value('3')
            else:
                vista.panel_matriz_cuadrada.celdas[0][0].set_value('3')
            return resultado
        monkeypatch.setattr(run, 'io_bound', trabajador)
        boton = await ejecutar_calculo_sesion(vista, herramienta)
        assert vista.ultimo_resultado is None and vista._huella_resultado is None
        assert not vista.historial
        assert any('Los datos cambiaron.' in texto for texto in etiquetas(vista))
        assert boton._props['loading'] == 'false'
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


@pytest.mark.parametrize('herramienta', ['sistemas', 'inversa'])
def test_error_inesperado_no_filtra_entrada_y_finaliza_carga(monkeypatch, herramienta, caplog):
    """Los errores del trabajador presentan orientacion sin registrar datos sensibles."""
    async def comprobar(vista, cliente):
        """Inyecta un fallo con datos privados y comprueba el estado recuperable."""
        if herramienta == 'sistemas':
            vista.cuadricula.cargar_datos([['2']], ['1'])
        else:
            vista.panel_matriz_cuadrada.cargar_matriz([['2']])
        monkeypatch.setattr(run, 'io_bound', AsyncMock(side_effect=RuntimeError('entrada privada')))
        boton = await ejecutar_calculo_sesion(vista, herramienta)
        assert 'entrada privada' not in ' '.join(etiquetas(vista))
        assert 'entrada privada' not in caplog.text
        assert any('Revisa los datos' in texto for texto in etiquetas(vista))
        assert boton._props['loading'] == 'false' and vista.ultimo_resultado is None
    asyncio.run(construir_pagina(monkeypatch, herramienta, comprobar))


def test_historial_es_copia_independiente_y_retiene_cinco():
    """Las ediciones posteriores no cambian la captura conservada en el historial."""
    historial = []
    datos = {'datos': [['1001/1000']], 'dimension': 1, 'estado': 'EXITO', 'determinante': '1001/1000'}
    sesion_matricial.registrar_calculo(historial, datos)
    datos['datos'][0][0] = '2'
    assert historial[0]['datos'] == [['1001/1000']]
    for indice in range(8):
        sesion_matricial.registrar_calculo(historial, dict(datos, determinante=str(indice)))
    assert len(historial) == 5
    assert [registro['determinante'] for registro in historial] == ['7', '6', '5', '4', '3']


def test_espera_cancelable_cancela_sustitucion_y_desmontaje(monkeypatch):
    """El espera cancelable compartido publica solo la tarea vigente y cancela al desmontar."""
    async def escenario():
        """Programa sustitucion, ejecuta la ultima tarea y cancela un desmontaje."""
        monkeypatch.setattr(sesion_matricial, 'ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS', 0)
        actualizar = AsyncMock()
        vista = SimpleNamespace(tarea_vista_previa=None, contenedor_vista_previa=SimpleNamespace(is_deleted=False), _actualizar_vista_previa=actualizar)
        sesion_matricial.programar_vista_previa(vista)
        anterior = vista.tarea_vista_previa
        sesion_matricial.programar_vista_previa(vista)
        await asyncio.gather(anterior, vista.tarea_vista_previa, return_exceptions=True)
        assert anterior.cancelled() and actualizar.await_count == 1
        sesion_matricial.programar_vista_previa(vista)
        ultima = vista.tarea_vista_previa
        sesion_matricial.cancelar_vista_previa(vista)
        await asyncio.gather(ultima, return_exceptions=True)
        assert ultima.cancelled() and vista.tarea_vista_previa is None
        assert actualizar.await_count == 1
    asyncio.run(escenario())


def test_presentacion_escapa_texto_y_conserva_fraccion():
    """Las etiquetas y valores largos se escapan sin truncar fracciones."""
    variable, latex, valor = formatear_elemento_solucion('<script>', '1001/1000<img>')
    assert '<script>' not in variable and '&lt;script&gt;' in variable
    assert '<img>' not in valor and '1001/1000' in valor
    assert '&lt;script&gt;' in latex
    assert preparar_presentacion_previa([['1001/1000']], 1)['identificadores'] == ['inversa-previa-matriz', 'inversa-previa-aumentada']
