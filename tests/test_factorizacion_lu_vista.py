"""Integración de la página y ciclo de sesión de factorización LU."""
import asyncio
from types import SimpleNamespace

from nicegui import run, ui

from src.frontend.navegacion import elementos_navegacion, ruta_de
from src.frontend.recursos_vistas import seleccionar_recursos
from tests.comun_construccion_vistas import VISTAS_RUTAS, construir_pagina


def test_navegacion_y_recursos():
    """Comprueba la ruta, su orden y la selección de recursos de álgebra."""
    claves = [elemento.clave for elemento in elementos_navegacion("algebra")]
    assert claves[claves.index("determinantes") + 1] == "factorizacion_lu"
    assert ruta_de("factorizacion_lu") == "/algebra-lineal/factorizacion-lu"
    cabecera = '<link rel="stylesheet" href="/assets/css/vistas_inversa.css"><script src="/assets/js/inicio.js"></script>'
    assert 'vistas_inversa.css' in seleccionar_recursos(cabecera, 'factorizacion_lu')
    assert 'inicio.js' not in seleccionar_recursos(cabecera, 'factorizacion_lu')


def test_sesion_factorizacion(monkeypatch):
    """Monta la ruta real y comprueba cálculo, errores, historial y restauración."""
    monkeypatch.setitem(VISTAS_RUTAS, 'factorizacion_lu', ('operaciones_matrices.vista_factorizacion_lu', 'VistaFactorizacionLU'))

    async def comprobar(vista, cliente):
        """Ejercita el ciclo de una captura rectangular y una celda inválida."""
        boton = ui.button('Calcular')
        await vista.calcular(SimpleNamespace(sender=boton))
        assert vista.ultimo_resultado is None and not vista.historial
        vista.panel_matriz.cargar_matriz([['1', '2', '3'], ['4', '5', '6']])
        await vista.calcular(SimpleNamespace(sender=boton))
        assert vista.ultimo_resultado['estado'] == 'EXITO'
        assert len(vista.historial) == 1 and vista.reproductor_pasos is not None
        registro = vista.historial[0]
        reproductor_anterior = vista.reproductor_pasos
        detenido = []
        monkeypatch.setattr(reproductor_anterior, 'detener', lambda: detenido.append(True))
        await vista.calcular(SimpleNamespace(sender=boton))
        assert detenido and len(vista.historial) == 2
        vista.historial.pop()
        vista.panel_matriz.cargar_matriz([['mal']])
        assert vista.ultimo_resultado is None
        await vista.calcular(SimpleNamespace(sender=boton))
        assert vista.ultimo_resultado['estado'] == 'ERROR' and len(vista.historial) == 1
        vista._restaurar_historial(registro)
        assert vista.ultimo_resultado is None and vista.panel_matriz.obtener_datos_matriz() == registro['datos']
        vista.limpiar_todo()
        assert vista.panel_matriz.esta_vacio()

    asyncio.run(construir_pagina(monkeypatch, 'factorizacion_lu', comprobar))


def test_respuesta_obsoleta_no_se_publica(monkeypatch):
    """Descarta un resultado cuando la captura cambia durante el cálculo."""
    monkeypatch.setitem(VISTAS_RUTAS, 'factorizacion_lu', ('operaciones_matrices.vista_factorizacion_lu', 'VistaFactorizacionLU'))

    async def comprobar(vista, cliente):
        """Simula una edición mientras el trabajador produce el resultado."""
        vista.panel_matriz.cargar_matriz([['2']])

        async def trabajador(funcion, captura):
            """Edita la captura después de calcular la respuesta anterior."""
            resultado = funcion(captura)
            vista.panel_matriz.cargar_matriz([['3']])
            return resultado

        monkeypatch.setattr(run, 'io_bound', trabajador)
        await vista.calcular(SimpleNamespace(sender=ui.button('Calcular')))
        assert vista.ultimo_resultado is None and not vista.historial

    asyncio.run(construir_pagina(monkeypatch, 'factorizacion_lu', comprobar))
