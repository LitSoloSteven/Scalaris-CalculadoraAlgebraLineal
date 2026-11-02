"""Contrato documental opcional separado de la entrada que identifica el cálculo."""
from types import SimpleNamespace

from src.frontend.controladores.captura_contexto import capturar_matrices_documento
from src.frontend.controladores.exportacion_pdf.vigencia import EnlacePDF


def test_enlace_anterior_reutiliza_su_entrada_sin_proveedor():
    """Las herramientas existentes conservan su contrato sin registrar otro callback."""
    entrada = {'datos': [['1']]}
    enlace = EnlacePDF(SimpleNamespace(), lambda: entrada, 'raiz')
    assert enlace.entrada_documental() is entrada


def test_proveedor_documental_no_sustituye_entrada_de_huella():
    """El documento puede recibir datos completos mientras la huella usa su captura original."""
    entrada = {'matrices': {'A': {(0, 0): '1'}}}
    documental = {'matrices': {'A': [['1', '0'], ['0', '0']]}}
    enlace = EnlacePDF(SimpleNamespace(), lambda: entrada, 'raiz',
                       leer_entrada_documental=lambda: documental)
    assert enlace.entrada() is entrada
    assert enlace.entrada_documental() is documental


def test_preparacion_documental_no_muta_las_celdas_ni_interpreta_expresiones():
    """El formato conserva texto íntegro y dimensiones sin modificar la cuadrícula recibida."""
    datos = {'A': {'datos': [['1/3', ''], ['', '0']]}}
    documento = capturar_matrices_documento(datos, 'A + A')
    assert documento == {'expresion': 'A + A', 'matrices': {'A': [['1/3', '0'], ['0', '0']]}}
    assert datos['A']['datos'] == [['1/3', ''], ['', '0']]
