"""Controles de auxiliares, límites del cotejo y preservación de cada parametrización."""
import ast

import pytest

from tests.comun_conciliacion_ast import funciones_prueba, firma_ast
from tests.comun_conciliacion_flujo import indexar_modulos, controles_efectivos
from tests.comun_conciliacion_comparacion import proponer_equivalencias, predicado_control
from tests.comun_conciliacion_parametros import parametrizaciones_literales
from tests.comun_entradas import copiar_entrada_prueba
from tests.comun_conciliacion import contexto_preparacion, conciliar_fuentes
from tests.comun_conciliacion_informe import emparejar_controles


def test_cada_invocacion_del_auxiliar_conserva_su_control_y_valor():
    """Dos llamadas a la misma función generan dos controles con argumentos diferentes."""
    fuentes = {'tests/test_muestra.py': 'def verificar(dato):\n assert dato > 0\ndef test_muestra():\n verificar(1)\n verificar(2)'}
    caso = next(iter(funciones_prueba(fuentes).values()))
    controles = controles_efectivos(caso, 'tests/test_muestra.py', indexar_modulos(fuentes))
    assert [ast.unparse(control['nodo']) for control in controles] == ['assert 1 > 0', 'assert 2 > 0']


def test_auxiliar_importado_conserva_valores_por_defecto():
    """La preparación explícita y la predeterminada quedan ligadas a cada invocación."""
    fuentes = {'tests/comun_muestra.py': 'def verificar(dato=7, *, valido=True):\n assert dato == 7\n assert valido is True',
               'tests/test_muestra.py': 'from tests.comun_muestra import verificar\ndef test_muestra():\n verificar()'}
    caso = next(iter(funciones_prueba(fuentes).values()))
    controles = controles_efectivos(caso, 'tests/test_muestra.py', indexar_modulos(fuentes))
    assert [ast.unparse(control['nodo']) for control in controles] == ['assert 7 == 7', 'assert True is True']


def test_variable_local_y_metodo_externo_tienen_mapas_distintos():
    """Traducir una variable no cambia el método externo homónimo de un receptor."""
    antes = ast.parse('assert inicio < coincidencia.start()').body[0]
    despues = ast.parse('assert comienzo < coincidencia.start()').body[0]
    nombres, literales, conflictos = proponer_equivalencias(antes, despues)
    assert not conflictos and not literales
    assert firma_ast(predicado_control(antes), nombres) == firma_ast(predicado_control(despues))
    assert nombres['Name:inicio'] == 'comienzo'
    assert nombres['Attribute:start'] == 'start'


def test_parametrizacion_conserva_filas_repetidas_y_producto_de_tablas():
    """La multiplicidad y las combinaciones no se pierden al comparar decoradores."""
    texto = "@pytest.mark.parametrize('dato', [1, 1])\n@pytest.mark.parametrize('valido', [True, False])\ndef test_muestra(dato, valido):\n assert dato"
    caso = ast.parse(texto).body[0]
    parametros = parametrizaciones_literales(caso)
    assert len(parametros) == 4
    assert [ast.literal_eval(enlaces['dato']) for enlaces in parametros] == [1, 1, 1, 1]


@pytest.mark.parametrize('decorador', [
    "pytest.mark.parametrize('dato', tabla)",
    "pytest.mark.parametrize('dato', [1], indirect=True)",
    "pytest.mark.parametrize('primero,segundo', [1])",
])
def test_parametros_no_resueltos_no_se_acreditan_automaticamente(decorador):
    """El cotejo exige revisión explícita al encontrar datos calculados o fixtures indirectas."""
    caso = ast.parse('@' + decorador + '\ndef test_muestra():\n assert True').body[0]
    with pytest.raises(ValueError):
        parametrizaciones_literales(caso)


def test_entradas_compartidas_no_transmiten_mutaciones_a_otros_casos():
    """La edición de una matriz anidada no altera la siguiente captura ni el catálogo."""
    primera = copiar_entrada_prueba('sistema_unico')
    primera['matriz_a'][0][0] = '999'
    segunda = copiar_entrada_prueba('sistema_unico')
    assert segunda['matriz_a'][0][0] == '2'
    assert primera['matriz_a'] is not segunda['matriz_a']


