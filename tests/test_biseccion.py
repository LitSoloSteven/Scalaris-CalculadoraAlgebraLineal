"""Pruebas unitarias para el motor de bisección y el contrato."""
import pytest
from src.backend.resolutores.raices.contrato_biseccion import (
    validar_entrada, validar_precision, EntradaBiseccion
)
from src.backend.resolutores.raices.biseccion import biseccion


def crear_entrada(expresion, a, b, d, limite=100):
    """Fábrica auxiliar para construir entradas válidas en los tests."""
    return EntradaBiseccion(expresion=expresion, a=a, b=b, d=d, limite_iteraciones=limite)


def test_convergencia_clasica():
    """x^2 - 2 en [1, 2] converge a sqrt(2)."""
    resultado = biseccion(crear_entrada("x**2 - 2", 1.0, 2.0, 4))
    assert resultado.estado == "EXITO"
    assert abs(resultado.aproximacion - 1.41421356) < 1e-4
    assert resultado.motivo_parada == "ancho_menor_que_E"


def test_funcion_orden_alto():
    """x^10 - 1 en [0, 1.3] converge a 1.0."""
    resultado = biseccion(crear_entrada("x**10 - 1", 0.0, 1.3, 4))
    assert resultado.estado == "EXITO"
    assert abs(resultado.aproximacion - 1.0) < 1e-4


def test_raiz_en_extremo_a():
    """x - 1 en [1, 2] tiene la raíz exacta en el extremo a."""
    resultado = biseccion(crear_entrada("x - 1", 1.0, 2.0, 4))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_exacta"
    assert resultado.aproximacion == 1.0


def test_raiz_en_punto_medio():
    """x - 0.5 en [0, 1] tiene la raíz exacta en la primera c."""
    resultado = biseccion(crear_entrada("x - 0.5", 0.0, 1.0, 4))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_exacta"
    assert resultado.aproximacion == 0.5


def test_sin_cambio_de_signo():
    """x^2 + 1 en [-1, 1] no tiene raíz real en el intervalo."""
    resultado = biseccion(crear_entrada("x**2 + 1", -1.0, 1.0, 4))
    assert resultado.estado == "SIN_CAMBIO_DE_SIGNO"
    assert len(resultado.iteraciones) == 0
    assert resultado.aproximacion is None


def test_singularidad_en_intervalo():
    """1/x en [-1, 1] falla al evaluar en c=0."""
    resultado = biseccion(crear_entrada("1/x", -1.0, 1.0, 4))
    assert resultado.estado == "ERROR"
    assert "división por cero" in resultado.mensaje.lower()


def test_limite_de_iteraciones():
    """Agota el límite sin alcanzar la precisión pedida."""
    resultado = biseccion(crear_entrada("x**2 - 2", 1.0, 2.0, 10, limite=2))
    assert resultado.estado == "PRECISION_NO_ALCANZADA"
    assert len(resultado.iteraciones) == 2
    assert resultado.motivo_parada == "limite_iteraciones"


def test_validacion_precision():
    """d debe ser entero, no booleano y estar entre 0 y 15."""
    for valor in [-1, 1.5, 16, True]:
        with pytest.raises(ValueError):
            validar_precision(valor)


def test_validacion_entrada_intervalo_invalido():
    """a debe ser estrictamente menor que b."""
    with pytest.raises(ValueError):
        validar_entrada({"expresion": "x", "a": 2.0, "b": 1.0, "d": 4})


def test_error_relativo():
    """La primera iteración es No aplica, la segunda lleva porcentaje."""
    resultado = biseccion(crear_entrada("x**2 - 2", 1.0, 2.0, 4))
    assert resultado.iteraciones[0].error_relativo == "No aplica"
    assert "%" in resultado.iteraciones[1].error_relativo


def test_primeras_filas_libro():
    """Comprueba las tres primeras c del ejemplo del libro."""
    polinomio = "x**4 - 5*x**3 + 0.5*x**2 - 11*x + 10"
    resultado = biseccion(crear_entrada(polinomio, 0.6, 1.0, 4))
    assert resultado.iteraciones[0].c == pytest.approx(0.8)
    assert resultado.iteraciones[1].c == pytest.approx(0.7)
    assert resultado.iteraciones[2].c == pytest.approx(0.75)