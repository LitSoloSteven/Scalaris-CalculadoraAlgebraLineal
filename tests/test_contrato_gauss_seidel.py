"""Contrato público y explicación de resultados de Gauss-Seidel."""
from fractions import Fraction

from src.backend.resolutores.sistemas_lineales.gauss_seidel import (
    DiagnosticoGaussSeidel,
    EntradaGaussSeidel,
    PasoGaussSeidel,
    ResultadoGaussSeidel,
    resolver_gauss_seidel,
)
import src.backend.resolutores.sistemas_lineales.gauss_seidel as paquete


def _entrada(
    matriz_a: tuple, vector_b: tuple, vector_inicial: tuple,
    tolerancia: Fraction = Fraction(1, 100), maximo: int = 3,
) -> EntradaGaussSeidel:
    return EntradaGaussSeidel(
        matriz_a=matriz_a,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
    )


def test_el_paquete_expone_el_contrato_publico() -> None:
    """Cada nombre declarado en __all__ existe dentro del paquete."""
    faltantes = [nombre for nombre in paquete.__all__ if not hasattr(paquete, nombre)]

    assert faltantes == []
    assert "resolver_gauss_seidel" in paquete.__all__
    assert "resolver_gauss_seidel_desde_captura" in paquete.__all__


def test_explicacion_de_una_solucion_inicial_exacta() -> None:
    """Un inicio que ya resuelve el sistema se describe sin barridos."""
    resultado = resolver_gauss_seidel(_entrada(
        ((4, 1), (1, 3)), (2, 2), (Fraction(4, 11), Fraction(6, 11)),
    ))

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.explicacion == (
        "El vector inicial ya era una solución exacta (4/11, 6/11)."
    )


def test_explicacion_de_una_solucion_exacta_en_un_barrido() -> None:
    """El conteo de barridos usa singular cuando corresponde."""
    resultado = resolver_gauss_seidel(_entrada(((3,),), (1,), (0,)))

    assert resultado.explicacion == (
        "El método encontró una solución exacta (1/3) tras 1 barrido."
    )


def test_explicacion_de_la_tolerancia_alcanzada() -> None:
    """La explicación incluye la aproximación, la norma y los barridos."""
    resultado = resolver_gauss_seidel(_entrada(
        ((4, 1), (1, 3)), (2, 2), (0, 0),
        tolerancia=Fraction(1, 24), maximo=2,
    ))

    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    assert resultado.explicacion == (
        "La aproximación (3/8, 13/24) cumple la tolerancia con una norma del "
        "residuo de 1/24 tras 2 barridos."
    )


def test_explicacion_del_maximo_de_iteraciones() -> None:
    """Agotar el máximo describe el último vector y su residuo."""
    resultado = resolver_gauss_seidel(_entrada(
        ((4, 1), (1, 3)), (2, 2), (0, 0), maximo=1,
    ))

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert resultado.explicacion == (
        "Se alcanzó el máximo de 1 barrido con la aproximación (1/2, 1/2) "
        "y una norma del residuo de 1/2."
    )


def test_explicacion_del_limite_aritmetico_con_aproximacion() -> None:
    """El límite a mitad de barrido conserva y describe el último vector completo."""
    paso = PasoGaussSeidel(
        indice=1,
        vector_anterior=(Fraction(0), Fraction(0)),
        vector_nuevo=(Fraction(1, 2), Fraction(1, 2)),
        norma_cambio=Fraction(1, 2),
        norma_residuo=Fraction(1, 2),
    )
    resultado = ResultadoGaussSeidel(
        codigo="LIMITE_ARITMETICO",
        aproximacion=paso.vector_nuevo,
        residuo=(Fraction(-1, 2), Fraction(0)),
        norma_residuo=Fraction(1, 2),
        pasos=(paso,),
        diagnostico=DiagnosticoGaussSeidel(mensaje="Límite simulado."),
    )

    assert resultado.explicacion == (
        "El cálculo se interrumpió por el límite aritmético tras 1 barrido; "
        "se conserva la aproximación (1/2, 1/2) con una norma del residuo de 1/2."
    )


def test_explicacion_de_un_error_usa_el_diagnostico() -> None:
    """Sin vector verificado, la explicación es el diagnóstico ubicado."""
    resultado = resolver_gauss_seidel(_entrada(
        ((1, 2), (3, 0)), (1, 1), (0, 0),
    ))

    assert resultado.codigo == "DIAGONAL_NULA"
    assert resultado.explicacion == resultado.diagnostico.mensaje
    assert "A[2,2]" in resultado.explicacion


def test_explicacion_de_una_entrada_invalida() -> None:
    """Una entrada ajena al contrato explica qué se esperaba."""
    resultado = resolver_gauss_seidel(object())

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.explicacion == resultado.diagnostico.mensaje
    assert "Gauss-Seidel" in resultado.explicacion


def test_explicacion_sin_vector_ni_diagnostico() -> None:
    """Un resultado incompleto no inventa una aproximación."""
    resultado = ResultadoGaussSeidel(codigo="ENTRADA_INVALIDA")

    assert resultado.explicacion == (
        "No se pudo verificar una aproximación del sistema."
    )
