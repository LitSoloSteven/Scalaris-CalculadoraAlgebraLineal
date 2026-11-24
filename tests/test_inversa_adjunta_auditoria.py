"""Forma, presupuesto numérico y precisión de la entrada directa de adjunta."""
from fractions import Fraction
from unittest.mock import Mock

import pytest

from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa import inversa_adjunta
from src.backend.resolutores.operaciones_matrices.inversa.captura_inversa import (
    validar_y_parsear_matriz_cuadrada,
)
from src.backend.resolutores.operaciones_matrices.inversa.validacion_adjunta import (
    MAXIMO_BITS_DATOS_ADJUNTA,
)


def _exigir_rechazo_sin_calculo(monkeypatch, matriz):
    construir = Mock(side_effect=AssertionError("Una entrada rechazada no debe calcular menores."))
    monkeypatch.setattr(inversa_adjunta, "construir_adjunta", construir)
    resultado = inversa_adjunta.calcular_inversa_adjunta(matriz)
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert resultado["menores"] is resultado["adjunta"] is resultado["inversa"] is None
    assert resultado["traza"] == resultado["detalle_cofactores"] == resultado["comprobaciones"] == ()
    assert resultado["nodos_cofactores"] == 0
    construir.assert_not_called()
    return resultado


@pytest.mark.parametrize("datos", [None, 1, {}, (), [None], [[1, 2]], [[1], [2]]])
def test_estructura_alterada_devuelve_error_controlado(monkeypatch, datos):
    """El modelo mutable se valida de nuevo antes de acceder a sus filas o celdas."""
    matriz = Matriz(1, 1, [[1]])
    matriz.datos = datos
    _exigir_rechazo_sin_calculo(monkeypatch, matriz)


@pytest.mark.parametrize("dimension", [True, False, "1", None, 1.0])
def test_dimensiones_no_enteras_se_rechazan(monkeypatch, dimension):
    """Booleanos, flotantes y atributos inválidos no entran a rangos de cálculo."""
    matriz = Matriz(1, 1, [[1]])
    matriz.filas = matriz.columnas = dimension
    resultado = _exigir_rechazo_sin_calculo(monkeypatch, matriz)
    assert resultado["dimension"] == 0


@pytest.mark.parametrize("valor", [True, False, 0.5, float("nan"), float("inf"), "1/2", None])
def test_valores_residuales_se_rechazan_sin_conversion(monkeypatch, valor):
    """El motor no redondea ni normaliza celdas ajenas al contrato exacto."""
    matriz = Matriz(1, 1, [[1]])
    matriz.datos[0][0] = valor
    _exigir_rechazo_sin_calculo(monkeypatch, matriz)


@pytest.mark.parametrize("valor", [10 ** 5000, Fraction(1, 10 ** 5000)], ids=["entero", "fraccion"])
def test_racionales_grandes_se_rechazan_antes_de_la_traza(monkeypatch, valor):
    """La inspección de bits evita convertir números excesivos a cadenas."""
    resultado = _exigir_rechazo_sin_calculo(monkeypatch, Matriz(1, 1, [[valor]]))
    assert "presupuesto conjunto" in resultado["mensaje"]


def test_presupuesto_se_acumula_entre_todas_las_celdas(monkeypatch):
    """Cuatro celdas individualmente pequeñas pueden superar el presupuesto total."""
    valor = 1 << (MAXIMO_BITS_DATOS_ADJUNTA // 4)
    resultado = _exigir_rechazo_sin_calculo(monkeypatch, Matriz(2, 2, [[valor, valor], [valor, valor]]))
    assert "presupuesto conjunto" in resultado["mensaje"]


def test_borde_del_presupuesto_conserva_valor_e_inversa():
    """El valor situado exactamente en el límite se calcula sin truncarlo."""
    valor = 1 << (MAXIMO_BITS_DATOS_ADJUNTA - 2)
    resultado = inversa_adjunta.calcular_inversa_adjunta(Matriz(1, 1, [[valor]]))
    assert resultado["estado"] == "EXITO"
    assert resultado["determinante"] == valor
    assert resultado["inversa"].datos == [[Fraction(1, valor)]]
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])


def test_un_bit_sobre_el_presupuesto_se_rechaza(monkeypatch):
    """El primer valor que excede la cota se rechaza sin construir menores."""
    valor = 1 << (MAXIMO_BITS_DATOS_ADJUNTA - 1)
    _exigir_rechazo_sin_calculo(monkeypatch, Matriz(1, 1, [[valor]]))


def test_matriz_grande_casi_singular_conserva_determinante_uno():
    """La cancelación exacta cerca de la cota no redondea el determinante ni la inversa."""
    escala = 1 << (MAXIMO_BITS_DATOS_ADJUNTA // 4 - 4)
    matriz = Matriz(2, 2, [[escala, escala - 1], [escala + 1, escala]])
    resultado = inversa_adjunta.calcular_inversa_adjunta(matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["determinante"] == 1
    assert resultado["inversa"].datos == [[escala, 1 - escala], [-escala - 1, escala]]
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])


@pytest.mark.parametrize("literal", [
    "0.12345678901234567890123456789",
    "0." + "0" * (LONGITUD_MAXIMA_CADENA_NUMERO - 3) + "1",
])
def test_captura_decimal_conserva_el_valor_hasta_la_adjunta(literal):
    """El literal admitido en captura mantiene todas sus cifras en el motor nuevo."""
    matriz, dimension, error = validar_y_parsear_matriz_cuadrada({"dimension": 1, "datos": [[literal]]})
    assert error is None and dimension == 1
    resultado = inversa_adjunta.calcular_inversa_adjunta(matriz)
    assert resultado["estado"] == "EXITO"
    assert resultado["determinante"] == Fraction(literal)
    assert resultado["inversa"].datos == [[1 / Fraction(literal)]]
