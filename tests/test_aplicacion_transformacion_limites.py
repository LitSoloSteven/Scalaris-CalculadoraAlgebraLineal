"""Precisión declarada y representación segura de aplicaciones lineales."""
from fractions import Fraction
import json
import math
import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.aplicacion_transformacion import aplicar_vector, matriz_rotacion


@pytest.mark.parametrize("origen", ["matriz", "vector"])
def test_aplicacion_declara_aproximacion_de_cualquiera_de_sus_entradas(origen):
    """Los flotantes de A o de v impiden declarar exacta la aplicación."""
    matriz = matriz_rotacion(45)[0] if origen == "matriz" else Matriz(2, 2, [[1, 0], [0, 1]])
    vector = Matriz(2, 1, [[1], [0]]) if origen == "matriz" else Matriz(2, 1, [[math.sqrt(2)], [0]])
    resultado = aplicar_vector(matriz, vector)
    assert resultado["aproximacion"] is True
    assert all(math.isfinite(valor) for valor in resultado["vector_transformado"]["aproximado"])


def test_cancelacion_de_flotantes_conserva_la_senal_de_aproximacion():
    """Obtener cero no borra la procedencia aproximada de la matriz aplicada."""
    matriz = Matriz(1, 2, [[math.sqrt(2), -math.sqrt(2)]])
    resultado = aplicar_vector(matriz, Matriz(2, 1, [[1], [1]]))
    assert resultado["vector_transformado"]["exacta"] == ["0"]
    assert resultado["aproximacion"] is True


@pytest.mark.parametrize("valor", [10**400, Fraction(10**400), Fraction(-(10**400))])
def test_resultado_exacto_grande_no_depende_de_su_aproximacion_decimal(valor):
    """Un resultado racional finito conserva su texto aunque no quepa en float."""
    resultado = aplicar_vector(Matriz(1, 1, [[valor]]), Matriz(1, 1, [[1]]))
    assert resultado["estado"] == "EXITO" and resultado["aproximacion"] is False
    assert resultado["vector_transformado"] == {"exacta": [str(valor)], "aproximado": [None]}
    assert resultado["vector_original"] == {"exacta": ["1"], "aproximado": [1.0]}
    assert str(valor) in resultado["pasos"][0]["detalle_latex"]
    json.dumps(resultado["vector_transformado"], allow_nan=False)


def test_vector_original_grande_puede_transformarse_en_cero():
    """La serialización de la entrada no impide publicar un resultado representable."""
    grande = Fraction(10**400)
    resultado = aplicar_vector(Matriz(1, 1, [[0]]), Matriz(1, 1, [[grande]]))
    assert resultado["vector_original"] == {"exacta": [str(grande)], "aproximado": [None]}
    assert resultado["vector_transformado"] == {"exacta": ["0"], "aproximado": [0.0]}
    assert resultado["aproximacion"] is False


@pytest.mark.parametrize("valor", [10**400, 1.7e308])
def test_producto_de_entradas_finitas_no_desborda_por_mezclar_flotantes(valor):
    """La mezcla con un flotante finito conserva un resultado racional representable en texto."""
    matriz, vector = Matriz(1, 1, [[valor]]), Matriz(1, 1, [[math.sqrt(2)]])
    esperado = Fraction(matriz.obtener(0, 0)) * Fraction(vector.obtener(0, 0))
    resultado = aplicar_vector(matriz, vector)
    assert resultado["estado"] == "EXITO" and resultado["aproximacion"] is True
    assert resultado["vector_transformado"] == {"exacta": [str(esperado)], "aproximado": [None]}
    assert matriz.obtener(0, 0) == valor and vector.obtener(0, 0) == math.sqrt(2)


def test_productos_flotantes_grandes_pueden_cancelarse_antes_de_serializar():
    """El reintento racional conserva la cancelación aunque cada término desborde float."""
    matriz = Matriz(1, 2, [[10**400, 10**400]])
    vector = Matriz(2, 1, [[math.sqrt(2)], [-math.sqrt(2)]])
    resultado = aplicar_vector(matriz, vector)
    assert resultado["aproximacion"] is True
    assert resultado["vector_transformado"] == {"exacta": ["0"], "aproximado": [0.0]}


@pytest.mark.parametrize("grados", [0, 90, 180, 270])
def test_rotaciones_exactas_siguen_sin_marcar_aproximacion(grados):
    """Los constructores exactos mantienen la precisión del contrato anterior."""
    matriz, exacta = matriz_rotacion(grados)
    resultado = aplicar_vector(matriz, Matriz(2, 1, [[Fraction(1, 3)], [Fraction(2, 3)]]))
    assert exacta and resultado["aproximacion"] is False


@pytest.mark.parametrize("valor", [float("inf"), float("-inf"), float("nan")])
@pytest.mark.parametrize("origen", ["matriz", "vector"])
def test_entradas_no_finitas_se_rechazan_antes_de_operar(valor, origen):
    """Los valores sin representación real finita producen un error de dominio."""
    matriz = Matriz(1, 1, [[valor if origen == "matriz" else 1]])
    vector = Matriz(1, 1, [[valor if origen == "vector" else 1]])
    with pytest.raises(ValueError, match="finitos"):
        aplicar_vector(matriz, vector)
