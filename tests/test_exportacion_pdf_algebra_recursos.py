"""Carga del capturador y estilos PDF exclusivamente en las rutas que los consumen."""
import pytest

from src.frontend.recursos_vistas import seleccionar_recursos
from src.frontend import tema
from tests.comun_exportacion_algebra import HERRAMIENTAS


@pytest.mark.parametrize('herramienta', ('sistemas', *HERRAMIENTAS))
def test_exportadores_reciben_script_y_estilos_pdf(herramienta):
    """Cada exportador dispone del espacio de nombres cliente y de su diálogo accesible."""
    cabecera = seleccionar_recursos(tema._CABECERA_HTML, herramienta)
    assert '/assets/js/captura_pdf.js' in cabecera
    assert '/assets/css/exportacion_pdf.css' in cabecera
    assert '/assets/js/html2canvas.min.js' not in cabecera


@pytest.mark.parametrize('herramienta', ('inicio', 'bases', 'romanos', 'visualizador'))
def test_rutas_sin_exportador_no_cargan_recursos_pdf(herramienta):
    """Las vistas sin exportador conservan su selección de recursos existente."""
    cabecera = seleccionar_recursos(tema._CABECERA_HTML, herramienta)
    assert '/assets/js/captura_pdf.js' not in cabecera
    assert '/assets/css/exportacion_pdf.css' not in cabecera
