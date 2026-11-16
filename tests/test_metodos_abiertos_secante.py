"""Motor de la secante: ejemplos, paradas, fallos y entradas inválidas."""
import pytest

from src.backend.resolutores.raices.metodos_abiertos import secante


def _datos(**cambios):
    datos = {
        "metodo": "secante",
        "expresion": "x^3 - x - 2",
        "x0": 1.0,
        "x1": 2.0,
        "tolerancia": 1e-6,
        "limite_iteraciones": 100,
    }
    datos.update(cambios)
    return datos


@pytest.mark.parametrize(
    "caso",
    [
        ("x^3 - x - 2", 1.0, 2.0, 1.5213797079848717, 7.015477976324291e-09, 6),
        ("x^3 - 2*x - 5", 2.0, 3.0, 2.094551481227599, 3.512811375117053e-09, 5),
    ],
)
def test_ejemplos_del_pdf(caso):
    """Los ejemplos del documento convergen con los valores esperados."""
    expresion, x0, x1, raiz, residuo, iteraciones = caso
    resultado = secante(_datos(expresion=expresion, x0=x0, x1=x1))
    assert resultado.estado == "EXITO"
    assert resultado.codigo_diagnostico == "TOLERANCIA_RESIDUO"
    assert resultado.raiz == pytest.approx(raiz, rel=1e-12)
    assert resultado.residuo == pytest.approx(residuo, rel=1e-8, abs=1e-15)
    assert resultado.iteraciones_totales == iteraciones


def test_puntos_invertidos_llegan_a_la_misma_raiz():
    """El orden de los dos puntos iniciales no cambia la raíz encontrada."""
    normal = secante(_datos(x0=1.0, x1=2.0))
    invertido = secante(_datos(x0=2.0, x1=1.0))
    assert invertido.estado == "EXITO"
    assert invertido.raiz == pytest.approx(normal.raiz, rel=1e-6)


def test_puntos_iguales_devuelven_error():
    """x0 == x1 se detecta antes de evaluar la función."""
    resultado = secante(_datos(x0=2.0, x1=2.0))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"


def test_denominador_nulo_con_funcion_constante():
    """Una función constante anula la diferencia de residuos."""
    resultado = secante(_datos(expresion="1", x0=1.0, x1=2.0))
    assert resultado.estado == "DENOMINADOR_NULO"
    assert resultado.contexto_fallo["denominador"] == 0


def test_punto_inicial_que_ya_es_raiz():
    """El primer punto puede ser raíz exacta sin iterar."""
    resultado = secante(_datos(expresion="x - 2", x0=2.0, x1=3.0))
    assert resultado.codigo_diagnostico == "PUNTO_INICIAL_RAIZ"
    assert resultado.iteraciones_totales == 0


def test_error_de_evaluacion_en_un_punto_inicial():
    """Un punto fuera del dominio devuelve ERROR de evaluación."""
    resultado = secante(_datos(expresion="ln(x)", x0=-1.0, x1=2.0))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "EVALUACION"


def test_limite_de_iteraciones_conserva_las_filas():
    """Si se agota el límite se devuelve la última aproximación y una fila."""
    resultado = secante(_datos(expresion="x^2 - 2", x0=1.0, x1=2.0, tolerancia=1e-15, limite_iteraciones=1))
    assert resultado.estado == "LIMITE_ITERACIONES"
    assert resultado.iteraciones_totales == 1


def test_divergencia_por_magnitud():
    """Con tolerancia estricta, 1/x crece hasta exceder el límite de magnitud."""
    resultado = secante(_datos(expresion="1/x", x0=1.0, x1=2.0, tolerancia=1e-15))
    assert resultado.estado == "DIVERGENCIA"
    assert resultado.codigo_diagnostico == "DIVERGENCIA"


def test_fila_de_secante_registra_los_dos_puntos():
    """Cada fila conserva los puntos anterior y actual, sin derivada."""
    resultado = secante(_datos())
    fila = resultado.iteraciones[-1]
    assert fila.x_anterior is not None and fila.f_x_anterior is not None
    assert fila.derivada is None
    assert fila.criterio == "residuo"


@pytest.mark.parametrize(
    "cambios",
    [
        {"x1": None},
        {"x1": ""},
        {"x1": float("nan")},
        {"x1": float("inf")},
        {"x1": True},
        {"tolerancia": 0},
        {"tolerancia": -1e-6},
        {"tolerancia": float("nan")},
        {"limite_iteraciones": 0},
        {"limite_iteraciones": 501},
        {"limite_iteraciones": 3.0},
        {"metodo": "newton"},
    ],
)
def test_entrada_invalida_devuelve_error(cambios):
    """La captura inválida nunca escapa como excepción hacia la interfaz."""
    resultado = secante(_datos(**cambios))
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"
