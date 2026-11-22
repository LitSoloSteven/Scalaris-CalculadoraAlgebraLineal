"""Comprobaciones del motor de Gauss-Seidel con sistemas reproducibles."""
from fractions import Fraction

from src.backend.resolutores.sistemas_lineales.gauss_seidel.contrato_gauss_seidel import (
    EntradaGaussSeidel, MatrizCrudaGaussSeidel, ResultadoGaussSeidel,
)
from src.backend.resolutores.sistemas_lineales.gauss_seidel.gauss_seidel import (
    resolver_gauss_seidel, resolver_gauss_seidel_desde_captura,
)
from src.backend.resolutores.sistemas_lineales.iterativos.aritmetica_iterativa import (
    LimiteAritmeticoIterativo,
)
import src.backend.resolutores.sistemas_lineales.gauss_seidel.gauss_seidel as motor


def _matriz(datos: list[list[int]]) -> MatrizCrudaGaussSeidel:
    return tuple(tuple(fila) for fila in datos)


def _ejecutar(
    matriz: MatrizCrudaGaussSeidel,
    vector_b: tuple | list,
    vector_inicial: tuple | list | None = None,
    tolerancia: Fraction | int | str = Fraction(1, 100),
    maximo: int = 5,
) -> ResultadoGaussSeidel:
    inicio = (0,) * len(matriz) if vector_inicial is None else vector_inicial
    return resolver_gauss_seidel(EntradaGaussSeidel(
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


def test_actualizacion_inmediata_y_parada_por_maximo() -> None:
    """La segunda ecuación usa el valor de x recién calculado en el mismo barrido."""
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2], maximo=2)
    primero, segundo = resultado.pasos

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert primero.vector_nuevo == (Fraction(1, 2), Fraction(1, 2))
    assert segundo.vector_anterior == primero.vector_nuevo
    assert segundo.vector_nuevo == (Fraction(3, 8), Fraction(13, 24))
    assert resultado.aproximacion == (Fraction(3, 8), Fraction(13, 24))
    assert resultado.residuo == (Fraction(-1, 24), Fraction(0))
    assert resultado.norma_residuo == Fraction(1, 24)
    assert resultado.iteraciones_realizadas == 2


def test_tolerancia_se_alcanza_en_el_ultimo_barrido_permitido() -> None:
    """La igualdad con el umbral se comprueba antes que el máximo."""
    resultado = _ejecutar(
        _matriz([[4, 1], [1, 3]]), [2, 2],
        tolerancia=Fraction(1, 24), maximo=2,
    )

    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    assert resultado.iteraciones_realizadas == 2
    assert resultado.norma_residuo == Fraction(1, 24)


def test_inicio_exacto_termina_sin_barridos() -> None:
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
    """La dimensión uno se resuelve en un barrido exacto."""
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


def test_aproximaciones_que_se_alejan_conservan_la_ultima() -> None:
    """Agotar el máximo devuelve el último vector completo y su residuo."""
    resultado = _ejecutar(_matriz([[1, 2], [2, 1]]), [1, 1], maximo=2)
    vectores = [paso.vector_nuevo for paso in resultado.pasos]

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert vectores == [(Fraction(1), Fraction(-1)), (Fraction(3), Fraction(-5))]
    assert resultado.aproximacion == (Fraction(3), Fraction(-5))
    assert resultado.residuo == (Fraction(8), Fraction(0))
    assert resultado.norma_residuo == 8


def test_diagonal_nula_se_informa_antes_de_dividir() -> None:
    """Una diagonal cero bloquea el cálculo e identifica la ecuación."""
    resultado = _ejecutar(_matriz([[1, 2], [3, 0]]), [1, 1])

    assert resultado.codigo == "DIAGONAL_NULA"
    assert resultado.aproximacion is None
    assert resultado.pasos == ()
    assert resultado.diagnostico.campo == "matriz_a"
    assert (resultado.diagnostico.fila, resultado.diagnostico.columna) == (2, 2)


