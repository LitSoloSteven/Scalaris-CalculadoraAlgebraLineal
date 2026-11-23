"""Recorrido de Jacobi por la ruta pública y controles reales de NiceGUI."""
import asyncio

from nicegui import run, ui

from src.frontend.navegacion import ruta_de
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


def _registrar_vista(monkeypatch) -> None:
    monkeypatch.setitem(VISTAS_RUTAS, 'metodos_iterativos', (
        'algebra.sistemas_lineales.vista_metodos_iterativos', 'VistaMetodosIterativos',
    ))
    monkeypatch.setenv('SCALARIS_NAV', '1')


def _registrar_subespacios(monkeypatch) -> None:
    monkeypatch.setitem(VISTAS_RUTAS, 'espacios_subespacios', (
        'algebra.operaciones_vectores.vista_espacios_subespacios', 'VistaEspaciosSubespacios',
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


def _pulsar_boton(boton: ui.button) -> None:
    for escucha in boton._event_listeners.values():
        if escucha.type == 'click':
            escucha.handler(None)


def test_ruta_espacios_subespacios_analiza_criterios_y_recursos(monkeypatch):
    """Abre Espacios y subespacios, valida recursos, analiza el ejemplo y navega criterios."""
    _registrar_subespacios(monkeypatch)

    async def comprobar(vista, cliente):
        """Verifica enlace activo, recursos propios, veredicto y botones de criterio."""
        activos = [elemento._props.get('href') for elemento in cliente.elements.values()
                   if elemento._props.get('aria-current') == 'page']
        assert activos == [ruta_de('espacios_subespacios')]
        cabecera = cliente.head_html
        for recurso in ('vistas_subespacios.css', 'vistas_vectores.css', 'vistas_inversa.css', 'tema_graficos.js'):
            assert recurso in cabecera
        for ajeno in ('sistemas_metodo.js', 'vistas_metodos_iterativos.css'):
            assert ajeno not in cabecera
        vista.captura.cargar_ejemplo()
        await vista.analizar()
        assert vista.ultimo_resultado['dimension'] == 2
        etiquetas = [getattr(elemento, 'text', '') for elemento in vista.contenedor_resultados.descendants()]
        assert any('espacio vectorial con las operaciones usuales' in texto.lower() for texto in etiquetas)
        botones = [elemento for elemento in vista.contenedor_resultados.descendants()
                   if isinstance(elemento, ui.button) and 'subespacios-criterio-boton' in elemento.classes]
        assert len(botones) == 3
        claves_visitadas = []
        for boton in botones:
            _pulsar_boton(boton)
            paso = vista.reproductor_pasos.pasos[vista.reproductor_pasos.indice_actual]
            assert paso.cuerpo[0] == 'teorema'
            claves_visitadas.append(paso.cuerpo[1]['clave'])
        assert claves_visitadas == ['origen', 'suma', 'escalar']

    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar))


def test_espacios_subespacios_dimension_cero_limpieza_y_vigencia(monkeypatch):
    """Conserva etiquetas al redimensionar, distingue cero de vacío y descarta obsoletos."""
    _registrar_subespacios(monkeypatch)

    async def comprobar(vista, _cliente):
        """Comprueba redimensionado, cero explícito, limpieza y edición durante cálculo."""
        vista.captura.cargar_generadores({'etiqueta_larga': ['1', '2', '3']})
        vista.captura.panel.agregar_vector()
        assert list(vista.captura.obtener()['vectores']) == ['etiqueta_larga', 'v_1']
        await vista.captura.panel.ajustar_dimension(delta=1)
        assert vista.captura.obtener()['dimension_ambiente'] == 4
        assert vista.captura.obtener()['vectores']['etiqueta_larga']['datos'] == ['1', '2', '3', '']
        await vista.captura.panel.ajustar_dimension(delta=-1)
        vista.captura.cargar_generadores({'v_1': ['0', '0', '0']})
        await vista.analizar()
        assert vista.ultimo_resultado['es_subespacio_cero'] is True
        vista.captura.limpiar()
        assert vista.captura.obtener()['dimension_ambiente'] == 3
        await vista.analizar()
        assert vista.ultimo_resultado['estado'] == 'ERROR'
        assert vista.ultimo_resultado['codigo'] == 'ENTRADA_INVALIDA'

    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar))


def test_edicion_durante_analisis_subespacio_descarta_respuesta(monkeypatch):
    """Una edición durante el análisis impide publicar el resultado anterior."""
    _registrar_subespacios(monkeypatch)

    async def comprobar(vista, _cliente):
        """Retiene el trabajador mientras cambia la captura y confirma el descarte."""
        iniciado, continuar = asyncio.Event(), asyncio.Event()

        async def ejecutar(calcular, captura):
            """Notifica el arranque y espera a que la vista quede obsoleta."""
            iniciado.set()
            await continuar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, 'io_bound', ejecutar)
        vista.captura.cargar_ejemplo()
        solicitud = asyncio.create_task(vista.analizar())
        await iniciado.wait()
        vista.captura.panel._al_cambiar_celda_vector('v_1', 0, '5')
        continuar.set()
        await solicitud
        assert vista.ultimo_resultado is None
        assert vista.reproductor_pasos is None
        assert vista.boton_analizar._props.get('loading') == 'false'

    asyncio.run(construir_pagina(monkeypatch, 'espacios_subespacios', comprobar))
