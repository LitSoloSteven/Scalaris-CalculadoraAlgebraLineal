"""Casos de dominio para operaciones personalizadas y sus certificados exactos."""
from concurrent.futures import CancelledError
from copy import deepcopy
from fractions import Fraction

import pytest

from src.backend.resolutores.operaciones_vectores.espacios_vectoriales import (
    espacios_vectoriales as motor, limites_espacio_vectorial as limites,
)
from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.captura_espacio_vectorial import (
    capturar_espacio_vectorial,
)
from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.contrato_espacio_vectorial import (
    AXIOMAS_ESPACIO_VECTORIAL, ErrorCapturaEspacioVectorial,
)


def _termino(coeficiente, *exponentes):
    return {"coeficiente": coeficiente, "exponentes": list(exponentes)}


def _generadores(*vectores):
    return {
        "modo": "generadores", "dimension_ambiente": len(vectores[0]),
        "vectores": {f"v{indice}": {"datos": list(vector)} for indice, vector in enumerate(vectores, 1)},
    }


def _restricciones(matriz, vector):
    return {"modo": "restricciones", "dimension_ambiente": len(matriz[0]), "matriz_a": matriz, "vector_b": vector}


def _recta_real():
    return {
        "conjunto": _generadores((1,)),
        "suma": [[_termino("1", 1, 0), _termino("1", 0, 1)]],
        "producto_escalar": [[_termino("1", 1, 1)]],
    }


def _operaciones_binarias():
    return {
        "suma": [[_termino("1", 1, 0, 0, 0), _termino("1", 0, 0, 1, 0)],
                 [_termino("1", 0, 1, 0, 0), _termino("1", 0, 0, 0, 1)]],
        "producto_escalar": [[_termino("1", 1, 1, 0)], [_termino("1", 1, 0, 1)]],
    }


def _resolver(captura):
    return motor.analizar_espacio_vectorial(capturar_espacio_vectorial(captura))


def _comprobar(resultado, axioma):
    return next(comprobacion for comprobacion in resultado["comprobaciones"] if comprobacion["axioma"] == axioma)


@pytest.mark.parametrize("altura", ("1", "1/3"))
def test_reconoce_recta_afin_con_operaciones_trasladadas(altura):
    """Certifica los diez axiomas y el neutro trasladado, incluso si es fraccionario."""
    captura = {"conjunto": _restricciones([[0, 1]], [altura]), **_operaciones_binarias()}
    captura["suma"][1].append(_termino(f"-{altura}", 0, 0, 0, 0))
    captura["producto_escalar"][1].extend([_termino(f"-{altura}", 1, 0, 0), _termino(altura, 0, 0, 0)])
    resultado = _resolver(captura)
    assert (resultado["estado"], resultado["codigo"], resultado["es_espacio_vectorial"]) == (
        "EXITO", "ESPACIO_VECTORIAL", True,
    )
    assert resultado["vector_cero"] == (Fraction(0), Fraction(altura))
    assert all(comprobacion["estado"] == "CUMPLE" for comprobacion in resultado["comprobaciones"])


def test_reconoce_recta_real_y_normaliza_terminos_duplicados():
    """Cancela monomios iguales con coeficientes exactos de signos opuestos."""
    captura = _recta_real()
    captura["suma"][0].extend([_termino("0.125", 3, 0), _termino("-1/8", 3, 0)])
    resultado = _resolver(captura)
    assert resultado["es_espacio_vectorial"] is True
    assert resultado["vector_cero"] == (Fraction(0),)
    assert tuple(comprobacion["axioma"] for comprobacion in resultado["comprobaciones"]) == AXIOMAS_ESPACIO_VECTORIAL
    for comprobacion in resultado["comprobaciones"]:
        assert comprobacion["estado"] == "CUMPLE"
        assert not any(comprobacion["certificado"]["identidades"])


def test_recta_afin_con_operaciones_usuales_tiene_residuos_de_cierre():
    """Certifica que las operaciones usuales producen puntos fuera de la recta afín."""
    resultado = _resolver({"conjunto": _restricciones([[0, 1]], [1]), **_operaciones_binarias()})
    assert resultado["codigo"] == "NO_ESPACIO_VECTORIAL"
    assert resultado["vector_cero"] is None
    suma = _comprobar(resultado, "CIERRE_SUMA")
    assert suma["estado"] == "NO_CUMPLE"
    assert suma["certificado"] == {
        "variables_libres": ("u1", "v1"),
        "identidades": (({"coeficiente": Fraction(1), "exponentes": (0, 0)},),),
    }
    assert _comprobar(resultado, "CIERRE_ESCALAR")["estado"] == "NO_CUMPLE"


