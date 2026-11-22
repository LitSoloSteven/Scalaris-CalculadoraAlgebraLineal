"""Reproducibilidad del resultado sin depender de la captura original."""
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from fractions import Fraction
from types import ModuleType

import pytest

import src.backend.resolutores.sistemas_lineales.gauss_seidel.gauss_seidel as motor_gauss_seidel
import src.backend.resolutores.sistemas_lineales.jacobi.jacobi as motor_jacobi
from src.backend.resolutores.sistemas_lineales.iterativos.aritmetica_iterativa import (
    LimiteAritmeticoIterativo,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import (
    ResultadoIterativo,
)

ResolutorCaptura = Callable[[object], ResultadoIterativo]
RESOLUTORES = (
    (motor_gauss_seidel, motor_gauss_seidel.resolver_gauss_seidel_desde_captura),
    (motor_jacobi, motor_jacobi.resolver_jacobi_desde_captura),
)


def _captura() -> dict[str, object]:
    return {
        "matriz_a": [["4", "1"], ["1", "3"]],
        "vector_b": ["2", "2"],
        "vector_inicial": ["0", "0"],
        "tolerancia": "1/100",
        "maximo_iteraciones": 2,
    }


@pytest.mark.parametrize("modulo,resolver", RESOLUTORES)
def test_el_resultado_conserva_todos_los_datos_canonicos(
    modulo: ModuleType, resolver: ResolutorCaptura,
) -> None:
    """La instantánea incluye racionales exactos y los parámetros originales."""
    captura = _captura()
    captura["matriz_a"] = [["4", "0.125"], ["1/3", "3"]]
    resultado = resolver(captura)
    entrada = resultado.entrada_canonica

    assert entrada is not None
    assert entrada.matriz == (
        (Fraction(4), Fraction(1, 8)), (Fraction(1, 3), Fraction(3)),
    )
    assert entrada.vector_b == (Fraction(2), Fraction(2))
    assert entrada.vector_inicial == (Fraction(0), Fraction(0))
    assert entrada.tolerancia == Fraction(1, 100)
    assert entrada.maximo_iteraciones == 2
    assert entrada.dominancia_estricta is True


@pytest.mark.parametrize("modulo,resolver", RESOLUTORES)
def test_la_captura_mutable_no_altera_el_resultado(
    modulo: ModuleType, resolver: ResolutorCaptura,
) -> None:
    """Cambiar A, b y el inicio tras resolver no modifica la instantánea."""
    matriz = [[4, 1], [1, 3]]
    terminos = [2, 2]
    inicio = [0, 0]
    captura = _captura()
    captura.update(matriz_a=matriz, vector_b=terminos, vector_inicial=inicio)
    resultado = resolver(captura)
    matriz[0][0], terminos[0], inicio[0] = 99, 99, 99
    captura.clear()
    entrada = resultado.entrada_canonica

    assert entrada is not None
    assert entrada.matriz == ((Fraction(4), Fraction(1)), (Fraction(1), Fraction(3)))
    assert entrada.vector_b == (Fraction(2), Fraction(2))
    assert entrada.vector_inicial == (Fraction(0), Fraction(0))
    with pytest.raises(FrozenInstanceError):
        setattr(entrada, "tolerancia", Fraction(99))
    with pytest.raises(TypeError):
        entrada.matriz[0][0] = Fraction(99)


@pytest.mark.parametrize("modulo,resolver", RESOLUTORES)
@pytest.mark.parametrize("tolerancia,codigo", [
    ("1/100", "SOLUCION_EXACTA"), ("1/10", "TOLERANCIA_ALCANZADA"),
])
def test_una_parada_inicial_conserva_la_entrada(
    modulo: ModuleType, resolver: ResolutorCaptura, tolerancia: str, codigo: str,
) -> None:
    """La solución exacta y la tolerancia inicial preservan el sistema sin pasos."""
    captura = _captura()
    captura.update(matriz_a=[[1]], vector_b=["1/20"], tolerancia=tolerancia)
    captura["vector_inicial"] = ["1/20" if codigo == "SOLUCION_EXACTA" else "0"]
    resultado = resolver(captura)

    assert resultado.codigo == codigo
    assert resultado.iteraciones_realizadas == 0
    assert resultado.entrada_canonica is not None
    assert resultado.entrada_canonica.vector_b == (Fraction(1, 20),)
    assert resultado.explicacion


@pytest.mark.parametrize("modulo,resolver", RESOLUTORES)
def test_un_limite_antes_del_residuo_conserva_la_entrada(
    modulo: ModuleType, resolver: ResolutorCaptura, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La captura validada sigue disponible aunque no se verifique el inicio."""
    def _interrumpir(*argumentos):
        raise LimiteAritmeticoIterativo("Se agotó el presupuesto de operaciones.")

    monkeypatch.setattr(modulo, "residuo_sistema", _interrumpir)
    resultado = resolver(_captura())

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.entrada_canonica is not None
    assert resultado.entrada_canonica.vector_inicial == (Fraction(0), Fraction(0))
    assert resultado.aproximacion is None
    assert resultado.pasos == ()
    assert resultado.explicacion == resultado.diagnostico.mensaje


@pytest.mark.parametrize("modulo,resolver", RESOLUTORES)
def test_un_limite_tras_un_barrido_conserva_el_sistema_y_la_traza(
    modulo: ModuleType, resolver: ResolutorCaptura, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Una interrupción posterior mantiene el sistema y el último paso completo."""
    siguiente = modulo._siguiente_vector
    llamadas = []

    def _interrumpir_segundo(*argumentos):
        llamadas.append(1)
        if len(llamadas) == 2:
            raise LimiteAritmeticoIterativo("Se agotó el presupuesto de operaciones.")
        return siguiente(*argumentos)

    monkeypatch.setattr(modulo, "_siguiente_vector", _interrumpir_segundo)
    resultado = resolver(_captura())

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.entrada_canonica is not None
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == resultado.pasos[0].vector_nuevo
    assert "1 barrido" in resultado.explicacion


@pytest.mark.parametrize("modulo,resolver", RESOLUTORES)
@pytest.mark.parametrize("matriz,codigo", [
    ([[1, 2], [3, 0]], "DIAGONAL_NULA"), ([[1, 2]], "ENTRADA_INVALIDA"),
])
def test_una_entrada_rechazada_no_declara_una_instantanea_validada(
    modulo: ModuleType, resolver: ResolutorCaptura, matriz: list, codigo: str,
) -> None:
    """Los errores conservan el diagnóstico sin presentar una captura como válida."""
    captura = _captura()
    captura["matriz_a"] = matriz
    resultado = resolver(captura)

    assert resultado.codigo == codigo
    assert resultado.entrada_canonica is None
    assert resultado.aproximacion is None
    assert resultado.pasos == ()


def test_reconstruir_las_sustituciones_solo_con_el_resultado() -> None:
    """Cada componente se reproduce con los valores nuevos y anteriores guardados."""
    resultado = motor_gauss_seidel.resolver_gauss_seidel_desde_captura({
        "matriz_a": [[4, 1, 1], [1, 4, 1], [1, 1, 4]],
        "vector_b": [1, 2, 3],
        "tolerancia": "1/1000000",
        "maximo_iteraciones": 2,
    })
    entrada = resultado.entrada_canonica

    assert entrada is not None
    assert resultado.iteraciones_realizadas == 2
    for paso in resultado.pasos:
        reconstruido = []
        for indice, fila in enumerate(entrada.matriz):
            nuevos = sum((fila[j] * reconstruido[j] for j in range(indice)), Fraction(0))
            anteriores = sum((fila[j] * paso.vector_anterior[j]
                              for j in range(indice + 1, len(fila))), Fraction(0))
            reconstruido.append((entrada.vector_b[indice] - nuevos - anteriores) / fila[indice])
        assert tuple(reconstruido) == paso.vector_nuevo
