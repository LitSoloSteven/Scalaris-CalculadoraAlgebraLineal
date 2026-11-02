"""Alfabeto compartido y saneamiento numérico sin anticipar validación de dominio."""
import json
import re
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.frontend import tema
from src.frontend.constantes import CARACTERES_ENTRADA_NUMERICA
from src.frontend.textos import MENSAJE_ENTRADA_NUMERICA
from src.frontend.componentes.carga_numerica import preparar_matriz_numerica
from src.frontend.componentes.captura_modelos import crear_entradas_nombres, crear_entradas_vector, llenar_entradas
from src.frontend.componentes.cuadricula_base import propiedades_celda_accesible, propiedades_vector_accesible
from src.frontend.componentes.portapapeles_matricial import filtrar_entrada_numerica, filtrar_matriz_numerica


@pytest.mark.parametrize('texto,esperado', [
    ('', ''), ('+-./', '+-./'), ('-3/7', '-3/7'), ('+0.25', '+0.25'),
    ('1e3', '13'), ('-2E-4', '-2-4'), ('uno 12 dos', '12'),
    ('１２٣−2\u00a0', '2'), ('1\U0001f600/2', '1/2'),
    ('<script>9</script>', '9/'), ('--1//2..++', '--1//2..++'),
    ('9' * 10000, '9' * 10000),
])
def test_filtro_conserva_solo_caracteres_ascii_sin_interpretar(texto, esperado):
    """El filtro retira letras y Unicode, conservando signos, límites y sintaxis incompleta."""
    assert filtrar_entrada_numerica(texto) == esperado


def test_filtro_matricial_conserva_huecos_forma_y_entrada_original():
    """Una celda eliminada conserva sus coordenadas y no desplaza las siguientes."""
    original = [['1', 'letras', '3'], [], ['-1/2', '0.2', '']]
    assert filtrar_matriz_numerica(original) == [['1', '', '3'], [], ['-1/2', '0.2', '']]
    assert original[0][1] == 'letras'


def test_configuracion_json_coincide_con_fuentes_python():
    """El cliente recibe el mismo alfabeto y aviso, antes de cargar el filtro."""
    bloque = re.search(r'<script id="scalaris-configuracion-numerica" type="application/json">(.*?)</script>',
                      tema._CABECERA_HTML)
    assert bloque is not None
    assert json.loads(bloque.group(1)) == {'caracteres': CARACTERES_ENTRADA_NUMERICA,
                                         'mensaje': MENSAJE_ENTRADA_NUMERICA}
    assert set(CARACTERES_ENTRADA_NUMERICA) == set('0123456789./-+')
    assert tema._CABECERA_HTML.index('scalaris-configuracion-numerica') < tema._CABECERA_HTML.index('/assets/js/entrada_numerica.js')


def test_propiedades_separan_celdas_y_texto_libre():
    """Las propiedades numéricas conservan coordenadas y admiten exclusión explícita."""
    assert 'data-solo-numerico="true"' in propiedades_celda_accesible(1, 2)
    assert 'data-solo-numerico="false"' in propiedades_celda_accesible(1, 2, solo_numerico=False)
    assert 'data-solo-numerico="true"' in propiedades_vector_accesible(1, 'fila', nombre_vector='u', identificador_panel='p')


def test_carga_matricial_avisa_una_vez_y_no_avisa_por_espacios_externos(monkeypatch):
    """Una carga sucia genera un único aviso y una carga válida conserva fracciones."""
    aviso = Mock()
    monkeypatch.setattr(ui, 'notify', aviso)
    assert preparar_matriz_numerica([['a1', '2b'], ['3c', '4d']]) == [['1', '2'], ['3', '4']]
    aviso.assert_called_once_with(MENSAJE_ENTRADA_NUMERICA, type='warning')
    aviso.reset_mock()
    assert preparar_matriz_numerica([[' -1/3 ', ' 0.25 ']]) == [['-1/3', '0.25']]
    aviso.assert_not_called()


def test_modelos_cargan_numeros_sin_modificar_nombres(monkeypatch):
    """Sectores y variables mantienen letras, espacios y tildes durante carga y edición."""
    monkeypatch.setattr(ui, 'notify', Mock())
    contenedor = ui.column()
    try:
        nombres = crear_entradas_nombres(contenedor, 2, 'Sector')
        llenar_entradas(nombres, ['Energía 2', 'Sector α'])
        assert [entrada.value for entrada in nombres] == ['Energía 2', 'Sector α']
        assert all(entrada._props['data-solo-numerico'] == 'false' for entrada in nombres)
        numeros = crear_entradas_vector(contenedor, 2, 'demanda')
        llenar_entradas(numeros, ['a1/2', '-3b'])
        assert [entrada.value for entrada in numeros] == ['1/2', '-3']
    finally:
        contenedor.delete()
