"""Excepción acotada del proveedor, integridad y cobertura del código de captura propio."""
import hashlib

from tests.comun import RAIZ, ARCHIVOS_CSS
from tests.comun_javascript_embebido import PROVEEDORES_CLIENTE, fuentes_javascript


def test_proveedor_excluido_solo_de_estilo_con_distribucion_y_licencias_intactas():
    """La exclusión identifica un solo archivo oficial y exige su contenido y licencia MIT."""
    assert PROVEEDORES_CLIENTE == {'src/frontend/recursos/js/html2canvas.min.js'}
    ruta = RAIZ / next(iter(PROVEEDORES_CLIENTE))
    contenido = ruta.read_bytes().replace(b'\r\n', b'\n')
    assert hashlib.sha256(contenido).hexdigest() == 'e87e550794322e574a1fda0c1549a3c70dae5a93d9113417a429016838eab8cb'
    assert b'html2canvas 1.4.1' in contenido
    assert b'Released under MIT License' in contenido


def test_excepcion_no_excluye_el_adaptador_ni_otro_javascript_propio():
    """La captura nueva y los demás scripts propios conservan todas las auditorías de estilo."""
    rutas = sorted((RAIZ / 'src/frontend/recursos/js').glob('*.js'))
    auditadas = {fuente['ruta'] for fuente in fuentes_javascript(rutas)}
    assert 'src/frontend/recursos/js/captura_pdf.js' in auditadas
    assert auditadas == {ruta.relative_to(RAIZ).as_posix() for ruta in rutas} - PROVEEDORES_CLIENTE


def test_hoja_pdf_pertenece_al_inventario_de_cascada():
    """El inventario incluye los controles PDF justo después de los controles compartidos."""
    nombres = [ruta.name for ruta in ARCHIVOS_CSS]
    assert nombres[nombres.index('componentes_controles.css') + 1] == 'exportacion_pdf.css'
