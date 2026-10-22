"""Carga de todos los sucesores del módulo de interacciones y alcance de auditoría."""
import json
from src.frontend import tema
from tests.comun import RAIZ
from tests.comun_javascript import leer_interacciones_cliente


def test_cabecera_carga_catalogo_entre_tema_y_consumidores(monkeypatch):
    """La carga conserva el orden y registra una vez cada recurso del catálogo."""
    cabeceras = []
    monkeypatch.setattr(tema.ui, "add_head_html", cabeceras.append)
    monkeypatch.setattr(tema.banderas, "panel_lateral_habilitado", lambda: False)
    tema.configurar_tema()
    assert len(cabeceras) == 1
    nombres = json.loads((RAIZ / "src/frontend/recursos/catalogo_interacciones.json").read_text(encoding="utf-8"))
    posiciones = [cabeceras[0].index(f'/assets/js/{nombre}') for nombre in nombres]
    assert posiciones == sorted(posiciones)
    assert cabeceras[0].index('/assets/js/tema.js') < posiciones[0]
    assert posiciones[-1] < cabeceras[0].index('/assets/js/cuadricula_compartida.js')
    assert all(cabeceras[0].count(f'/assets/js/{nombre}') == 1 for nombre in nombres)


def test_lector_conjunto_conserva_todas_las_responsabilidades():
    """Las comprobaciones negativas conservan el alcance de todos los recursos separados."""
    contenido = leer_interacciones_cliente()
    assert "registrarEntradaGlobal" in contenido
    assert "registrarRenderizadoMathJax" in contenido
    assert "registrarEscrituraProgresiva" in contenido
    assert "registrarTemaGraficos" in contenido
