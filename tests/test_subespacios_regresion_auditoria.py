"""Regresiones de exactitud, verificación y trazas del motor de subespacios."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, localcontext
from fractions import Fraction
from math import factorial
from threading import Barrier
import json
import sys

import pytest

from src.backend.modelos.escalares import conversion_fracciones
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.subespacios import subespacios as motor
from src.backend.resolutores.operaciones_vectores.subespacios.captura_subespacios import (
    capturar_generadores,
    capturar_restricciones,
)
from src.frontend.controladores.algebra.operaciones_matrices.base.codificador import CodificadorMatriz


@pytest.fixture
def matriz_de_cauchy() -> list[list[str]]:
    """Construye diez columnas independientes con celdas admitidas por la captura."""
    factor = factorial(110) * 10**71
    return [
        [f"1/{(1 + 10 * fila + columna) * factor + 1}" for columna in range(10)]
        for fila in range(10)
    ]


def test_generadores_largos_reutilizan_la_reduccion_para_certificar_la_base(matriz_de_cauchy, monkeypatch):
    """Conserva la base original y ejecuta una sola reducción exacta."""
    reducciones = []
    reducir = motor.ReductorFilas.reducir

    def _contar_reduccion(reductor):
        reducciones.append(reductor.matriz.columnas)
        return reducir(reductor)

    monkeypatch.setattr(motor.ReductorFilas, "reducir", _contar_reduccion)
    columnas = list(zip(*matriz_de_cauchy))
    entrada = capturar_generadores({
        "modo": "generadores", "dimension_ambiente": 10,
        "vectores": {f"v{indice + 1}": {"datos": columna} for indice, columna in enumerate(columnas)},
    })
    resultado = motor.analizar_subespacio(entrada)

    assert resultado["codigo"] == "SUBESPACIO_GENERADO"
    assert resultado["dimension"] == 10
    assert resultado["indices_generadores_base"] == tuple(range(10))
    assert resultado["base"] == tuple(tuple(map(Fraction, columna)) for columna in columnas)
    assert reducciones == [10]


def test_sistema_incompatible_serializa_el_testigo_racional_largo(matriz_de_cauchy):
    """Conserva la fila contradictoria y su término exacto a través de JSON."""
    entrada = capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 9,
        "matriz_a": [fila[:-1] for fila in matriz_de_cauchy],
        "vector_b": [fila[-1] for fila in matriz_de_cauchy],
    })
    resultado = motor.analizar_subespacio(entrada)

    assert resultado["codigo"] == "SISTEMA_INCOMPATIBLE"
    assert (resultado["rango"], resultado["rango_aumentada"]) == (9, 10)
    testigo = resultado["testigo"]
    assert testigo["coeficientes"] == (Fraction(0),) * 9
    termino = testigo["termino_independiente"]
    assert termino != 0
    assert resultado["matriz_reducida"].obtener(testigo["indice_fila"], 9) == termino
    serializado = json.loads(json.dumps(resultado, cls=CodificadorMatriz))
    numerador, denominador = serializado["testigo"]["termino_independiente"].split("/")
    assert max(len(numerador), len(denominador)) > 4300
    assert Fraction(int(Decimal(numerador)), int(Decimal(denominador))) == termino


@pytest.mark.parametrize("modo", ["generadores", "restricciones"])
def test_matrices_tipadas_serializan_todas_sus_celdas_como_texto_exacto(modo):
    """Preserva enteros fuera del rango seguro de JavaScript en las matrices y la traza."""
    entero = 2**53 + 1
    columna = Matriz(2, 1, [[entero], [0]])
    entrada = {"modo": modo, "dimension_ambiente": 2 if modo == "generadores" else 1}
    if modo == "generadores":
        entrada.update(generadores=(columna,), etiquetas=("v1",))
    else:
        entrada.update(matriz_a=columna, vector_b=(Fraction(0), Fraction(0)))
    resultado = motor.analizar_subespacio(entrada)

    assert resultado["estado"] == "EXITO"
    serializado = json.loads(json.dumps(resultado, cls=CodificadorMatriz))
    assert serializado["matriz_original"]["datos"][0][0] == "9007199254740993"
    matrices = [serializado["matriz_original"], serializado["matriz_reducida"]]
    matrices.extend(paso["matriz"] for paso in serializado["pasos"])
    assert all(isinstance(celda, str) for matriz in matrices for fila in matriz["datos"] for celda in fila)
    assert type(columna.obtener(0, 0)) is int


@pytest.mark.parametrize("coeficiente", [1, 10**4500], ids=["detalle", "resumen"])
@pytest.mark.parametrize("direcciones", [
    [],
    [[0, 1, 0], [0, 0, 1], [0, 1, 0]],
    [[0, 1, 0], [0, 1, 0]],
], ids=["faltantes", "sobrantes", "dependientes"])
def test_restricciones_rechazan_una_base_incompleta_o_dependiente(coeficiente, direcciones, monkeypatch):
    """Detecta un fallo de parametrización aunque todas las direcciones satisfagan Ax=0."""
    entrada = capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 3,
        "matriz_a": [[coeficiente, 0, 0]], "vector_b": [0],
    })
    monkeypatch.setattr(motor, "calcular_solucion_parametrica", lambda *_: {
        "particular": [Fraction(0)] * 3,
        "direcciones": [list(map(Fraction, direccion)) for direccion in direcciones],
    })

    resultado = motor.analizar_subespacio(entrada)

    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "VERIFICACION_INCONSISTENTE"


def test_conversion_concurrente_de_enteros_largos_preserva_el_limite_global(monkeypatch):
    """Fuerza la conversión larga en paralelo y verifica que el intérprete no se reconfigure."""
    limite = sys.get_int_max_str_digits()
    barrera = Barrier(2, timeout=5)

    def _exceder_limite(_):
        raise ValueError("Entero fuera del límite decimal")

    def _rechazar_cambio(_):
        pytest.fail("La conversión no debe modificar el límite del intérprete.")

    def _convertir(entero):
        with localcontext() as contexto:
            contexto.prec = 2
            barrera.wait()
            return conversion_fracciones.texto_entero_exacto(entero)

    monkeypatch.setattr(conversion_fracciones, "str", _exceder_limite, raising=False)
    monkeypatch.setattr(sys, "set_int_max_str_digits", _rechazar_cambio)
    enteros = (10**4500 + 19, -(10**5000 + 23))
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(_convertir, enteros))

    assert resultados == ["1" + "0" * 4498 + "19", "-1" + "0" * 4998 + "23"]
    assert sys.get_int_max_str_digits() == limite


def test_traza_impide_reinicializar_la_matriz_o_alterarla_mediante_vars():
    """Protege la instantánea y permite obtener una copia de trabajo independiente."""
    entrada = capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 1, "matriz_a": [[1]], "vector_b": [0],
    })
    resultado = motor.analizar_subespacio(entrada)
    instantanea = resultado["pasos"][0]["matriz"]

    with pytest.raises(AttributeError):
        instantanea.__init__(1, 2, [[8, 9]])
    with pytest.raises(TypeError):
        vars(instantanea)["datos"] = ((8, 9),)
    copia = instantanea.clonar()
    copia.establecer(0, 0, Fraction(9))
    assert instantanea.datos == ((Fraction(1), Fraction(0)),)
