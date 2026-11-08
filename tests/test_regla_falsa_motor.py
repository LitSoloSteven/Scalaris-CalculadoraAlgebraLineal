"""Motor de regla falsa: estados, cierres y traza."""
import math

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.regla_falsa import regla_falsa


def _entrada(expresion="x**2-2", a=1, b=2, tol=1e-6, limite=100):
    return EntradaReglaFalsa(
        expresion=expresion,
        extremo_izquierdo=a,
        extremo_derecho=b,
        tolerancia=tol,
        limite_iteraciones=limite,
    )


def test_convergencia_por_residuo():
    """x^2-2 en [1,2] converge por residuo."""
    resultado = regla_falsa(_entrada())
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "tolerancia_residuo"
    assert abs(resultado.aproximacion - math.sqrt(2)) < 1e-4
    assert resultado.residuo is not None
    assert resultado.residuo < 1e-6
    assert resultado.iteraciones_totales == len(resultado.iteraciones)


def test_raiz_en_extremo_izquierdo():
    """x-1 en [1,2] encuentra raiz en extremo."""
    resultado = regla_falsa(_entrada("x-1", 1, 2))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 1.0
    assert resultado.residuo == 0.0
    assert resultado.iteraciones_totales == 0


def test_raiz_en_extremo_derecho():
    """x-1 en [0,1] encuentra raiz en extremo derecho."""
    resultado = regla_falsa(_entrada("x-1", 0, 1))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 1.0


def test_sin_cambio_de_signo():
    """x^2+1 en [-1,1] no tiene cambio de signo."""
    resultado = regla_falsa(_entrada("x**2+1", -1, 1))
    assert resultado.estado == "SIN_CAMBIO_DE_SIGNO"
    assert resultado.motivo_parada == "sin_cambio_de_signo"
    assert resultado.aproximacion is None
    assert resultado.iteraciones == ()


def test_limite_iteraciones():
    """x^2-2 en [1,2] con limite 1 no converge."""
    resultado = regla_falsa(_entrada(tol=1e-12, limite=1))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.motivo_parada == "limite_iteraciones"
    assert len(resultado.iteraciones) == 1
    assert abs(resultado.iteraciones[0].aproximacion - 4/3) < 1e-9


def test_dominio_invalido():
    """sqrt(x) en [-1,1] falla por dominio."""
    resultado = regla_falsa(_entrada("sqrt(x)", -1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"
    assert resultado.contexto_fallo is not None


def test_singularidad_detectada():
    """1/x en [-1,1] detecta singularidad."""
    resultado = regla_falsa(_entrada("1/x", -1, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"


def test_sintaxis_invalida():
    """sin() no es compilable."""
    resultado = regla_falsa(_entrada("sin()", 0, 1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EXPRESION_INVALIDA"
    assert resultado.motivo_parada == "expresion_invalida"


def test_entrada_invalida():
    """Una entrada que no es EntradaReglaFalsa falla."""
    resultado = regla_falsa({"expresion": "x"})
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"


def test_estancamiento_por_redondeo():
    """x^2-2 en un intervalo diminuto no puede avanzar."""
    raiz = math.sqrt(2)
    a = math.nextafter(raiz, -math.inf)
    b = raiz
    resultado = regla_falsa(_entrada(a=a, b=b, tol=1e-30))
    assert resultado.estado == "ESTANCAMIENTO"
    assert resultado.motivo_parada == "estancamiento_numerico"


def test_secante_exacta():
    """x-1 en [0,2] encuentra la raiz en la primera iteracion."""
    resultado = regla_falsa(_entrada("x-1", 0, 2))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_aproximacion"
    assert abs(resultado.aproximacion - 1.0) < 1e-9


def test_intervalo_invertido():
    """x^2-2 en [2,1] se normaliza."""
    resultado = regla_falsa(_entrada("x**2-2", 2, 1))
    assert resultado.estado == "EXITO"
    assert resultado.entrada.intervalo_invertido is True
    assert len(resultado.advertencias) > 0


def test_unidad_angular():
    """sin(x)-0.5 en grados converge a 30."""
    resultado = regla_falsa(EntradaReglaFalsa(
        expresion="sin(x)-0.5",
        extremo_izquierdo=0,
        extremo_derecho=90,
        tolerancia=1e-6,
        limite_iteraciones=100,
        unidad_angular="grados",
    ))
    assert resultado.estado == "EXITO"
    assert abs(resultado.aproximacion - 30.0) < 1e-3
    
def test_intervalo_final_con_limite():
    """x^2-2 en [1,2], tol 1e-12, limite 1: intervalo_final debe ser (4/3, 2)."""
    resultado = regla_falsa(_entrada(tol=1e-12, limite=1))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.intervalo_final[0] == pytest.approx(4 / 3)
    assert resultado.intervalo_final[1] == 2.0


def test_intervalo_final_en_secante_exacta():
    """x-1 en [0,2]: intervalo_final debe colapsar a (1,1)."""
    resultado = regla_falsa(_entrada("x-1", 0, 2))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_aproximacion"
    assert resultado.intervalo_final == (1.0, 1.0)


def test_estancamiento_con_tolerancia_cumplida_es_exito():
    """Si f(c) en el extremo cacheado ya cumple la tolerancia, el estado es EXITO."""
    raiz = math.sqrt(2)
    a = math.nextafter(raiz, -math.inf)
    b = raiz
    resultado = regla_falsa(_entrada(a=a, b=b, tol=1e-10))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "tolerancia_residuo"


def test_estancamiento_conserva_intervalo_y_accion():
    """El estancamiento real mantiene el intervalo, la accion y el residuo finito."""
    raiz = math.sqrt(2)
    a = math.nextafter(raiz, -math.inf)
    b = raiz
    resultado = regla_falsa(_entrada(a=a, b=b, tol=1e-30))
    assert resultado.estado == "ESTANCAMIENTO"
    assert resultado.motivo_parada == "estancamiento_numerico"
    ultima = resultado.iteraciones[-1]
    assert ultima.accion == "sin_cambio"
    assert ultima.intervalo_siguiente == resultado.intervalo_final
    assert math.isfinite(ultima.residuo)
    
def test_ambos_extremos_cero_advierte_y_elige_a():
    """x*(x-1) en [0,1]: ambos extremos cero; aproximacion a=0 y aviso de no unicidad."""
    resultado = regla_falsa(_entrada("x*(x-1)", 0, 1))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 0.0
    assert any("ambos extremos" in aviso.lower() for aviso in resultado.advertencias)


def test_cero_extremo_con_restriccion_advierte():
    """(x-1)/(x-2) en [1,3]: raiz en extremo con restriccion interior; advertencia presente."""
    resultado = regla_falsa(_entrada("(x-1)/(x-2)", 1, 3))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 1.0
    assert any("anula" in aviso.lower() or "cero" in aviso.lower()
               for aviso in resultado.advertencias)


def test_intervalo_invertido_no_duplica_advertencia_en_raiz_extremo():
    """x-1 en [1,0]: se normaliza a [0,1], hay cero en el extremo 1 y una sola advertencia."""
    resultado = regla_falsa(_entrada("x-1", 1, 0))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 1.0
    assert len(resultado.advertencias) == 1
    assert "intercambiaron" in resultado.advertencias[0].lower()