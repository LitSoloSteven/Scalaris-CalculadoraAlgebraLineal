"""Fronteras existentes de dibujo y nuevas guardas de entrada para servicios matematicos."""
from unittest.mock import Mock

import pytest

from src.backend.constantes import DIMENSION_MAXIMA_COFACTORES, LONGITUD_MAXIMA_NOMBRE_MODELO
from src.backend.geometria.muestreo import extremos_recta, TOLERANCIA_CERO_GRAFICO
from src.backend.geometria.recorte import recortar_recta_a_caja
from src.backend.modelos.construcciones import identidad
from src.backend.resolutores.operaciones_matrices.captura_modelos import validar_nombres
from src.backend.resolutores.operaciones_matrices.determinante import ResolutorDeterminante


def test_recorte_y_muestreo_conservan_convenciones_de_frontera():
    """La tolerancia grafica no cambia las convenciones historicas de recorte y muestreo."""
    assert extremos_recta([0, TOLERANCIA_CERO_GRAFICO], 0, [-1, 1]) is None
    assert recortar_recta_a_caja([0], [TOLERANCIA_CERO_GRAFICO], 1) == (-1e12, 1e12)
    assert recortar_recta_a_caja([0], [TOLERANCIA_CERO_GRAFICO / 2], 1) is None


def test_laplace_rechaza_exceso_antes_de_la_recursion(monkeypatch):
    """La guarda de cofactores limita el presupuesto antes de invocar el calculo recursivo."""
    recursion = Mock(side_effect=AssertionError("No debe iniciarse la recursion."))
    monkeypatch.setattr(ResolutorDeterminante, "_determinante_recursivo", recursion)
    with pytest.raises(ValueError, match="cofactores"):
        ResolutorDeterminante.resolver_laplace(identidad(DIMENSION_MAXIMA_COFACTORES + 1))
    recursion.assert_not_called()


def test_nombres_largos_admitidos_conservan_texto_literal():
    """La validacion conserva nombres literales de usuario hasta el presupuesto establecido."""
    nombres = ["<sector>&" + "n" * (LONGITUD_MAXIMA_NOMBRE_MODELO - 9)]
    assert validar_nombres(nombres, "sectores") == nombres


def test_nombre_por_encima_del_presupuesto_se_rechaza():
    """La validacion rechaza nombres de longitud superior al presupuesto con ValueError."""
    with pytest.raises(ValueError, match="caracteres"):
        validar_nombres(["n" * (LONGITUD_MAXIMA_NOMBRE_MODELO + 1)], "sectores")