def test_mapa_no_colapsa_receptores_distintos_en_una_tautologia():
    """Dos variables originales distintas no pueden normalizarse como una sola."""
    antes = ast.parse('assert primero.estado == segundo.estado').body[0]
    despues = ast.parse('assert resultado.estado == resultado.estado').body[0]
    nombres, literales, conflictos = proponer_equivalencias(antes, despues)
    assert any(conflicto[0] == 'colision' for conflicto in conflictos)


def test_contexto_detecta_cambio_en_preparacion_importada_y_conftest():
    """Una limpieza importada distinta altera el contexto aunque el caso sea idéntico."""
    caso_texto = 'from tests.comun_muestra import limpiar\ndef test_muestra():\n assert 1 == 1'
    originales = {'tests/test_muestra.py': caso_texto,
                  'tests/comun_muestra.py': '@pytest.fixture(autouse=True)\ndef limpiar():\n configurar(1)',
                  'tests/conftest.py': '@pytest.fixture\ndef entorno():\n configurar(3)'}
    modificados = {**originales, 'tests/comun_muestra.py': originales['tests/comun_muestra.py'].replace('configurar(1)', 'configurar(2)')}
    antes, despues = indexar_modulos(originales), indexar_modulos(modificados)
    caso = next(iter(funciones_prueba(originales).values()))
    primero = contexto_preparacion(caso, antes['tests/test_muestra.py'], antes)
    segundo = contexto_preparacion(caso, despues['tests/test_muestra.py'], despues)
    assert primero != segundo
    assert 'tests/conftest.py' in primero['modulos_preparacion']
    assert 'configurar(1)' in primero['modulos_preparacion']['tests/comun_muestra.py']['cuerpo']


def test_auxiliar_inaccesible_conserva_la_condicion_que_impide_ejecutarlo():
    """Un control bajo una condición falsa requiere revisar su alcance de ejecución."""
    base = {'tests/test_muestra.py': 'def verificar(dato):\n assert dato > 0\ndef test_muestra():\n verificar(1)'}
    cambiada = {'tests/test_muestra.py': base['tests/test_muestra.py'].replace('assert dato > 0', 'if False:\n  assert dato > 0')}
    anteriores, actuales = indexar_modulos(base), indexar_modulos(cambiada)
    caso_antes = next(iter(funciones_prueba(base).values()))
    caso_actual = next(iter(funciones_prueba(cambiada).values()))
    controles_anteriores = controles_efectivos(caso_antes, 'tests/test_muestra.py', anteriores)
    controles_actuales = controles_efectivos(caso_actual, 'tests/test_muestra.py', actuales)
    fila = emparejar_controles(controles_anteriores, controles_actuales, {})[0]
    assert any(conflicto[0] == 'alcance_pendiente' for conflicto in fila['conflictos'])
    assert controles_actuales[0]['alcance'][0]['expresion'] == 'False'


def test_el_cotejo_no_reinterpreta_temporales_tras_mutar_su_origen():
    """El control conserva la variable capturada en vez de volver a leer el subíndice."""
    fuentes = {'tests/test_muestra.py': 'def test_muestra():\n primero = datos[0]\n datos[0] = 2\n assert primero == 1'}
    mapa = [{'origen': ['tests/test_muestra.py', 'test_muestra'],
             'sucesores': [['tests/test_muestra.py', 'test_muestra']]}]
    fila = conciliar_fuentes(fuentes, fuentes, mapa, {})[0]['controles'][0]
    assert fila['antes'] == 'assert primero == 1'
    assert fila['despues'] == fila['antes']


