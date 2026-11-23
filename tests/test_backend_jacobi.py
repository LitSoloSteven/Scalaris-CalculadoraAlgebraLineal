"""Comprobaciones del motor de Jacobi con sistemas reproducibles."""
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.jacobi.aritmetica_jacobi import (
    LimiteAritmeticoJacobi, PresupuestoAritmetico,
)
from src.backend.resolutores.sistemas_lineales.jacobi.contrato_jacobi import (
    EntradaJacobi, MatrizCrudaJacobi, ResultadoJacobi,
)
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi
from src.backend.resolutores.sistemas_lineales.jacobi.limites_jacobi import (
    MAXIMO_BITS_CALCULO_JACOBI,
)
import src.backend.resolutores.sistemas_lineales.jacobi.jacobi as motor


def _matriz(datos: list[list[int]]) -> MatrizCrudaJacobi:
    return tuple(tuple(fila) for fila in datos)


def _ejecutar(
    matriz: MatrizCrudaJacobi,
    vector_b: tuple | list,
    vector_inicial: tuple | list | None = None,
    tolerancia: Fraction | int | str = Fraction(1, 100),
    maximo: int = 5,
) -> ResultadoJacobi:
    inicio = (
        (0,) * len(matriz)
        if vector_inicial is None
        else vector_inicial
    )
    return resolver_jacobi(EntradaJacobi(
        matriz_a=matriz,
        vector_b=tuple(vector_b),
        vector_inicial=inicio,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
    ))


def _residuo_manual(datos: list[list[int]], vector_b: list, vector: tuple) -> tuple:
    """Calcula b - A·x con un recorrido independiente del motor."""
    return tuple(
        termino - sum(
            (coeficiente * componente for coeficiente, componente in zip(fila, vector)),
            Fraction(0),
        )
        for termino, fila in zip(vector_b, datos)
    )


def test_actualizacion_simultanea_y_parada_por_maximo() -> None:
    """Las dos primeras iteraciones usan el vector anterior completo."""
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2], maximo=2)
    primero, segundo = resultado.pasos

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert primero.vector_nuevo == (Fraction(1, 2), Fraction(2, 3))
    assert segundo.vector_anterior == primero.vector_nuevo
    assert segundo.vector_nuevo == (Fraction(1, 3), Fraction(1, 2))
    assert resultado.aproximacion == (Fraction(1, 3), Fraction(1, 2))
    assert resultado.residuo == (Fraction(1, 6), Fraction(1, 6))
    assert resultado.norma_residuo == Fraction(1, 6)
    assert resultado.iteraciones_realizadas == 2


def test_tolerancia_se_alcanza_en_el_ultimo_paso_permitido() -> None:
    """La igualdad con el umbral se comprueba antes que el máximo."""
    resultado = _ejecutar(
        _matriz([[4, 1], [1, 3]]), [2, 2], tolerancia=Fraction(1, 6), maximo=2,
    )

    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    assert resultado.iteraciones_realizadas == 2
    assert resultado.norma_residuo == Fraction(1, 6)


def test_inicio_exacto_termina_sin_iteraciones() -> None:
    """Un vector inicial que ya resuelve el sistema no consume el máximo."""
    resultado = _ejecutar(
        _matriz([[4, 1], [1, 3]]), [2, 2],
        [Fraction(4, 11), Fraction(6, 11)],
    )

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.iteraciones_realizadas == 0
    assert resultado.residuo == (Fraction(0), Fraction(0))
    assert resultado.norma_residuo == 0


def test_sistema_de_una_variable() -> None:
    """La dimensión uno se resuelve en un paso exacto."""
    resultado = _ejecutar(_matriz([[3]]), [1])

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == (Fraction(1, 3),)
    assert resultado.residuo == (Fraction(0),)
    assert resultado.iteraciones_realizadas == 1


def test_convergencia_sin_dominancia_estricta() -> None:
    """El método avanza aunque la dominancia por filas sea falsa."""
    resultado = _ejecutar(_matriz([[1, 2], [0, 1]]), [3, 1], maximo=2)
    vectores = [paso.vector_nuevo for paso in resultado.pasos]

    assert resultado.dominancia_estricta is False
    assert vectores == [(Fraction(3), Fraction(1)), (Fraction(1), Fraction(1))]
    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.norma_residuo == 0


def test_sistema_que_se_aleja_conserva_la_ultima_aproximacion() -> None:
    """Agotar el máximo devuelve el último vector completo y su residuo."""
    resultado = _ejecutar(_matriz([[1, 2], [2, 1]]), [1, 1], maximo=3)
    vectores = [paso.vector_nuevo for paso in resultado.pasos]

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert vectores == [
        (Fraction(1), Fraction(1)),
        (Fraction(-1), Fraction(-1)),
        (Fraction(3), Fraction(3)),
    ]
    assert resultado.aproximacion == (Fraction(3), Fraction(3))
    assert resultado.residuo == (Fraction(-8), Fraction(-8))
    assert resultado.norma_residuo == 8


