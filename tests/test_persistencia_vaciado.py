"""Protección del archivo de una sesión nueva ante borrados antiguos en espera."""
import asyncio
import json
import threading
from pathlib import Path

from nicegui import core

from src.frontend import archivo_atomico
from src.frontend.persistencia_archivo import DiccionarioPersistenteSeguro
from tests.test_persistencia_archivo import _esperar_respaldos


def test_borrado_antiguo_revalida_directorio_despues_de_esperar(monkeypatch, tmp_path):
    """Un bloqueo al borrar no permite eliminar el archivo publicado por una sesión posterior."""
    async def comprobar():
        """Pausa entre intentos de borrado y sustituye el directorio antes de liberar el trabajador."""
        monkeypatch.setattr(core, 'loop', asyncio.get_running_loop())
        carpeta = tmp_path / 'almacen'
        carpeta.mkdir()
        ruta = carpeta / 'usuario.json'
        ruta.write_text('{"dato": "anterior"}', encoding='utf-8')
        almacen = DiccionarioPersistenteSeguro(ruta, encoding='utf-8')
        esperando, continuar = threading.Event(), threading.Event()
        eliminar = Path.unlink

        def eliminar_bloqueado(destino, **opciones):
            """Simula un bloqueo de Windows mientras el archivo sigue en su directorio anterior."""
            error = PermissionError('Archivo ocupado')
            error.winerror = 5
            raise error

        def esperar(duracion):
            """Cede al bucle para sustituir el directorio durante la pausa del reintento."""
            esperando.set()
            assert continuar.wait(3)

        monkeypatch.setattr(Path, 'unlink', eliminar_bloqueado)
        monkeypatch.setattr(archivo_atomico.time, 'sleep', esperar)
        almacen.backup()
        assert await asyncio.to_thread(esperando.wait, 3)
        eliminar(ruta)
        carpeta.rmdir()
        carpeta.mkdir()
        ruta.write_text('{"dato": "sesion nueva"}', encoding='utf-8')
        continuar.set()
        await _esperar_respaldos(almacen)
        assert json.loads(ruta.read_text(encoding='utf-8')) == {'dato': 'sesion nueva'}
    asyncio.run(comprobar())