def test_el_cierre_en_un_espacio_generado_usa_su_nucleo_dual():
    """Verifica la pertenencia incluso si la familia generadora es dependiente."""
    captura = {"conjunto": _generadores((2, 3), (4, 6)), **_operaciones_binarias()}
    assert _resolver(captura)["es_espacio_vectorial"] is True
    captura["suma"][1].append(_termino("1", 0, 0, 0, 0))
    resultado = _resolver(captura)
    assert _comprobar(resultado, "CIERRE_SUMA")["certificado"]["identidades"] == (
        ({"coeficiente": Fraction(1), "exponentes": (0, 0)},),
    )


def test_el_subespacio_cero_admite_operaciones_con_coordenadas_vacias():
    """Interpreta los polinomios sin términos como cero en un conjunto unitario."""
    resultado = _resolver({"conjunto": _generadores((0, 0)), "suma": [[], []], "producto_escalar": [[], []]})
    assert resultado["codigo"] == "ESPACIO_VECTORIAL"
    assert resultado["vector_cero"] == (Fraction(0), Fraction(0))


def test_suma_por_resta_demuestra_violacion_de_conmutatividad():
    """Conserva el residuo exacto de una suma cerrada y no conmutativa."""
    captura = _recta_real()
    captura["suma"][0][1]["coeficiente"] = "-1"
    resultado = _resolver(captura)
    assert resultado["es_espacio_vectorial"] is False
    assert _comprobar(resultado, "CIERRE_SUMA")["estado"] == "CUMPLE"
    assert _comprobar(resultado, "CONMUTATIVIDAD_SUMA")["certificado"]["identidades"] == (
        ({"coeficiente": Fraction(-2), "exponentes": (0, 1)},
         {"coeficiente": Fraction(2), "exponentes": (1, 0)}),
    )


def test_producto_escalar_invalido_no_refuta_la_existencia_de_inversos_aditivos():
    """Distingue el candidato calculado de la existencia real de inversos."""
    captura = _recta_real()
    captura["producto_escalar"] = [[_termino("1", 2, 1)]]
    resultado = _resolver(captura)
    assert _comprobar(resultado, "DISTRIBUTIVIDAD_ESCALARES")["estado"] == "NO_CUMPLE"
    assert _comprobar(resultado, "INVERSO_SUMA")["estado"] == "NO_VERIFICADO"
    assert resultado["vector_cero"] == (Fraction(0),)


def test_suma_nula_interrumpe_la_certificacion_del_neutro_y_del_inverso():
    """Publica la violación de distributividad sin atribuirla a un candidato fallido."""
    captura = _recta_real()
    captura["suma"] = [[]]
    resultado = _resolver(captura)
    assert resultado["codigo"] == "NO_ESPACIO_VECTORIAL"
    assert _comprobar(resultado, "DISTRIBUTIVIDAD_ESCALARES")["estado"] == "NO_CUMPLE"
    assert _comprobar(resultado, "NEUTRO_SUMA")["estado"] == "NO_VERIFICADO"
    assert _comprobar(resultado, "INVERSO_SUMA")["estado"] == "NO_VERIFICADO"


def test_operaciones_no_lineales_transportadas_por_una_biyeccion_polinomica():
    """Certifica el transporte de las operaciones tras sustituir y cancelar monomios."""
    captura = {"conjunto": _generadores((1, 0), (0, 1)), **_operaciones_binarias()}
    captura["suma"][1].append(_termino("2", 1, 0, 1, 0))
    captura["producto_escalar"][1].extend([_termino("1", 2, 2, 0), _termino("-1", 1, 2, 0)])
    resultado = _resolver(captura)
    assert resultado["codigo"] == "ESPACIO_VECTORIAL"
    assert all(comprobacion["estado"] == "CUMPLE" for comprobacion in resultado["comprobaciones"])


def test_conjunto_vacio_tiene_diagnostico_y_no_genera_axiomas():
    """Distingue un conjunto vacío de una entrada inválida o un cálculo inconcluso."""
    captura = _recta_real()
    captura["conjunto"] = _restricciones([[1], [1]], [0, 1])
    resultado = _resolver(captura)
    assert resultado == {
        "estado": "EXITO", "codigo": "CONJUNTO_VACIO", "es_espacio_vectorial": False,
        "dimension_ambiente": 1, "vector_cero": None, "comprobaciones": (),
        "diagnostico": {
            "campo": "conjunto", "coordenada": None, "termino": None,
            "mensaje": "Las restricciones son incompatibles y el conjunto es vacío.",
        },
    }