def test_tres_por_tres_usa_las_dos_componentes_nuevas() -> None:
    """La última fila consume los valores actualizados de x e y en el mismo barrido."""
    resultado = _ejecutar(
        _matriz([[2, 0, 0], [1, 2, 0], [1, 1, 2]]), [2, 5, 9], maximo=1,
    )

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.pasos[0].vector_nuevo == (
        Fraction(1), Fraction(2), Fraction(3),
    )
    assert resultado.aproximacion == (Fraction(1), Fraction(2), Fraction(3))
    assert resultado.residuo == (Fraction(0), Fraction(0), Fraction(0))


def test_la_traza_conserva_el_primer_barrido_tras_el_segundo() -> None:
    """El vector histórico no cambia aunque el cálculo en sitio continúe."""
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2], maximo=2)

    assert resultado.pasos[0].vector_anterior == (Fraction(0), Fraction(0))
    assert resultado.pasos[0].vector_nuevo == (Fraction(1, 2), Fraction(1, 2))
    assert resultado.pasos[1].vector_anterior == (Fraction(1, 2), Fraction(1, 2))
    assert resultado.pasos[1].vector_nuevo == (Fraction(3, 8), Fraction(13, 24))


def test_el_residuo_se_verifica_con_un_recorrido_independiente() -> None:
    """El residuo de cada paso y el final coinciden con b - A·x externo."""
    datos = [[4, 1], [1, 3]]
    resultado = _ejecutar(_matriz(datos), [2, 2], maximo=2)

    for paso in resultado.pasos:
        esperado = _residuo_manual(datos, [Fraction(2), Fraction(2)], paso.vector_nuevo)
        assert paso.norma_residuo == max(abs(valor) for valor in esperado)
    esperado_final = _residuo_manual(
        datos, [Fraction(2), Fraction(2)], resultado.aproximacion,
    )
    assert resultado.residuo == esperado_final


def test_limite_aritmetico_conserva_el_ultimo_barrido_completo(monkeypatch) -> None:
    """Un fallo a mitad del segundo barrido no publica una iteración parcial."""
    calcular = motor.producto_fila_mixto
    llamadas = []

    def _fallar_en_la_cuarta(*argumentos, **opciones):
        llamadas.append(1)
        if len(llamadas) > 3:
            raise LimiteAritmeticoIterativo("Límite simulado.")
        return calcular(*argumentos, **opciones)

    monkeypatch.setattr(motor, "producto_fila_mixto", _fallar_en_la_cuarta)
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2])

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.iteraciones_realizadas == 1
    assert resultado.aproximacion == (Fraction(1, 2), Fraction(1, 2))
    assert resultado.residuo == (Fraction(-1, 2), Fraction(0))
    assert resultado.diagnostico is not None


def test_limite_aritmetico_antes_del_residuo_inicial(monkeypatch) -> None:
    """Sin residuo inicial verificable no se declara una aproximación."""
    def _fallar(*argumentos):
        raise LimiteAritmeticoIterativo("Límite simulado.")

    monkeypatch.setattr(motor, "residuo_sistema", _fallar)
    resultado = _ejecutar(_matriz([[4, 1], [1, 3]]), [2, 2])

    assert resultado.codigo == "LIMITE_ARITMETICO"
    assert resultado.aproximacion is None
    assert resultado.residuo is None
    assert resultado.pasos == ()
    assert resultado.diagnostico is not None


def test_dimension_diez_resuelve_en_un_barrido() -> None:
    """El tope de sistemas admite diez variables con diagonal no nula."""
    matriz = [[10 if fila == columna else 0 for columna in range(10)] for fila in range(10)]
    resultado = _ejecutar(matriz, [10] * 10, maximo=1)

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == (Fraction(1),) * 10
    assert resultado.iteraciones_realizadas == 1


def test_captura_omitida_empieza_en_cero() -> None:
    """La captura sin vector_inicial construye un cero por variable."""
    resultado = resolver_gauss_seidel_desde_captura({
        "matriz_a": [[4, 1], [1, 3]],
        "vector_b": [2, 2],
        "tolerancia": "1/100",
        "maximo_iteraciones": 1,
    })

    assert resultado.pasos[0].vector_anterior == (Fraction(0), Fraction(0))
    assert resultado.pasos[0].vector_nuevo == (Fraction(1, 2), Fraction(1, 2))
