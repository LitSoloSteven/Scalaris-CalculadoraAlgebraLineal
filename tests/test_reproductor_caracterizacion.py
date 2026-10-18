"""Fija las salidas actuales del renderizador y el controlador de inversa."""

import json
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.componentes.reproductor_pasos import (
    formatear_decimal,
    formatear_valor,
    html_sugerencia_tipo,
    html_tabla_aumentada,
    html_tabla_matriz,
)


TABLA_MATRIZ = '<div class="inversa-desplazamiento"><table class="inversa-tabla"><thead><tr><th class=\'fila-etiqueta\'></th><th>C1</th><th>C2</th></tr></thead><tbody><tr><th class=\'fila-etiqueta\'>F1</th><td title="≈ 0.5"><span class="inversa-fraccion"><span>1</span><span>2</span></span></td><td>-2</td></tr><tr><th class=\'fila-etiqueta\'>F2</th><td>3</td><td title="≈ -1.3333">−<span class="inversa-fraccion"><span>4</span><span>3</span></span></td></tr></tbody></table></div>'
TABLA_AUMENTADA = '<div class="inversa-desplazamiento"><table class="inversa-tabla"><thead><tr><th class=\'fila-etiqueta\'></th><th>1</th><th>2</th><th class=\'separador-izquierdo\'>1</th><th>2</th></tr></thead><tbody><tr><th class=\'fila-etiqueta\'>F1</th><td title="≈ 0.5"><span class="inversa-fraccion"><span>1</span><span>2</span></span></td><td>-2</td><td class="separador-izquierdo">1</td><td>0</td></tr><tr><th class=\'fila-etiqueta\'>F2</th><td>3</td><td title="≈ -1.3333">−<span class="inversa-fraccion"><span>4</span><span>3</span></span></td><td class="separador-izquierdo">0</td><td>1</td></tr></tbody></table></div>'


def _html_aumentado(**opciones):
    """Renderiza la matriz fija de caracterización con las opciones indicadas."""
    matriz = Matriz(2, 4, [[Fraction(1, 2), -2, 1, 0], [3, Fraction(-4, 3), 0, 1]])
    return html_tabla_aumentada(matriz, 2, opciones={**opciones})


def _resumen_controlador(datos):
    """Extrae del resultado los campos contractuales independientes del tiempo."""
    resultado = ControladorOperacionesInversas.procesar_inversa(
        json.dumps({"dimension": len(datos), "datos": datos})
    )
    pasos = [
        {campo: paso[campo] for campo in ("tipo", "indice_grupo", "explicacion")}
        for paso in resultado["pasos"]
    ]
    return pasos, resultado["grupos"], resultado["estadisticas"]


def test_formateadores_y_tabla_matriz_conservan_su_html():
    """Fija la salida literal de valores, decimales y la tabla de matriz."""
    matriz = Matriz(2, 2, [[Fraction(1, 2), -2], [3, Fraction(-4, 3)]])
    assert formatear_valor(Fraction(-3, 4), apilada=True) == '−<span class="inversa-fraccion"><span>3</span><span>4</span></span>'
    assert formatear_valor(Fraction(4, 1)) == "4"
    assert formatear_decimal(Fraction(1, 3)) == "0.3333"
    assert html_tabla_matriz(matriz) == TABLA_MATRIZ


def test_tabla_aumentada_conserva_resaltados_y_bloque_final():
    """Fija el HTML base y los resaltados de cambio, pivote, intercambio y resultado."""
    assert _html_aumentado() == TABLA_AUMENTADA
    assert _html_aumentado(filas_cambiadas=(1,)) == TABLA_AUMENTADA.replace(
        "<tr><th class=\'fila-etiqueta\'>F2", '<tr class="fila-modificada"><th class=\'fila-etiqueta\'>F2'
    )
    assert _html_aumentado(pivote=(0, 0)) == TABLA_AUMENTADA.replace(
        "<td title=\"≈ 0.5\">", '<td class="celda-pivote" title="≈ 0.5">', 1
    )
    tabla_intercambiada = TABLA_AUMENTADA.replace(
        "<tr><th class=\'fila-etiqueta\'>F1", '<tr class="fila-intercambio"><th class=\'fila-etiqueta\'>F1'
    ).replace(
        "<tr><th class=\'fila-etiqueta\'>F2", '<tr class="fila-intercambio"><th class=\'fila-etiqueta\'>F2'
    )
    assert _html_aumentado(filas_intercambio=(0, 1)) == tabla_intercambiada
    final = TABLA_AUMENTADA.replace('class="inversa-tabla"', 'class="inversa-tabla es-resultado"')
    final = final.replace('<td class="separador-izquierdo">1', '<td class="separador-izquierdo bloque-resultado">1')
    final = final.replace('<td class="separador-izquierdo">0', '<td class="separador-izquierdo bloque-resultado">0')
    final = final.replace('<td>0</td>', '<td class="bloque-resultado">0</td>')
    final = final.replace('<td>1</td>', '<td class="bloque-resultado">1</td>')
    assert _html_aumentado(bloque_resultado=True) == final


