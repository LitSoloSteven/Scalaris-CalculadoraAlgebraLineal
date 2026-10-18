"""Contratos de componentes y datos utilizados por las vistas de cálculo."""
from fractions import Fraction
from unittest.mock import Mock

import pytest
from nicegui import ui

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.leontief import ResolutorModeloLeontief
from src.backend.resolutores.operaciones_matrices.captura_matrices import obtener_diccionario_matrices
from src.frontend.componentes.captura_matrices import PanelCapturaMatrices
from src.backend.resolutores.sistemas_lineales.exportacion_ecuaciones import exportar_ecuaciones_desde_datos
from src.frontend.vistas.operaciones_inversas.vista_operaciones_inversas import VistaOperacionesInversas


def test_captura_construye_matriz_con_dimensiones_y_fracciones_exactas():
    """La extracción utiliza la firma real de Matriz y el validador canónico."""
    contenedor = ui.column()
    try:
        with contenedor:
            entradas = [[ui.input(value="1/3"), ui.input(value="-2")]]
        panel = PanelCapturaMatrices()
        panel.matrices = {"A": {"filas": 1, "columnas": 2, "entradas": entradas}}
        matriz = obtener_diccionario_matrices(panel.obtener_datos_crudos())["A"]
        assert isinstance(matriz, Matriz)
        assert (matriz.filas, matriz.columnas) == (1, 2)
        assert matriz.datos == [[Fraction(1, 3), Fraction(-2)]]
    finally:
        contenedor.delete()


def test_exportador_usa_validador_existente_para_coeficientes():
    """Exportar fracciones y signos no invoca una API ausente del validador."""
    assert exportar_ecuaciones_desde_datos([["1/3", "-1"]], ["2"], False) == ["1/3x1 - x2 = 2"]


def test_foco_inversa_emite_el_selector_del_panel_real(monkeypatch):
    """La acción de ir a una celda utiliza una función cliente publicada."""
    ejecutar = Mock()
    monkeypatch.setattr(ui, "run_javascript", ejecutar)
    vista = VistaOperacionesInversas()
    vista.enfocar_celda((0, 1))
    codigo = ejecutar.call_args.args[0]
    assert "window.scalaris" in codigo
    assert "sacudirCelda" in codigo
    assert '"A", 0, 1' in codigo


@pytest.mark.parametrize("demanda", [[Fraction(1, 3), Fraction(2, 3)], [Fraction(-1), Fraction(0)]])
def test_leontief_conserva_demanda_en_contrato_exitoso(demanda):
    """La demanda se expone exacta sin cambiar producción ni claves sectoriales."""
    matriz = Matriz(2, 2)
    resultado = ResolutorModeloLeontief().resolver(matriz, demanda)
    assert resultado["vector_demanda"] == [str(valor) for valor in demanda]
    assert resultado["vector_produccion"] == [str(valor) for valor in demanda]
    assert resultado["hawkins_simon"]["menores_principales"] == [
        {"orden": 1, "determinante": "1", "es_positivo": True},
        {"orden": 2, "determinante": "1", "es_positivo": True},
    ]
    assert all("consumo_intermedio" in sector for sector in resultado["analisis_sectorial"])
    assert all("insumos_intermedios" not in sector for sector in resultado["analisis_sectorial"])
