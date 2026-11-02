"""Registro de clones y obligatoriedad condicional de las comprobaciones de inversa."""
import pytest

from src.frontend import tema, textos
from src.frontend.controladores.exportacion_pdf.figuras import preparar_figuras
from src.frontend.recursos_vistas import seleccionar_recursos
from tests.comun_exportacion_pdf import crear_captura


@pytest.mark.parametrize('vista', [
    'sistemas', 'inversa', 'leontief', 'transformaciones', 'determinantes',
    'factorizacion_lu', 'vectores', 'matrices', 'bases', 'romanos', 'visualizador',
])
def test_clon_se_registra_antes_del_capturador_en_todas_sus_vistas(vista):
    """El recurso extraído llega antes que su consumidor en cada página exportable."""
    cabecera = seleccionar_recursos(tema._CABECERA_HTML, vista)
    assert cabecera.index('/assets/js/clon_pdf.js') < cabecera.index('/assets/js/captura_pdf.js')
    assert 'inversa-comprobaciones' in textos.PDF_REGIONES_POR_HERRAMIENTA['inversa']


def test_inicio_no_carga_el_preparador_de_clones():
    """La página sin exportación no incorpora el módulo de captura extraído."""
    assert '/assets/js/clon_pdf.js' not in seleccionar_recursos(tema._CABECERA_HTML, 'inicio')


@pytest.mark.parametrize('estado', ['EXITO', 'SINGULAR'])
def test_resultado_con_comprobaciones_rechaza_su_region_ausente(estado):
    """La exportación falla explícitamente si perdería comprobaciones recibidas."""
    resultado = {'estado': estado, 'comprobaciones': [{'titulo': 'Comprobación recibida'}]}
    with pytest.raises(ValueError, match=textos.PDF_ERROR_IMAGEN):
        preparar_figuras('inversa', resultado, [crear_captura('inversa-resumen')])


@pytest.mark.parametrize('estado', ['EXITO', 'SINGULAR'])
def test_resultado_con_comprobaciones_incluye_su_figura(estado):
    """Las comprobaciones se conservan como figura registrada en éxito y singularidad."""
    capturas = [crear_captura(clave) for clave in ('inversa-resumen', 'inversa-comprobaciones')]
    figuras = preparar_figuras('inversa', {'estado': estado, 'comprobaciones': [{}]}, capturas)
    assert [figura['imagen'].clave for figura in figuras] == ['inversa-resumen', 'inversa-comprobaciones']


@pytest.mark.parametrize('comprobaciones', [{}, {'comprobaciones': []}])
def test_resultado_sin_comprobaciones_no_exige_una_figura_vacia(comprobaciones):
    """Una respuesta sin comprobaciones mantiene la exportación de su resumen."""
    figuras = preparar_figuras('inversa', {'estado': 'SINGULAR', **comprobaciones},
                              [crear_captura('inversa-resumen')])
    assert len(figuras) == 1