def test_indicador_de_intercambio_conserva_su_html():
    """Fija el HTML del chip actual de intercambio de filas."""
    assert html_sugerencia_tipo("intercambio") == '<span class="pasos-distintivo-tipo pasos-etiqueta-intercambio"><span class="material-icons">swap_vert</span>Intercambio</span>'


def test_controlador_inversa_dos_por_dos_conserva_pasos_grupos_y_estadisticas():
    """Fija la secuencia completa que devuelve el controlador para una matriz 2x2."""
    pasos, grupos, estadisticas = _resumen_controlador([[1, 2], [3, 4]])
    assert [(paso["tipo"], paso["indice_grupo"]) for paso in pasos] == [
        ("inicial", 0), ("intercambio", 1), ("pivote", 1), ("eliminacion", 1),
        ("pivote", 2), ("eliminacion", 2), ("normalizacion", 3), ("normalizacion", 3),
    ]
    assert [paso["explicacion"] for paso in pasos] == [
        "Construimos la matriz aumentada [A | I]: A a la izquierda y la identidad I a la derecha. Meta: aplicar operaciones elementales de fila hasta obtener [I | A⁻¹].",
        "Intercambiamos la fila 1 con la fila 2 para que el pivote sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). Intercambiar filas no altera el resultado.",
        "Pivote: fila 1, columna 1 (valor 3). Usaremos esta fila para anular el resto de la columna 1.",
        "Hacemos 0 la entrada de la fila 2 en la columna 1: Fila 2 = Fila 2 − (1/3) · Fila 1. La operación afecta la fila completa, es decir, los dos bloques a la vez.",
        "Pivote: fila 2, columna 2 (valor 2/3). Usaremos esta fila para anular el resto de la columna 2.",
        "Hacemos 0 la entrada de la fila 1 en la columna 2: Fila 1 = Fila 1 − (6) · Fila 2. La operación afecta la fila completa, es decir, los dos bloques a la vez.",
        "Dividimos la fila 1 entre 3 para que su pivote valga 1 y la diagonal del bloque izquierdo quede igual a la identidad.",
        "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque derecho es A⁻¹. Dividimos la fila 2 entre 2/3 para que su pivote valga 1 y la diagonal del bloque izquierdo quede igual a la identidad.",
    ]
    assert grupos == [
        {"titulo": "Matriz inicial [A | I]", "resumen": "1 operación", "tipo": "inicial", "indices_pasos": [0]},
        {"titulo": "Columna 1 · pivote 3 en fila 1 · con intercambio", "resumen": "3 operaciones", "tipo": "columna", "indices_pasos": [1, 2, 3]},
        {"titulo": "Columna 2 · pivote 2/3 en fila 2", "resumen": "2 operaciones", "tipo": "columna", "indices_pasos": [4, 5]},
        {"titulo": "Normalización: cada pivote pasa a 1", "resumen": "2 operaciones", "tipo": "normalizacion", "indices_pasos": [6, 7]},
    ]
    assert estadisticas == {"total": 8, "pivotes": 2, "intercambios": 1, "eliminaciones": 2, "normalizaciones": 2}


def test_controlador_inversa_tres_por_tres_conserva_intercambio():
    """Fija la salida del controlador para una matriz 3x3 que requiere intercambio."""
    pasos, grupos, estadisticas = _resumen_controlador([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    assert [(paso["tipo"], paso["indice_grupo"]) for paso in pasos] == [
        ("inicial", 0), ("intercambio", 1), ("pivote", 1), ("pivote", 2), ("pivote", 3),
    ]
    assert [paso["explicacion"] for paso in pasos] == [
        "Construimos la matriz aumentada [A | I]: A a la izquierda y la identidad I a la derecha. Meta: aplicar operaciones elementales de fila hasta obtener [I | A⁻¹].",
        "Intercambiamos la fila 1 con la fila 2 para que el pivote sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). Intercambiar filas no altera el resultado.",
        "Pivote: fila 1, columna 1 (valor 1). Usaremos esta fila para anular el resto de la columna 1.",
        "Pivote: fila 2, columna 2 (valor 1). Usaremos esta fila para anular el resto de la columna 2.",
        "Resultado: el bloque izquierdo ya es I, por lo tanto el bloque derecho es A⁻¹. Pivote: fila 3, columna 3 (valor 1). Usaremos esta fila para anular el resto de la columna 3.",
    ]
    assert grupos == [
        {"titulo": "Matriz inicial [A | I]", "resumen": "1 operación", "tipo": "inicial", "indices_pasos": [0]},
        {"titulo": "Columna 1 · pivote 1 en fila 1 · con intercambio", "resumen": "2 operaciones", "tipo": "columna", "indices_pasos": [1, 2]},
        {"titulo": "Columna 2 · pivote 1 en fila 2", "resumen": "1 operación", "tipo": "columna", "indices_pasos": [3]},
        {"titulo": "Columna 3 · pivote 1 en fila 3", "resumen": "1 operación", "tipo": "columna", "indices_pasos": [4]},
    ]
    assert estadisticas == {"total": 5, "pivotes": 3, "intercambios": 1, "eliminaciones": 0, "normalizaciones": 0}
