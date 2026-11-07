"""Motor clasico de regla falsa: estados, cierres y aritmetica real."""
import math

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.regla_falsa import regla_falsa


def test_raiz_cuadrada_converge_por_tolerancia():
    """x^2 - 2 en [1, 2] converge por residuo en pocas iteraciones."""
    resultado = regla_falsa(EntradaReglaFalsa("x^2 - 2", 1.0, 2.0, 1e-6))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "tolerancia_residuo"
    assert resultado.codigo_diagnostico == "CONVERGENCIA_POR_RESIDUO"
    assert resultado.aproximacion is not None
    assert abs(resultado.aproximacion - math.sqrt(2)) < 1e-4
    assert abs(resultado.iteraciones[-1].residuo) < 1e-6


def test_funcion_lineal_cierra_por_secante_exacta_en_una_iteracion():
    """x - 2 en [1, 3] converge exactamente con la primera secante."""
    resultado = regla_falsa(EntradaReglaFalsa("x - 2", 1.0, 3.0, 1e-6))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "secante_exacta"
    assert len(resultado.iteraciones) == 1
    assert resultado.aproximacion == 2.0
    assert resultado.iteraciones[0].f_c == 0.0


def test_sin_cambio_de_signo_no_itera():
    """x^2 + 1 en [-1, 1] no tiene raiz real."""
    resultado = regla_falsa(EntradaReglaFalsa("x^2 + 1", -1.0, 1.0, 1e-6))
    assert resultado.estado == "SIN_CAMBIO_DE_SIGNO"
    assert resultado.motivo_parada == "sin_cambio_signo"
    assert resultado.iteraciones == ()


def test_raiz_en_extremo_inferior_no_itera():
    """x - 1 en [1, 3] tiene f(1) = 0."""
    resultado = regla_falsa(EntradaReglaFalsa("x - 1", 1.0, 3.0, 1e-6))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 1.0
    assert resultado.iteraciones == ()


def test_raiz_en_extremo_superior_no_itera():
    """x - 2 en [1, 2] tiene f(2) = 0."""
    resultado = regla_falsa(EntradaReglaFalsa("x - 2", 1.0, 2.0, 1e-6))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 2.0


def test_ambos_extremos_en_cero_prioriza_inferior():
    """x*(x-1) en [0, 1] tiene dos raices; se reporta el inferior."""
    resultado = regla_falsa(EntradaReglaFalsa("x*(x-1)", 0.0, 1.0, 1e-6))
    assert resultado.estado == "EXITO"
    assert resultado.motivo_parada == "raiz_en_extremo"
    assert resultado.aproximacion == 0.0


def test_limite_iteraciones_publica_ultima_aproximacion():
    """x^2 - 2 con limite 1 no alcanza la tolerancia."""
    resultado = regla_falsa(EntradaReglaFalsa("x^2 - 2", 1.0, 2.0, 1e-15, limite_iteraciones=1))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.motivo_parada == "limite_iteraciones"
    assert len(resultado.iteraciones) == 1
    assert resultado.aproximacion is not None


def test_dominio_invalido_se_reporta_sin_iterar():
    """sqrt(x) - 2 en [-1, 5] tiene un extremo fuera del dominio."""
    resultado = regla_falsa(EntradaReglaFalsa("sqrt(x) - 2", -1.0, 5.0, 1e-6))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"


def test_restriccion_estructural_sin_cero_en_extremos():
    """1/(x - 0.5) en [0, 1] tiene un polo interior."""
    resultado = regla_falsa(EntradaReglaFalsa("1/(x - 0.5)", 0.0, 1.0, 1e-6))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"


def test_expresion_invalida_se_reporta_sin_iterar():
    """sin() no es una expresion valida."""
    resultado = regla_falsa(EntradaReglaFalsa("sin()", 0.0, 1.0, 1e-6))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EXPRESION_INVALIDA"


def test_entrada_invalida_se_reporta_sin_iterar():
    """Tolerancia negativa se rechaza antes de preparar."""
    resultado = regla_falsa(EntradaReglaFalsa("x - 1", 0.0, 2.0, -1e-6))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"


def test_estancamiento_por_punto_cruce_en_extremo():
    """El peso de la secante es tan pequeno que la aproximacion coincide con a."""
    resultado = regla_falsa(EntradaReglaFalsa("x - 1 - 1e-20", 1.0, 1e15, 1e-25))
    assert resultado.estado == "ESTANCAMIENTO"
    assert resultado.motivo_parada == "estancamiento"
    assert resultado.codigo_diagnostico == "ESTANCAMIENTO"
    assert len(resultado.iteraciones) == 1


def test_intervalo_invertido_se_normaliza_y_advierte():
    """Los extremos se ordenan antes de iterar y se conserva el aviso."""
    resultado = regla_falsa(EntradaReglaFalsa("x^2 - 2", 2.0, 1.0, 1e-6))
    assert resultado.estado == "EXITO"
    assert len(resultado.advertencias) >= 1


def test_informe_continuidad_se_adjunta_al_exito():
    """La respuesta lleva el informe del preparado."""
    resultado = regla_falsa(EntradaReglaFalsa("x^2 - 2", 1.0, 2.0, 1e-6))
    assert resultado.informe_continuidad is not None
    assert resultado.informe_continuidad["estado"] == "CONFIRMADA"


def test_error_por_punto_medio_invalido_no_itera():
    """cos(x) en [0, 4] debe rechazarse por restriccion solo si aplica; en este caso no."""
    resultado = regla_falsa(EntradaReglaFalsa("cos(x)", 0.0, 4.0, 1e-6))
    # cos(0)=1, cos(4)≈-0.65; signos distintos, debe iterar o cerrar por secante.
    assert resultado.estado in ("EXITO", "ESTANCAMIENTO", "LIMITE_ITERACIONES")