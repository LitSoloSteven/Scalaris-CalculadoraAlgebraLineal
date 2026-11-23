"""Recorrido de Jacobi por la ruta pública y controles reales de NiceGUI."""
import asyncio

from nicegui import run

from src.frontend.navegacion import ruta_de
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


def _registrar_vista(monkeypatch) -> None:
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))
    monkeypatch.setenv('SCALARIS_NAV', '1')


def test_ruta_de_jacobi_resuelve_y_navega_al_barrido(monkeypatch):
    """Abre la ruta registrada, resuelve el ejemplo y conserva la traza en ambos modos."""
    _registrar_vista(monkeypatch)

    async def comprobar(vista, cliente):
        """Comprueba el resultado, el foco lógico y la conservación del texto."""
        activos = [elemento._props.get('href') for elemento in cliente.elements.values()
                   if elemento._props.get('aria-current') == 'page']
        assert activos == [ruta_de('metodos_iterativos')]
        captura = vista.captura
        assert captura.obtener()['vector_inicial'] == ['0', '0', '0']
        captura.restablecer(True)
        await vista.resolver()
        matriz = vista.ultimo_resultado
        assert matriz['codigo'] == 'TOLERANCIA_ALCANZADA'
        assert len(vista.reproductor_pasos.pasos) == 6
        vista.reproductor_pasos.ir_a(5)
        assert vista.reproductor_pasos.indice_actual == 5
        captura.selector.set_value('ecuaciones')
        assert captura.modo == 'ecuaciones'
        assert vista.ultimo_resultado is None
        await vista.resolver()
        assert vista.ultimo_resultado == matriz
        borrador = 'a + b = 1'
        captura.ecuaciones.set_value(borrador)
        captura.selector.set_value('matriz')
        assert captura.selector.value == 'ecuaciones'
        assert captura.ecuaciones.value == borrador
        await vista.resolver()
        assert vista.ultimo_resultado['codigo'] == 'ENTRADA_INVALIDA'
        assert captura.ecuaciones._props.get('aria-invalid') == 'true'

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar))


def test_edicion_descarta_una_respuesta_anterior(monkeypatch):
    """Una edición durante el cálculo impide publicar incluso si se repone el mismo texto."""
    _registrar_vista(monkeypatch)

    async def comprobar(vista, cliente):
        """Retiene el trabajador hasta que la captura haya cambiado dos veces."""
        iniciado, continuar = asyncio.Event(), asyncio.Event()

        async def ejecutar(calcular, captura):
            """Notifica el inicio y espera la señal de la prueba antes de calcular."""
            iniciado.set()
            await continuar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, 'io_bound', ejecutar)
        vista.captura.restablecer(True)
        solicitud = asyncio.create_task(vista.resolver())
        await iniciado.wait()
        vista.captura.tolerancia.set_value('')
        vista.captura.tolerancia.set_value('0.001')
        continuar.set()
        await solicitud
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
        assert vista.boton_resolver._props.get('loading') == 'false'

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar))


def test_el_inicio_conserva_componentes_al_ampliar_y_ordenar_incognitas(monkeypatch):
    """Amplía el inicio con ceros y mantiene los valores de las incógnitas que ya existían."""
    _registrar_vista(monkeypatch)

    async def comprobar(vista, cliente):
        """Inserta una incógnita antes de dos componentes editadas y amplía la matriz."""
        captura = vista.captura
        captura.selector.set_value('ecuaciones')
        captura.ecuaciones.set_value('y = 1\nz = 2')
        campos = captura._campos_vector()
        campos[0].set_value('1/2')
        campos[1].set_value('')
        captura.ecuaciones.set_value('a = 0\ny = 1\nz = 2')
        assert captura.obtener()['vector_inicial'] == ['0', '1/2', '']
        captura.selector.set_value('matriz')
        await captura.cuadricula.ajustar_tamano(incremento_columnas=1)
        assert captura.obtener()['vector_inicial'] == ['0', '1/2', '', '0']

    asyncio.run(construir_pagina(monkeypatch, 'metodos_iterativos', comprobar))
