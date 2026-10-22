"""Disponibilidad de recursos estáticos independiente del directorio de ejecución."""
from pathlib import Path
from unittest.mock import Mock

from src.frontend import aplicacion as modulo_aplicacion
from tests.comun import RAIZ


def test_recursos_estaticos_se_resuelven_desde_otro_directorio(monkeypatch, tmp_path):
    """La raíz de recursos corresponde al módulo, no al directorio de trabajo actual."""
    registrar = Mock()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(modulo_aplicacion, "_INICIALIZADO", False)
    monkeypatch.setattr(modulo_aplicacion.app, "add_static_files", registrar)
    monkeypatch.setattr(modulo_aplicacion, "registrar_rutas", Mock())
    modulo_aplicacion.inicializar_aplicacion()
    raiz_recursos = Path(registrar.call_args.args[1])
    assert raiz_recursos.is_absolute()
    assert raiz_recursos == RAIZ / "src/frontend/recursos"
    assert raiz_recursos.is_dir()


def test_favicon_se_resuelve_desde_otro_directorio(monkeypatch, tmp_path):
    """El arranque entrega a NiceGUI un favicon existente con ruta absoluta."""
    ejecutar_servidor = Mock()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(modulo_aplicacion, "inicializar_aplicacion", Mock())
    monkeypatch.setattr(modulo_aplicacion.ui, "run", ejecutar_servidor)
    monkeypatch.setenv("SCALARIS_ENV", "development")
    monkeypatch.setenv("STORAGE_SECRET", "secreto_ficticio_pruebas")
    modulo_aplicacion.ejecutar()
    icono = Path(ejecutar_servidor.call_args.kwargs["favicon"])
    assert icono.is_absolute()
    assert icono == RAIZ / "src/frontend/recursos/LogoOscuro.png"
    assert icono.is_file()
