"""Integración del adaptador con la fábrica NiceGUI y el arranque de Scalaris."""
from unittest.mock import Mock

import pytest
import nicegui.storage as almacenamiento_nicegui
from nicegui.persistence import FilePersistentDict

from src.frontend import aplicacion
from src.frontend.configuracion_persistencia import configurar_persistencia
from src.frontend.persistencia_archivo import DiccionarioPersistenteSeguro


def test_fabrica_crea_sesiones_seguras_sin_cambiar_rutas(monkeypatch, tmp_path):
    """La fábrica real conserva identificador, codificación y contrato del diccionario."""
    monkeypatch.setattr(almacenamiento_nicegui, 'FilePersistentDict', FilePersistentDict)
    monkeypatch.setattr(almacenamiento_nicegui.Storage, 'path', tmp_path)
    monkeypatch.setattr(almacenamiento_nicegui.Storage, 'redis_url', None)
    configurar_persistencia()
    configurar_persistencia()
    almacen = almacenamiento_nicegui.Storage._create_persistent_dict('user-prueba')
    assert isinstance(almacen, DiccionarioPersistenteSeguro)
    assert isinstance(almacen, FilePersistentDict)
    assert almacen.filepath == tmp_path / 'storage-user-prueba.json'
    assert almacen.encoding == 'utf-8'
    assert not list(tmp_path.iterdir())


def test_fabrica_redis_conserva_su_backend(monkeypatch):
    """La selección Redis explícita no se sustituye por persistencia de archivos."""
    devolver = object()
    constructor = Mock(return_value=devolver)
    monkeypatch.setattr(almacenamiento_nicegui, 'FilePersistentDict', FilePersistentDict)
    monkeypatch.setattr(almacenamiento_nicegui.Storage, 'redis_url', 'redis://ejemplo-prueba')
    monkeypatch.setattr(almacenamiento_nicegui, 'RedisPersistentDict', constructor)
    configurar_persistencia()
    assert almacenamiento_nicegui.Storage._create_persistent_dict('user-prueba') is devolver
    constructor.assert_called_once()


def test_no_reemplaza_un_adaptador_ajeno(monkeypatch):
    """Una integración personalizada se detecta antes de sustituir su comportamiento."""
    constructor = Mock()
    monkeypatch.setattr(almacenamiento_nicegui, 'FilePersistentDict', constructor)
    with pytest.raises(RuntimeError, match='otro adaptador'):
        configurar_persistencia()
    assert almacenamiento_nicegui.FilePersistentDict is constructor


def test_arranque_registra_persistencia_antes_de_las_rutas(monkeypatch):
    """Los constructores de página solo se registran después de seleccionar los respaldos seguros."""
    orden = []
    monkeypatch.setattr(aplicacion, '_INICIALIZADO', False)
    monkeypatch.setattr(aplicacion, 'configurar_persistencia', lambda: orden.append('persistencia'))
    monkeypatch.setattr(aplicacion, 'registrar_rutas', lambda: orden.append('rutas'))
    monkeypatch.setattr(aplicacion.app, 'add_static_files', Mock())
    monkeypatch.setattr(aplicacion, 'configurar_movimiento_componentes', Mock())
    aplicacion.inicializar_aplicacion()
    aplicacion.inicializar_aplicacion()
    assert orden == ['persistencia', 'rutas']