@pytest.mark.parametrize("termino", [
    _termino("1", -1, 0), _termino("1", True, 0), _termino("1", 1),
    _termino("1", limites.MAXIMO_GRADO_ENTRADA, 1), _termino("1/0", 0, 0),
    _termino("9" * 257, 0, 0), _termino("__import__('os')", 0, 0),
    _termino(0.5, 0, 0), {"coeficiente": "1", "exponentes": [0, 0], "extra": None},
])
def test_captura_rechaza_monomios_invalidos_con_diagnostico_localizado(termino):
    """Ubica el término inválido sin interpretar su contenido como código."""
    captura = _recta_real()
    captura["producto_escalar"][0].append(termino)
    with pytest.raises(ErrorCapturaEspacioVectorial) as error:
        capturar_espacio_vectorial(captura)
    diagnostico = error.value.diagnostico
    assert (diagnostico["campo"], diagnostico["coordenada"], diagnostico["termino"]) == ("producto_escalar", 1, 2)


def test_analisis_revalida_entrada_tipada_antes_de_expandir():
    """Rechaza coeficientes demasiado grandes incluso si llegan por la API tipada."""
    entrada = capturar_espacio_vectorial(_recta_real())
    entrada["suma"][0][0]["coeficiente"] = Fraction(1 << limites.MAXIMO_BITS_ENTRADA)
    resultado = motor.analizar_espacio_vectorial(entrada)
    assert (resultado["estado"], resultado["codigo"], resultado["es_espacio_vectorial"]) == (
        "ERROR", "ENTRADA_INVALIDA", None,
    )
    assert resultado["comprobaciones"] == ()
    assert resultado["diagnostico"]["coordenada"] == 1


def test_captura_normaliza_sin_mutar_la_carga():
    """Construye una representación tipada independiente de los contenedores de captura."""
    captura = _recta_real()
    original = deepcopy(captura)
    entrada = capturar_espacio_vectorial(captura)
    assert captura == original
    assert entrada["suma"][0][0] == {"coeficiente": Fraction(1), "exponentes": (1, 0)}


def test_presupuesto_sin_violacion_no_emite_veredicto(monkeypatch):
    """Conserva el estado inconcluso cuando no queda presupuesto inicial."""
    monkeypatch.setattr(limites, "MAXIMO_OPERACIONES", 0)
    resultado = _resolver(_recta_real())
    assert (resultado["estado"], resultado["codigo"], resultado["es_espacio_vectorial"]) == (
        "ERROR", "LIMITE_ARITMETICO", None,
    )
    assert len(resultado["comprobaciones"]) == 10
    assert all(comprobacion["estado"] == "NO_VERIFICADO" for comprobacion in resultado["comprobaciones"])


def test_preserva_una_violacion_certificada_si_se_agota_el_presupuesto(monkeypatch):
    """Retiene el veredicto negativo cuando se interrumpen axiomas posteriores."""
    monkeypatch.setattr(limites, "MAXIMO_OPERACIONES", 80)
    captura = _recta_real()
    captura["suma"][0][1]["coeficiente"] = "-1"
    resultado = _resolver(captura)
    assert resultado["codigo"] == "NO_ESPACIO_VECTORIAL"
    assert _comprobar(resultado, "CONMUTATIVIDAD_SUMA")["estado"] == "NO_CUMPLE"
    assert _comprobar(resultado, "DISTRIBUTIVIDAD_ESCALARES")["estado"] == "NO_VERIFICADO"


@pytest.mark.parametrize("tipo_error", [CancelledError, OSError])
def test_propagacion_de_cancelacion_y_errores_del_entorno(monkeypatch, tipo_error):
    """Permite al llamador gestionar la cancelación y los errores del entorno."""
    def fallar(_entrada):
        raise tipo_error("Error del entorno")

    monkeypatch.setattr(motor, "caracterizar_conjunto", fallar)
    with pytest.raises(tipo_error):
        _resolver(_recta_real())


def test_error_interno_devuelve_diagnostico_seguro(monkeypatch):
    """Omite los detalles internos en los diagnósticos visibles."""
    def fallar(_entrada):
        raise ArithmeticError("detalle interno")

    monkeypatch.setattr(motor, "caracterizar_conjunto", fallar)
    resultado = _resolver(_recta_real())
    assert resultado["codigo"] == "ERROR_INTERNO"
    assert resultado["es_espacio_vectorial"] is None
    assert len(resultado["comprobaciones"]) == 10
    assert "detalle interno" not in resultado["diagnostico"]["mensaje"]
