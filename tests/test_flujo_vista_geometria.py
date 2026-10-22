"""Pruebas de confirmación y recuperación de figuras geométricas."""
import asyncio
from unittest.mock import MagicMock, AsyncMock
from nicegui import ui, run
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria
from tests.comun import ejecutar_trabajador_simulado
from tests.comun_geometria import preparar_fallo_figura, comprobar_recuperacion_figura


def test_actualizar_figura_inicial_fallida(monkeypatch):
    """Una figura inicial fallida no confirma ni expone resultados parciales."""
    async def comprobar():
        """Ejecuta el fallo inicial con los mismos controles de recuperación."""
        vista = VistaGeometria()
        vista.escena = 'rectas-planos'
        dobles = preparar_fallo_figura(monkeypatch, vista, {
            'matriz_a': [['1', '0'], ['0', '1']], 'vector_b': ['1', '2'],
        })
        await comprobar_recuperacion_figura(vista, dobles)

    asyncio.run(comprobar())


def test_actualizar_figura_reutilizada_fallida(monkeypatch):
    """Una figura reutilizada fallida permite reiniciar el dibujo sin datos obsoletos."""
    async def comprobar():
        """Ejecuta el fallo con figura reutilizada y datos previos almacenados."""
        vista = VistaGeometria()
        vista.escena = 'rectas-planos'
        vista._primer_dibujo = False
        grafica_simulada = MagicMock()
        vista._elemento_plotly = grafica_simulada
        vista._clave_figura = ('rectas-planos', 2)
        vista.ultimo_hash_entrada = 9999
        vista.ultimo_resultado = {'estado': 'EXITO', 'numero_variables': 2}
        dobles = preparar_fallo_figura(monkeypatch, vista, {
            'matriz_a': [['2', '0'], ['0', '2']], 'vector_b': ['2', '4'],
        })
        await comprobar_recuperacion_figura(vista, dobles)

    asyncio.run(comprobar())


def test_construir_figura_devuelve_booleano(monkeypatch):
    """La construcción distingue fracaso y éxito mediante su retorno booleano."""
    async def comprobar():
        """Comprueba ambos resultados de construcción con un cliente simulado."""
        vista = VistaGeometria()
        vista.contenedor_figura = MagicMock()
        monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=None))
        monkeypatch.setattr(ui, 'run_javascript', lambda *argumentos, **opciones: None)
        error_simulado = MagicMock()
        monkeypatch.setattr(vista, '_renderizar_error', error_simulado)
        resultado = await vista._construir_figura({}, 'rectas-planos')
        assert resultado is False
        error_simulado.assert_called_once()
        figura_simulada = MagicMock()
        monkeypatch.setattr(vista, '_obtener_solo_figura', AsyncMock(return_value=figura_simulada))
        monkeypatch.setattr(ui, 'plotly', lambda figura: MagicMock())
        monkeypatch.setattr(ui, 'element', lambda *argumentos, **opciones: MagicMock())
        resultado_segundo = await vista._construir_figura({}, 'rectas-planos')
        assert resultado_segundo is True

    asyncio.run(comprobar())
