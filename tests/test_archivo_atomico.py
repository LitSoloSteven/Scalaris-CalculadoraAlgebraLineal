"""Regresiones de atomicidad y bloqueos reales del reemplazo de archivos."""
import json
import os
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.frontend import archivo_atomico


def _error_windows(codigo: int = 5) -> PermissionError:
    error = PermissionError('Archivo ocupado')
    error.winerror = codigo
    return error


@pytest.mark.parametrize('codigo', [5, 32, 33])
def test_reintenta_sin_publicar_contenido_parcial_y_limpia_temporal(monkeypatch, tmp_path, codigo):
    """Dos bloqueos conservan el destino anterior hasta que el reemplazo termina."""
    destino = tmp_path / 'usuario.json'
    destino.write_text('{"anterior": 1}', encoding='utf-8')
    reemplazar = Path.replace
    esperas = Mock()
    llamadas = []

    def reemplazar_ocupado(temporal, final):
        """Comprueba el archivo anterior en cada intento que simula un bloqueo de Windows."""
        llamadas.append(temporal)
        if len(llamadas) < 3:
            assert json.loads(final.read_text(encoding='utf-8')) == {'anterior': 1}
            raise _error_windows(codigo)
        return reemplazar(temporal, final)

    monkeypatch.setattr(Path, 'replace', reemplazar_ocupado)
    monkeypatch.setattr(archivo_atomico.time, 'sleep', esperas)
    archivo_atomico.guardar_archivo_atomico(destino, '{"actual": 2}')
    assert json.loads(destino.read_text(encoding='utf-8')) == {'actual': 2}
    assert len(llamadas) == 3 and len(set(llamadas)) == 1
    assert [llamada.args[0] for llamada in esperas.call_args_list] == [0.05, 0.1]
    assert list(tmp_path.iterdir()) == [destino]


def test_bloqueo_permanente_es_acotado_y_conserva_el_archivo(monkeypatch, tmp_path):
    """Agotar intentos propaga el error original sin borrar datos previos ni dejar temporales."""
    destino = tmp_path / 'usuario.json'
    destino.write_text('anterior', encoding='utf-8')
    reemplazar = Mock(side_effect=_error_windows())
    esperas = Mock()
    monkeypatch.setattr(Path, 'replace', reemplazar)
    monkeypatch.setattr(archivo_atomico.time, 'sleep', esperas)
    with pytest.raises(PermissionError):
        archivo_atomico.guardar_archivo_atomico(destino, 'actual')
    assert destino.read_text(encoding='utf-8') == 'anterior'
    assert reemplazar.call_count == archivo_atomico.INTENTOS_REEMPLAZO
    assert esperas.call_count == archivo_atomico.INTENTOS_REEMPLAZO - 1
    assert max(llamada.args[0] for llamada in esperas.call_args_list) <= archivo_atomico.ESPERA_MAXIMA
    assert list(tmp_path.iterdir()) == [destino]


@pytest.mark.parametrize('error', [ValueError('Ruta inválida'), OSError('Disco no disponible'),
                                 PermissionError('Permiso no relacionado'), _error_windows(6)])
def test_no_reintenta_errores_ajenos_al_bloqueo(monkeypatch, tmp_path, error):
    """Un error de disco o permisos sin el código Windows esperado se propaga una sola vez."""
    reemplazar = Mock(side_effect=error)
    monkeypatch.setattr(Path, 'replace', reemplazar)
    esperas = Mock()
    monkeypatch.setattr(archivo_atomico.time, 'sleep', esperas)
    with pytest.raises(type(error)):
        archivo_atomico.guardar_archivo_atomico(tmp_path / 'usuario.json', 'actual')
    assert reemplazar.call_count == 1
    esperas.assert_not_called()
    assert not list(tmp_path.iterdir())


@pytest.mark.skipif(os.name != 'nt', reason='El bloqueo de reemplazo corresponde a Windows.')
def test_winerror_5_real_se_recupera_al_cerrar_el_lector(tmp_path):
    """Mantiene el destino abierto y verifica que el respaldo termina cuando se libera."""
    destino = tmp_path / 'usuario.json'
    destino.write_text('{"anterior": 1}', encoding='utf-8')
    lector = destino.open(encoding='utf-8')
    liberador = threading.Timer(0.12, lector.close)
    liberador.start()
    try:
        archivo_atomico.guardar_archivo_atomico(destino, '{"actual": 2}')
    finally:
        liberador.join()
        lector.close()
    assert json.loads(destino.read_text(encoding='utf-8')) == {'actual': 2}
    assert list(tmp_path.iterdir()) == [destino]
