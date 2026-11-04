"""Fronteras de recursos, números extremos y generación de posiciones por índice."""
import math
from unittest.mock import patch

import pytest

from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.limites_exploracion import (
    MAXIMO_EVALUACIONES_EXPLORACION, MAXIMO_REGISTROS_EXPLORACION,
)
from src.backend.resolutores.raices.muestreo_intervalos import generar_posiciones


def test_presupuesto_exacto_de_evaluaciones():
    """La frontera permite exactamente el máximo y contabiliza cada evaluación."""
    entrada = EntradaExploracion("x+1", 0, MAXIMO_EVALUACIONES_EXPLORACION - 1, 1)
    assert explorar_intervalos(entrada).evaluaciones == MAXIMO_EVALUACIONES_EXPLORACION


def test_presupuesto_rechazado_antes_de_compilar_o_evaluar():
    """Un rango abusivo falla antes del trabajo matemático y sin reservar una malla enorme."""
    entrada = EntradaExploracion("x", -1e308, 1e308, math.ulp(0.0))
    with patch("src.backend.resolutores.raices.exploracion_intervalos.compilar") as compilar:
        with pytest.raises(ValueError, match="demasiadas evaluaciones"):
            explorar_intervalos(entrada)
        compilar.assert_not_called()


def test_una_evaluacion_sobre_el_maximo_se_rechaza():
    """No recorta ni ajusta silenciosamente el paso solicitado."""
    with pytest.raises(ValueError, match="demasiadas evaluaciones"):
        generar_posiciones(EntradaExploracion("x", 0, MAXIMO_EVALUACIONES_EXPLORACION, 1))


def test_registros_en_frontera_y_exceso():
    """Ceros consecutivos se conservan hasta la frontera; el exceso es un error explícito."""
    limite = MAXIMO_REGISTROS_EXPLORACION
    resultado = explorar_intervalos(EntradaExploracion("0", 0, limite - 1, 1))
    assert len(resultado.candidatos) == limite
    with pytest.raises(ValueError, match="demasiados registros"):
        explorar_intervalos(EntradaExploracion("0", 0, limite, 1))


@pytest.mark.parametrize("paso,esperadas", [(2, (0, 1)), (.5, (0, .5, 1)), (.3, (0, .3, .6, .8999999999999999, 1))])
def test_extremo_final_unico_incluido(paso, esperadas):
    """Incluye x_max exactamente una vez aun cuando el paso no divide el rango."""
    posiciones = generar_posiciones(EntradaExploracion("x", 0, 1, paso))
    assert posiciones == esperadas
    assert posiciones.count(1) == 1


def test_malla_con_ancho_no_representable_sin_desbordar():
    """Fraction evita desbordar al restar extremos o multiplicar índice y paso."""
    posiciones = generar_posiciones(EntradaExploracion("x", -1e308, 1e308, 1e308))
    assert posiciones == (-1e308, 0, 1e308)


def test_subnormales_representables():
    """Un paso subnormal representable no se convierte artificialmente en cero."""
    paso = math.ulp(0.0)
    assert generar_posiciones(EntradaExploracion("x", 0, paso * 2, paso)) == (0, paso, paso * 2)


def test_paso_sin_avance_por_redondeo():
    """Detecta muestras repetidas incluso si el número de posiciones cabe en el límite."""
    with pytest.raises(ValueError, match="no permite avanzar"):
        generar_posiciones(EntradaExploracion("x", 1e16, 1e16 + 4, .5))


@pytest.mark.parametrize("campo", ["x_min", "x_max", "paso"])
@pytest.mark.parametrize("valor", [None, "", "1", True, float("nan"), float("inf"), -float("inf"), 10**1000])
def test_numeros_invalidos_sin_coercion(campo, valor):
    """Rechaza vacíos, booleanos, texto, no finitos y enteros fuera de representación."""
    datos = dict(expresion="x", x_min=0, x_max=1, paso=.1)
    datos[campo] = valor
    with pytest.raises(ValueError):
        explorar_intervalos(EntradaExploracion(**datos))


@pytest.mark.parametrize("minimo,maximo,paso", [(1, 1, .1), (2, 1, .1), (0, 1, 0), (0, 1, -1)])
def test_rango_y_paso_estrictos(minimo, maximo, paso):
    """No invierte rangos ni sustituye pasos inválidos en la exploración."""
    with pytest.raises(ValueError):
        explorar_intervalos(EntradaExploracion("x", minimo, maximo, paso))


@pytest.mark.parametrize("expresion", [None, "", "  ", "x" * 513, 123])
def test_expresion_invalida(expresion):
    """Valida tipo, vacío y longitud antes de compilar."""
    with pytest.raises(ValueError):
        explorar_intervalos(EntradaExploracion(expresion, 0, 1, .1))


def test_forma_invalida():
    """La API exige su contrato de entrada sin interpretar cargas arbitrarias."""
    with pytest.raises(ValueError):
        explorar_intervalos({})
