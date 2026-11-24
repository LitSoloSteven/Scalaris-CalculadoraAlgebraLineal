"""Navegación y vigencia al cambiar el método de una captura iterativa."""
import asyncio

import pytest
from nicegui import run

from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


@pytest.fixture(autouse=True)
def registrar_vista_iterativa(monkeypatch):
    """Incluye el constructor de la página iterativa en el montaje de pruebas."""
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))


@pytest.mark.parametrize(('parametros', 'metodo', 'nombre'), [
    ({}, 'jacobi', 'Jacobi'),
    ({'method': 'jacobi'}, 'jacobi', 'Jacobi'),
    ({'method': 'gauss-seidel'}, 'gauss-seidel', 'Gauss-Seidel'),
    ({'method': 'desconocido'}, 'jacobi', 'Jacobi'),
])
def test_ruta_inicial_selecciona_metodo(monkeypatch, parametros, metodo, nombre):
    """El constructor público activa el método indicado o el predeterminado."""
    async def comprobar(vista, cliente):
        """Comprueba la selección, el título y el contexto del método activo."""
        assert vista.selector_metodo.value == metodo
        assert cliente.title == f'{nombre} | Scalaris'
        assert vista.obtener_contexto_ia().etiqueta == nombre

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar, parametros))


def test_cambiar_metodo_interrumpe_reproduccion_y_conserva_el_borrador(monkeypatch):
    """La selección retira el procedimiento y conserva parámetros, texto e incógnitas."""
    async def comprobar(vista, _cliente):
        """Arranca una reproducción real y cambia al otro método sobre la misma captura."""
        captura = vista.captura
        captura.restablecer(True)
        captura.selector.set_value('ecuaciones')
        captura.ecuaciones.set_value('8a - b + c = 5\n2a + 10b - c = 23\na - b + 6c = -7')
        captura._campos_vector()[0].set_value('1/2')
        captura.tolerancia.set_value('0.002')
        captura.maximo.set_value('20')
        borrador = captura.obtener()
        await vista.resolver()
        reproductor = vista.reproductor_pasos
        reproductor._alternar_reproduccion()
        temporizador = reproductor.temporizador
        assert temporizador.active
        vista.selector_metodo.set_value('gauss-seidel')
        assert temporizador.is_deleted
        assert vista.reproductor_pasos is None
        assert vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert captura.obtener() == borrador
        await vista.resolver()
        assert vista.ultimo_resultado['metodo'] == 'gauss-seidel'
        assert vista.ultimo_resultado['variables'] == ['a', 'b', 'c']
        assert vista.ultimo_resultado['pasos'][0]['vector_anterior'] == ('1/2', '0', '0')

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar))


@pytest.mark.parametrize('falla', [False, True])
def test_una_respuesta_tardia_no_reemplaza_el_otro_metodo(monkeypatch, falla):
    """Una respuesta o excepción tardía de Jacobi no reemplaza a Gauss-Seidel."""
    async def comprobar(vista, _cliente):
        """Retiene Jacobi hasta que la segunda solicitud publique el resultado vigente."""
        iniciado, liberar = asyncio.Event(), asyncio.Event()

        async def ejecutar(calcular, captura):
            """Simula el orden de finalización de los dos trabajadores."""
            if captura['metodo'] == 'jacobi':
                iniciado.set()
                await liberar.wait()
                if falla:
                    raise RuntimeError('fallo de la solicitud anterior')
            return calcular(captura)

        monkeypatch.setattr(run, 'io_bound', ejecutar)
        vista.captura.restablecer(True)
        antigua = asyncio.create_task(vista.resolver())
        await iniciado.wait()
        vista.selector_metodo.set_value('gauss-seidel')
        assert vista.boton_resolver.props.get('loading') == 'false'
        await vista.resolver()
        vigente = vista.ultimo_resultado
        liberar.set()
        await antigua
        assert vista.ultimo_resultado is vigente
        assert vigente['metodo'] == 'gauss-seidel'
        assert len(vista.reproductor_pasos.pasos) == 4
        assert vista.estado.text == ''

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar))
