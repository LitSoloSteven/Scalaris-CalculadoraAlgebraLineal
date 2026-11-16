"""Motor de Newton-Raphson: ejemplos, paradas, fallos y entradas inválidas."""
import pytest

from src.backend.resolutores.raices.metodos_abiertos import (
    EntradaMetodoAbierto,
    newton,
)


def _datos(**cambios):
    datos = {
        "metodo": "newton",
        "expresion": "x^3 - x - 2",
        "x0": 1.5,
        "tolerancia": 1e-6,
        "limite_iteraciones": 100,
    }
    datos.update(cambios)
    return datos


def _producto_balanceado(cantidad):
    factores = ["x"] * cantidad
    while len(factores) > 1:
        factores = [
            f"({factores[i]}*{factores[i + 1]})"
            for i in range(0, len(factores), 2)
        ]
    return factores[0]


@pytest.mark.parametrize(
    "expresion,x0,raiz,residuo,iteraciones",
    [
        ("x^3 - x - 2", 1.5, 1.5213798059647863, 5.893874259754739e-07, 2),
        ("x^3 - 2*x - 5", 2.0, 2.094551481698199, 1.7397612239733462e-09, 3),
    ],
)
def test_ejemplos_del_pdf(expresion, x0, raiz, residuo, iteraciones):
    """Los ejemplos del documento convergen con los valores esperados."""
    resultado = newton(_datos(expresion=expresion, x0=x0))
    assert resultado.estado == "EXITO"
    assert resultado.codigo_diagnostico == "TOLERANCIA_RESIDUO"
    assert resultado.raiz == pytest.approx(raiz, rel=1e-12)
    assert resultado.residuo == pytest.approx(residuo, rel=1e-9, abs=1e-15)
    assert resultado.iteraciones_totales == iteraciones
    assert resultado.derivada_expresion is not None


def test_newton_acepta_entrada_tipada():
    """El motor acepta la entrada canónica además de la captura cruda."""
    entrada = EntradaMetodoAbierto(metodo="newton", expresion="x^3 - x - 2", x0=1.5)
    resultado = newton(entrada)
    assert resultado.estado == "EXITO"
    assert resultado.entrada == entrada


def test_punto_inicial_que_ya_es_raiz():
    """Un residuo exactamente cero termina sin iterar."""
    resultado = newton(_datos(expresion="x - 2", x0=2))
    assert resultado.codigo_diagnostico == "PUNTO_INICIAL_RAIZ"
    assert resultado.iteraciones_totales == 0


def test_punto_inicial_que_ya_cumple_tolerancia():
    """Un residuo menor que la tolerancia no necesita el primer paso."""
    resultado = newton(_datos(expresion="x - 1.5000001", x0=1.5, tolerancia=1e-6))
    assert resultado.codigo_diagnostico == "PUNTO_INICIAL_TOLERANCIA"
    assert resultado.iteraciones_totales == 0


def test_derivada_nula_se_reporta_sin_excepcion():
    """Una derivada despreciable detiene el método con diagnóstico propio."""
    resultado = newton(_datos(expresion="x^2 + 1", x0=0))
    assert resultado.estado == "DERIVADA_NULA"
    assert resultado.contexto_fallo["derivada"] == 0


def test_derivada_relativamente_pequena_detiene_newton():
    """La guarda relativa evita pasos gigantes aunque la derivada no sea cero."""
    resultado = newton(_datos(expresion="1/x", x0=1))
    assert resultado.estado == "DERIVADA_NULA"
    assert resultado.iteraciones_totales > 0
    assert resultado.contexto_fallo["x"] == pytest.approx(16384.0)


def test_error_de_evaluacion_en_el_punto_inicial():
    """Un punto fuera del dominio devuelve ERROR de evaluación."""
    resultado = newton(_datos(expresion="ln(x)", x0=-1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EVALUACION"
    assert resultado.contexto_fallo["x"] == -1


def test_limite_de_iteraciones_conserva_las_filas():
    """Si se agota el límite se devuelve la última aproximación y una fila."""
    resultado = newton(_datos(expresion="x^2 - 2", x0=1, tolerancia=1e-15, limite_iteraciones=1))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.iteraciones_totales == 1
    assert resultado.raiz == pytest.approx(1.5)
    assert resultado.residuo == pytest.approx(0.25)


def test_divergencia_por_magnitud():
    """Un paso fuera del límite de magnitud se reporta como divergencia."""
    resultado = newton(_datos(expresion="x + 2e12", x0=0))
    assert resultado.estado == "DIVERGENCIA"
    assert resultado.codigo_diagnostico == "DIVERGENCIA"


def test_derivada_no_disponible():
    """x^x no tiene regla simbólica en esta versión."""
    resultado = newton(_datos(expresion="x^x", x0=1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DERIVADA_NO_DISPONIBLE"


def test_derivada_demasiado_grande():
    """Una derivada que excede la gramática se reporta con un código propio."""
    resultado = newton(_datos(expresion=_producto_balanceado(64), x0=1))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DERIVADA_DEMASIADO_GRANDE"


def test_fila_de_newton_registra_derivada_y_criterio():
    """La última fila conserva la derivada y el criterio que detuvo el método."""
    resultado = newton(_datos())
    fila = resultado.iteraciones[-1]
    assert fila.x_anterior is None and fila.f_x_anterior is None
    assert fila.derivada is not None
    assert fila.criterio == "residuo"


@pytest.mark.parametrize(
    "cambios",
    [
        {"tolerancia": 0},
        {"tolerancia": -1e-6},
        {"tolerancia": float("nan")},
        {"tolerancia": float("inf")},
        {"tolerancia": "1e-6"},
        {"tolerancia": True},
        {"limite_iteraciones": 0},
        {"limite_iteraciones": 501},
        {"limite_iteraciones": 3.0},
        {"limite_iteraciones": True},
        {"limite_iteraciones": "100"},
        {"x0": float("nan")},
        {"x0": float("inf")},
        {"x0": "1.5"},
        {"x0": True},
        {"metodo": "secante"},
    ],
)
def test_entrada_invalida_devuelve_error(cambios):
    """La captura inválida nunca escapa como excepción hacia la interfaz."""
    resultado = newton(_datos(**cambios))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"


def test_x0_ausente_devuelve_error():
    """La validación también cubre el campo obligatorio ausente."""
    resultado = newton({"metodo": "newton", "expresion": "x - 1"})
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"
