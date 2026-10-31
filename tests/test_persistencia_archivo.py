"""Respaldos compatibles de sesiones ante bloqueos y cambios consecutivos."""
import asyncio
import json
import os
import threading

import pytest
from nicegui import background_tasks, core

from src.frontend import persistencia_archivo
from src.frontend.persistencia_archivo import DiccionarioPersistenteSeguro


def test_lee_json_existente_y_conserva_estructura_y_unicode(tmp_path):
    """El adaptador conserva sesiones anteriores y cambios anidados observables."""
    ruta = tmp_path / 'storage-user-prueba.json'
    datos = {'ia_historial_chat': [{'texto': 'Álgebra 1/3', 'enviado': True}], 'ia_panel_abierto': False}
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding='utf-8')
    almacen = DiccionarioPersistenteSeguro(ruta, encoding='utf-8', indent=True)
    almacen.initialize_sync()
    assert dict(almacen) == datos
    almacen['ia_historial_chat'][0]['texto'] = 'Matriz 2/3'
    persistido = json.loads(ruta.read_text(encoding='utf-8'))
    assert persistido['ia_historial_chat'][0]['texto'] == 'Matriz 2/3'
    assert persistido['ia_panel_abierto'] is False
    assert list(tmp_path.iterdir()) == [ruta]


def test_vaciado_sync_conserva_el_contrato_de_eliminar_archivo(tmp_path):
    """Vaciar un diccionario guardado elimina su archivo sin publicar un JSON vacío."""
    ruta = tmp_path / 'usuario.json'
    almacen = DiccionarioPersistenteSeguro(ruta, encoding='utf-8')
    almacen['dato'] = 1
    assert ruta.exists()
    almacen.clear()
    assert not ruta.exists()
    assert not list(tmp_path.iterdir())


async def _esperar_respaldos(almacen):
    clave = f'persistencia:{almacen.filepath.resolve()}'
    while clave in background_tasks.lazy_tasks_running:
        await background_tasks.lazy_tasks_running[clave]
        await asyncio.sleep(0)


def test_cambios_rapidos_se_serializan_y_retienen_el_ultimo(monkeypatch, tmp_path):
    """Un respaldo bloqueado no permite adelantar a los siguientes ni perder el último cambio."""
    async def comprobar():
        """Controla la escritura del trabajador y espera todas las tareas programadas."""
        monkeypatch.setattr(core, 'loop', asyncio.get_running_loop())
        ruta = tmp_path / 'usuario.json'
        almacen = DiccionarioPersistenteSeguro(ruta, encoding='utf-8')
        original = persistencia_archivo.guardar_archivo_atomico
        iniciado, liberar = threading.Event(), threading.Event()
        escrituras = []

        def guardar(destino, contenido, codificacion):
            """Detiene el primer respaldo sin bloquear el bucle de interfaz."""
            escrituras.append(json.loads(contenido)['dato'])
            iniciado.set()
            assert liberar.wait(3)
            original(destino, contenido, codificacion)

        monkeypatch.setattr(persistencia_archivo, 'guardar_archivo_atomico', guardar)
        almacen['dato'] = 1
        assert await asyncio.to_thread(iniciado.wait, 3)
        almacen['dato'] = 2
        almacen['dato'] = 3
        assert escrituras == [1]
        liberar.set()
        await _esperar_respaldos(almacen)
        assert escrituras == [1, 3]
        assert json.loads(ruta.read_text(encoding='utf-8')) == {'dato': 3}
        almacen.clear()
        await _esperar_respaldos(almacen)
        assert not ruta.exists()
    asyncio.run(comprobar())


@pytest.mark.skipif(os.name != 'nt', reason='Reproduce el bloqueo de reemplazo de Windows.')
def test_respaldo_async_se_recupera_y_mantiene_la_interfaz_activa(monkeypatch, tmp_path):
    """Un lector se cierra desde el bucle mientras el respaldo espera fuera de él."""
    async def comprobar():
        """Espera el respaldo real y verifica que la sesión completa queda guardada."""
        monkeypatch.setattr(core, 'loop', asyncio.get_running_loop())
        ruta = tmp_path / 'usuario.json'
        ruta.write_text('{"dato": 1}', encoding='utf-8')
        lector = ruta.open(encoding='utf-8')
        almacen = DiccionarioPersistenteSeguro(ruta, encoding='utf-8')
        try:
            almacen['dato'] = 2
            await asyncio.sleep(0.12)
            assert json.loads(lector.read()) == {'dato': 1}
        finally:
            lector.close()
        await _esperar_respaldos(almacen)
        assert json.loads(ruta.read_text(encoding='utf-8')) == {'dato': 2}
        assert list(tmp_path.iterdir()) == [ruta]
    asyncio.run(comprobar())
