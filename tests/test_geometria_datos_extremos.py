"""Casos límite de captura, transferencia, muestreo y representación geométrica."""
from fractions import Fraction
import json
import pytest
from nicegui import ui

from src.backend.geometria.muestreo import extremos_recta, superficie_plano
from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.geometria.transferencia import validar_transferencia_escena
from src.frontend.controladores.geometria import ControladorGeometria
from src.frontend.controladores.geometria.captura import construir_carga_sistema, construir_carga_vectores
from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos, construir_figura_combinacion
from src.frontend.vistas.geometria.vista_geometria import VistaGeometria


def test_entradas_vacias_conservan_estado_inicial():
    """Una cuadrícula o familia sin datos no invoca un cálculo."""
    assert construir_carga_sistema([], [], True) is None
    assert construir_carga_sistema([['0', '0']], ['0'], True) is None
    assert construir_carga_vectores('vectores', 2, []) is None
    assert construir_carga_vectores('combinacion', 3, [{}, {}]) is None


def test_una_ecuacion_conserva_fracciones_exactas():
    """La captura no altera el término ni los coeficientes antes del controlador."""
    carga = construir_carga_sistema([['1/3', '0']], ['2/7'], False)
    assert carga == {'matrix_A': [['1/3', '0']], 'vector_b': ['2/7']}
    resultado = ControladorGeometria.procesar_rectas_planos(json.dumps(carga))
    assert resultado['status'] == 'OK'
    assert resultado['solution_status'] == 'INFINITE_SOLUTIONS'
    assert resultado['equations'][0]['coeffs_exact'] == ['1/3', '0']
    assert resultado['set']['point_exact'][0] == str(Fraction(6, 7))


def test_muchas_ecuaciones_generan_todas_las_trazas():
    """Diez ecuaciones no se omiten y la solución sigue siendo exacta."""
    matriz = [[str(i), '1'] for i in range(1, 11)]
    vector = [str(i + 2) for i in range(1, 11)]
    carga = construir_carga_sistema(matriz, vector, False)
    resultado = ControladorGeometria.procesar_rectas_planos(json.dumps(carga))
    assert resultado['status'] == 'OK'
    assert resultado['set']['point_exact'] == ['1', '2']
    figura = construir_figura_rectas_planos(resultado)
    assert sum(traza.name.startswith('Ecuación') for traza in figura.data) == 10
    figura.to_json()


def test_valor_largo_conserva_texto_y_controlador_rechaza_exceso():
    """La captura mantiene los dígitos; el dominio limita la entrada excesiva."""
    numero = '9' * 80
    carga = construir_carga_vectores('vectores', 2, [{0: numero}, {1: '1'}])
    assert carga['vectors'][0]['data'][0] == numero
    resultado = ControladorGeometria.procesar_vectores(json.dumps(carga))
    assert resultado['status'] == 'OK'
    assert resultado['u']['exact'][0] == numero
    carga['vectors'][0]['data'][0] = '9' * (LONGITUD_MAXIMA_CADENA_NUMERO + 1)
    resultado = ControladorGeometria.procesar_vectores(json.dumps(carga))
    assert resultado['status'] == 'ERROR'
    assert resultado['error_cell'] == {'kind': 'vec', 'name': 'u', 'index': 0}


@pytest.mark.parametrize('escena,cantidad', [('vectores', 1), ('vectores', 3), ('combinacion', 1), ('combinacion', 6)])
def test_cantidad_fuera_del_limite_se_valida_en_backend(escena, cantidad):
    """Las familias incompatibles se rechazan por las reglas de escena del dominio."""
    assert validar_transferencia_escena(escena, escena, [[1, 2]] * cantidad) is not None


@pytest.mark.parametrize('escena,cantidad', [('vectores', 2), ('combinacion', 2), ('combinacion', 5)])
def test_transferencias_en_limites_aceptadas(escena, cantidad):
    """Las cantidades mínima y máxima permitidas siguen siendo válidas."""
    assert validar_transferencia_escena(escena, escena, [[1, 2]] * cantidad) is None
    assert validar_transferencia_escena(escena, 'otra', [[1, 2]] * cantidad) is not None


@pytest.mark.parametrize('coeficientes', [[2, 0, 0], [0, 3, 0], [0, 0, 4], [1, 2, 3]])
def test_superficies_satisfacen_el_plano_en_todos_los_ejes(coeficientes):
    """Cada punto muestreado verifica la misma ecuación del plano original."""
    horizontal, vertical, profundidad = superficie_plano(coeficientes, 6, [-5, 5])
    assert len(horizontal) == len(vertical) == len(profundidad) == 12
    for fila in range(12):
        for columna in range(12):
            punto = [horizontal[fila][columna], vertical[fila][columna], profundidad[fila][columna]]
            assert sum(coeficiente * valor for coeficiente, valor in zip(coeficientes, punto)) == pytest.approx(6)


def test_recta_vertical_y_plano_degenerado():
    """Los casos degenerados mantienen el criterio gráfico de tolerancia."""
    assert extremos_recta([2, 0], 6, [-5, 5]) == ([3, 3], [-5, 5])
    assert extremos_recta([0, 0], 6, [-5, 5]) is None
    assert superficie_plano([0, 0, 0], 0, [-5, 5]) is None


@pytest.mark.parametrize('escena', ['vectores', 'combinacion'])
def test_controles_reales_crean_la_familia_minima(escena):
    """La vista usa la API real del componente y genera al menos dos vectores."""
    vista = VistaGeometria()
    vista.contenedor_controles = ui.column()
    vista._construir_controles(escena)
    panel = vista.panel_vectores if escena == 'vectores' else vista.panel_combinacion
    assert len(panel.vectors) == 2
    assert panel.on_data_change == vista._notificar_cambio_datos
    vista.contenedor_controles.delete()


def test_representacion_vacia_no_genera_trazas_ficticias():
    """Los constructores admiten ausencia de elementos sin inventar resultados."""
    assert not construir_figura_rectas_planos({'equations': [], 'set': None}).data
    assert not construir_figura_combinacion({'vectors': [], 'chain': [], 'b': {}}).data