def test_mapa_incompleto_o_repetido_no_oculta_casos_originales():
    """El inventario exige cubrir cada función original exactamente una vez."""
    fuentes = {'tests/test_muestra.py': 'def test_primero():\n assert True\ndef test_segundo():\n assert True'}
    mapa = [{'origen': ['tests/test_muestra.py', 'test_primero'],
             'sucesores': [['tests/test_muestra.py', 'test_primero']]}]
    with pytest.raises(ValueError):
        conciliar_fuentes(fuentes, fuentes, mapa, {})
    with pytest.raises(ValueError):
        conciliar_fuentes(fuentes, fuentes, [*mapa, *mapa], {})


@pytest.mark.parametrize('antes,despues', [
    ('try:\n  assert dato\n except ValueError:\n  pass',
     'try:\n  assert dato\n except TypeError:\n  pass'),
    ('try:\n  pass\n finally:\n  assert dato',
     'try:\n  assert dato\n finally:\n  pass'),
    ('with primero():\n  assert dato', 'with segundo():\n  assert dato'),
])
def test_excepciones_ramas_y_gestores_cambiados_exigen_revision(antes, despues):
    """Los controles aislados no acreditan alcances con excepciones o gestores distintos."""
    fuentes = {'tests/test_muestra.py': 'def test_muestra():\n ' + antes}
    cambiadas = {'tests/test_muestra.py': 'def test_muestra():\n ' + despues}
    caso_antes = next(iter(funciones_prueba(fuentes).values()))
    caso_despues = next(iter(funciones_prueba(cambiadas).values()))
    controles_anteriores = controles_efectivos(caso_antes, 'tests/test_muestra.py', indexar_modulos(fuentes))
    controles_actuales = controles_efectivos(caso_despues, 'tests/test_muestra.py', indexar_modulos(cambiadas))
    fila = emparejar_controles(controles_anteriores, controles_actuales, {})[0]
    assert any(conflicto[0] == 'alcance_pendiente' for conflicto in fila['conflictos'])


def test_distancia_no_desplaza_un_predicado_nominal_con_literales_exactos():
    """La posición desempata candidatos sin favorecer cien controles de otros valores."""
    anterior = {'ruta': 'antes.py', 'linea': 1, 'nodo': ast.parse("assert resultado['status'] == 'UNIQUE'").body[0]}
    actual = {'ruta': 'actual.py', 'linea': 1, 'nodo': ast.parse("assert resultado['estado'] == 'UNICA'").body[0]}
    distractor = {**actual, 'nodo': ast.parse("assert resultado['estado'] == 'ERROR'").body[0]}
    filas = emparejar_controles([anterior], [*[distractor] * 500, actual], {'status': 'estado', 'UNIQUE': 'UNICA'})
    assert filas[0]['despues'] == "assert resultado['estado'] == 'UNICA'"


def test_controles_del_lector_pasado_como_argumento_conservan_su_modulo():
    """El lector invocado por un auxiliar resuelve el cuerpo original de la función recibida."""
    fuentes = {'tests/comun_muestra.py': 'def comprobar(lector):\n lector(1)',
               'tests/test_muestra.py': 'from tests.comun_muestra import comprobar\ndef leer(dato):\n assert dato == 1\ndef test_muestra():\n comprobar(leer)'}
    caso = next(iter(funciones_prueba(fuentes).values()))
    controles = controles_efectivos(caso, 'tests/test_muestra.py', indexar_modulos(fuentes))
    assert [ast.unparse(control['nodo']) for control in controles] == ['assert 1 == 1']
    assert controles[0]['ruta'] == 'tests/test_muestra.py'


def test_un_candidato_ambiguo_no_consume_el_sucesor_exacto_de_otro_control():
    """El emparejamiento reserva primero los predicados con mejor correspondencia nominal."""
    controles = [{'ruta': 'muestra.py', 'linea': i, 'nodo': ast.parse(texto).body[0]}
                 for i, texto in enumerate(["assert 'ambiguo' in datos", "assert 'exacto' in datos",
                                            "assert 'exacto' in datos", "assert 'otro' in datos"])]
    filas = emparejar_controles(controles[:2], controles[2:], {})
    assert filas[1]['despues'] == "assert 'exacto' in datos"