def test_diagonal_nula_se_informa_antes_de_dividir() -> None:
    """Una diagonal cero bloquea el cálculo e identifica la ecuación."""
    resultado = _ejecutar(_matriz([[0, 1], [1, 2]]), [1, 3])

    assert resultado.codigo == "DIAGONAL_NULA"
    assert resultado.aproximacion is None
    assert resultado.pasos == ()
    assert resultado.diagnostico.campo == "matriz_a"
    assert (resultado.diagnostico.fila, resultado.diagnostico.columna) == (1, 1)


def test_ejemplo_de_cuatro_variables_conserva_el_vector_anterior() -> None:
    """Las dos primeras iteraciones coinciden con la sustitución exacta."""
    datos = [[10, -1, 2, 0], [-1, 11, -1, 3], [2, -1, 10, -1], [0, 3, -1, 8]]
    resultado = _ejecutar(_matriz(datos), [6, 25, -11, 15], maximo=2)
    primero, segundo = resultado.pasos

    assert resultado.dominancia_estricta is True
    assert primero.vector_nuevo == (
        Fraction(3, 5), Fraction(25, 11), Fraction(-11, 10), Fraction(15, 8),
    )
    assert segundo.vector_anterior == primero.vector_nuevo
    assert segundo.vector_nuevo == (
        Fraction(288, 275), Fraction(151, 88), Fraction(-3543, 4400), Fraction(779, 880),
    )


def test_el_residuo_se_verifica_con_un_recorrido_independiente() -> None:
    """El residuo final coincide con b - A·x calculado fuera del motor."""
    datos = [[4, 1], [1, 3]]
    resultado = _ejecutar(_matriz(datos), [2, 2], maximo=2)
    esperado = _residuo_manual(datos, [Fraction(2), Fraction(2)], resultado.aproximacion)

    assert esperado == (Fraction(1, 6), Fraction(1, 6))
    assert resultado.residuo == esperado
    assert resultado.norma_residuo == max(abs(valor) for valor in esperado)


def test_cada_paso_conserva_el_residuo_del_vector_nuevo() -> None:
    """La traza permite reproducir la métrica de cada actualización completa."""
    datos = [[4, 1], [1, 3]]
    resultado = _ejecutar(_matriz(datos), [2, 2], maximo=2)

    for paso in resultado.pasos:
        esperado = _residuo_manual(datos, [Fraction(2), Fraction(2)], paso.vector_nuevo)
        assert paso.norma_residuo == max(abs(valor) for valor in esperado)


def test_limite_aritmetico_conserva_el_ultimo_paso_completo(monkeypatch) -> None:
    """Un fallo al calcular el vector siguiente no publica una iteración parcial."""
    calcular = motor._siguiente_vector
    llamadas = []

    def _fallar_en_la_segunda(*argumentos):
        llamadas.append(1)
        if len(llamadas) > 1:
            raise LimiteAritmeticoJacobi("Límite simulado.")
        return calcular(*argumentos)

    monkeypatch.setattr(motor, "_siguiente_vector", _fallar_en_la_segunda)
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2])
    ultimo = resultado.pasos[-1]

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == ultimo.vector_nuevo
    assert resultado.residuo == (Fraction(-2, 3), Fraction(-1, 2))
    assert resultado.diagnostico is not None


def test_limite_aritmetico_antes_del_residuo_inicial(monkeypatch) -> None:
    """Sin residuo inicial verificable no se declara una aproximación."""
    def _fallar(*argumentos):
        raise LimiteAritmeticoJacobi("Límite simulado.")

    monkeypatch.setattr(motor, "residuo_sistema", _fallar)
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2])

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.aproximacion is None
    assert resultado.residuo is None
    assert resultado.pasos == ()
    assert resultado.diagnostico is not None


def test_limite_aritmetico_real_durante_la_iteracion() -> None:
    """El crecimiento exacto agota el presupuesto sin publicar un paso parcial."""
    grande = 2 ** (MAXIMO_BITS_CALCULO_JACOBI // 2)
    resultado = _ejecutar(_matriz([[1, grande], [grande, 1]]), [1, 1], maximo=4)

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.iteraciones_realizadas == 3
    assert resultado.aproximacion == (Fraction(grande ** 2 - grande + 1),) * 2
    assert resultado.residuo == (-grande ** 3,) * 2


def test_la_solucion_exacta_prevalece_sobre_la_norma_del_cambio() -> None:
    """Una diferencia grande no descarta un residuo ya certificado."""
    grande = 2 ** (MAXIMO_BITS_CALCULO_JACOBI - 1)
    matriz = ((Fraction(1, 2),),)
    resultado = _ejecutar(matriz, [Fraction(-grande, 2)], [grande])

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == (Fraction(-grande),)
    assert resultado.pasos[0].norma_cambio == 2 * grande
    assert (resultado.pasos[0].norma_cambio.numerator.bit_length()
            == MAXIMO_BITS_CALCULO_JACOBI + 1)


def test_presupuesto_aritmetico_cuenta_y_rechaza_fracciones_grandes() -> None:
    """El contador agota su cupo y el tamaño de cálculo se comprueba aparte."""
    presupuesto = PresupuestoAritmetico(operaciones=1)
    presupuesto.consumir()
    with pytest.raises(LimiteAritmeticoJacobi):
        presupuesto.consumir()
    with pytest.raises(LimiteAritmeticoJacobi):
        PresupuestoAritmetico().registrar(Fraction(10 ** 5000))
