"""Muestreo intermedio y orden documental independientes del orden de transporte."""
import pytest

from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor
from src.frontend.controladores.exportacion_pdf.documento import generar_pdf
from src.frontend.controladores.exportacion_pdf.figuras import preparar_figuras
from src.frontend.controladores.exportacion_pdf.secuencia import seleccionar_intermedios
from tests.comun_exportacion_pdf import PORTADA, crear_captura


@pytest.mark.parametrize('cantidad,esperados', [(0, []), (1, []), (2, []), (3, [1]),
                                              (4, [1, 2]), (5, [1, 2, 3]), (11, [1, 5, 9])])
def test_muestreo_reparte_interiores_sin_duplicar(cantidad, esperados):
    """Los procedimientos cortos no inventan pasos y los largos cubren su recorrido."""
    pasos = tuple(PasoReproductor(indice, 'inicial' if indice == 0 else 'operacion', str(indice))
                  for indice in range(cantidad))
    assert [paso.indice for paso in seleccionar_intermedios(pasos)] == esperados


def test_muestreo_excluye_resultados_y_desarrollos_posteriores():
    """Una comprobación o un desarrollo tras el resultado no se presenta como intermedio."""
    tipos = ('planteamiento', 'inicial', 'eliminacion', 'resultado', 'operacion', 'verificacion')
    pasos = tuple(PasoReproductor(indice, tipo, tipo) for indice, tipo in enumerate(tipos))
    assert [paso.indice for paso in seleccionar_intermedios(pasos)] == [2]


def test_primera_operacion_real_se_conserva_como_intermedio():
    """Una expresión con dos operaciones exporta la primera antes de su resultado final."""
    pasos = tuple(PasoReproductor(indice, 'operacion', str(indice)) for indice in range(2))
    assert seleccionar_intermedios(pasos) == (pasos[0],)


def test_figuras_ordenan_entrada_pasos_resultado_y_comprobaciones():
    """El transporte desordenado no afecta al recorrido editorial del documento."""
    claves = ['inversa-comprobaciones', 'inversa-resultado', 'inversa-paso-3',
              'inversa-resumen', 'inversa-paso-1', 'inversa-entrada', 'inversa-paso-2']
    figuras = preparar_figuras('inversa', {'estado': 'EXITO', 'comprobaciones': [True]},
                              [crear_captura(clave) for clave in claves])
    assert [figura['imagen'].clave for figura in figuras] == [
        'inversa-entrada', 'inversa-paso-1', 'inversa-paso-2', 'inversa-paso-3',
        'inversa-resumen', 'inversa-resultado', 'inversa-comprobaciones']


@pytest.mark.parametrize('adicional', ['inversa-paso-4', 'inversa-procedimiento', 'ajena'])
def test_secuencia_rechaza_pasadas_fuera_del_contrato(adicional):
    """Una secuencia no admite pasos ilimitados ni la captura duplicada del reproductor."""
    claves = ['inversa-entrada', 'inversa-resumen', adicional]
    with pytest.raises(ValueError, match='capturas'):
        preparar_figuras('inversa', {'estado': 'EXITO'}, [crear_captura(clave) for clave in claves])


def test_pdf_numeracion_y_comprobacion_final():
    """ReportLab conserva títulos y numeración consecutiva en el orden solicitado."""
    claves = ['sistemas-verificaciones', 'sistemas-resumen', 'sistemas-paso-3',
              'sistemas-paso-2', 'sistemas-entrada', 'sistemas-paso-1']
    documento, _ = generar_pdf('sistemas', dict(PORTADA), {'estado': 'SOLUCION_UNICA'},
                               [crear_captura(clave) for clave in claves])
    titulos = [b'Datos Introducidos', b'Paso Intermedio 1', b'Paso Intermedio 2', b'Paso Intermedio 3',
               b'Clasificaci', b'Comprobaciones del Resultado']
    posiciones = [documento.index(titulo) for titulo in titulos]
    assert posiciones == sorted(posiciones)
    assert all(f'(Figura {numero})'.encode('ascii') in documento for numero in range(1, 7))
