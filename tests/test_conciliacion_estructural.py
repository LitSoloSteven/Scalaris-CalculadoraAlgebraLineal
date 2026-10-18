"""Regresiones del cotejo nominal, multiplicidad de aserciones y preparación."""
import ast

from tests.comun_conciliacion_ast import (
    firma_ast, funciones_prueba, multiconjunto_aserciones, preparacion_caso,
)


def _caso(texto):
    return funciones_prueba({'tests/test_muestra.py': texto}).popitem()[1]


def test_multiconjunto_conserva_aserciones_repetidas():
    """Dos controles iguales no se reducen a un único control."""
    doble = _caso('def test_muestra():\n assert dato == 1\n assert dato == 1')
    unico = _caso('def test_muestra():\n assert dato == 1')
    assert sum(multiconjunto_aserciones(doble).values()) == 2
    assert multiconjunto_aserciones(doble) != multiconjunto_aserciones(unico)


def test_mismos_conteos_no_ocultan_operadores_o_valores_distintos():
    """Cambiar el umbral o su relación sigue alterando la huella de la aserción."""
    original = _caso('def test_muestra():\n assert dato >= 4.5')
    umbral = _caso('def test_muestra():\n assert dato >= 3.0')
    operador = _caso('def test_muestra():\n assert dato <= 4.5')
    assert multiconjunto_aserciones(original) != multiconjunto_aserciones(umbral)
    assert multiconjunto_aserciones(original) != multiconjunto_aserciones(operador)


def test_mapa_nominal_conserva_relaciones_entre_variables():
    """La traducción explícita preserva receptores diferentes y la misma constante."""
    original = _caso('def test_muestra():\n assert primero.estado == segundo.estado')
    traducido = _caso('def test_muestra():\n assert izquierda.estado == derecha.estado')
    debilitado = _caso('def test_muestra():\n assert izquierda.estado == izquierda.estado')
    mapa = {'primero': 'izquierda', 'segundo': 'derecha'}
    esperado = multiconjunto_aserciones(original, mapa)
    assert esperado == multiconjunto_aserciones(traducido)
    assert esperado != multiconjunto_aserciones(debilitado)


def test_preparacion_distinta_no_se_confunde_con_asercion_igual():
    """La misma aserción no acredita que se haya utilizado la misma entrada."""
    original = _caso('def test_muestra():\n dato = resolver([1, 2])\n assert dato == 3')
    distinta = _caso('def test_muestra():\n dato = resolver([3])\n assert dato == 3')
    assert multiconjunto_aserciones(original) == multiconjunto_aserciones(distinta)
    assert firma_ast(preparacion_caso(original)) != firma_ast(preparacion_caso(distinta))


def test_nombres_repetidos_en_clases_no_sobrescriben_casos():
    """Los métodos homónimos de dos clases conservan su identidad independiente."""
    texto = ('class TestPrimera:\n def test_resultado(self):\n  assert 1\n'
             'class TestSegunda:\n def test_resultado(self):\n  assert 2')
    casos = funciones_prueba({'tests/test_muestra.py': texto})
    assert len(casos) == 2
    assert {clave[1] for clave in casos} == {'TestPrimera.test_resultado', 'TestSegunda.test_resultado'}
