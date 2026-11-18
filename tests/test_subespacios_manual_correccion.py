"""Regresiones del manual de correccion: fracciones largas y traza inmutable."""
import json
from fractions import Fraction
from random import Random

import pytest

from src.backend.modelos.conversion_fracciones import texto_fraccion_exacta
from src.backend.resolutores.operaciones_vectores.captura_subespacios import (
    capturar_restricciones,
)
from src.backend.resolutores.operaciones_vectores.subespacios import analizar_subespacio
from src.frontend.controladores.operaciones_matrices.codificador import CodificadorMatriz


def _captura_fracciones_largas():
    """Reproduce el sistema 10x10 del manual con la semilla indicada."""
    azar = Random(0)
    matriz = [
        [f"1/{azar.randrange(10**58, 10**59)}" for _ in range(10)]
        for _ in range(10)
    ]
    return capturar_restricciones({
        "modo": "restricciones",
        "dimension_ambiente": 10,
        "matriz_a": matriz,
        "vector_b": [1] * 10,
    })


def _satisface_sistema(entrada, particular, direcciones):
    """Comprueba A·p=b y A·d=0 con racionales exactos, sin usar el resultado textual."""
    for fila, termino in zip(entrada["matriz_a"].datos, entrada["vector_b"]):
        izquierda = sum(
            (coeficiente * valor for coeficiente, valor in zip(fila, particular)),
            Fraction(0),
        )
        if izquierda != termino:
            return False
        for direccion in direcciones:
            peso = sum(
                (coeficiente * valor for coeficiente, valor in zip(fila, direccion)),
                Fraction(0),
            )
            if peso != 0:
                return False
    return True


def test_fracciones_largas_devuelven_afin_exacto_y_serializable():
    """Un 10x10 con denominadores de 59 digitos evita el limite de texto y conserva exactitud."""
    entrada = _captura_fracciones_largas()
    resultado = analizar_subespacio(entrada)
    assert resultado["estado"] == "EXITO"
    assert resultado["codigo"] == "AFIN_NO_CONTIENE_ORIGEN"
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
    assert _satisface_sistema(
        entrada, resultado["particular"], resultado["direcciones"]
    )
    serializado = json.loads(json.dumps(
        resultado, cls=CodificadorMatriz, ensure_ascii=False
    ))
    assert serializado["particular"][0] == texto_fraccion_exacta(resultado["particular"][0])
    assert serializado["pasos"][0]["matriz"]["columnas"] == 11


def test_pasos_rechazan_cualquier_intento_de_mutacion():
    """Tipo, metadatos y celdas de una instantanea no se pueden alterar ni eliminar."""
    resultado = analizar_subespacio(capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 2,
        "matriz_a": [[1, 1]], "vector_b": [0],
    }))
    paso = resultado["pasos"][0]
    with pytest.raises(TypeError):
        paso["tipo"] = "otro"
    with pytest.raises(TypeError):
        paso["datos"]["fila"] = 0
    with pytest.raises(TypeError):
        paso["matriz"].datos[0][0] = Fraction(9)
    with pytest.raises(AttributeError):
        paso["matriz"].datos = ()
    with pytest.raises(AttributeError):
        del paso["matriz"].datos


def test_traza_inmutable_se_serializa_con_el_codificador_comun():
    """La representacion de solo lectura mantiene el formato matricial esperado por #111."""
    resultado = analizar_subespacio(capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 2,
        "matriz_a": [[1, 1]], "vector_b": [0],
    }))
    serializado = json.loads(json.dumps(resultado, cls=CodificadorMatriz))
    primer_paso = serializado["pasos"][0]
    assert primer_paso["tipo"] == "inicial"
    assert primer_paso["datos"] == {}
    assert primer_paso["matriz"]["filas"] == 1
    assert primer_paso["matriz"]["columnas"] == 3
