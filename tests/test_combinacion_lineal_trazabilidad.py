"""Contrato, pasos, verificación y mensajes de combinación lineal."""
import re
from fractions import Fraction
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal

_CLAVES_RESPUESTA = {
    "estado", "es_combinacion_lineal", "coeficientes", "coeficientes_texto",
    "solucion_parametrica", "parametros_libres", "mensaje", "pasos",
    "pasos_sustitucion_regresiva", "paso_verificacion",
}


def test_combinacion_unica_devuelve_pasos_gauss():
    """Los pasos conservan la matriz del planteamiento."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert len(resultado["pasos"]) > 0
    assert resultado["pasos"][0]["matriz"] is not None


def test_combinacion_unica_incluye_sustitucion_regresiva():
    """La solución única conserva los pasos de sustitución."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert len(resultado["pasos_sustitucion_regresiva"]) > 0


def test_verificacion_unica_incluye_comprobacion_y_coeficientes():
    """La comprobación identifica el coeficiente y confirma coincidencia."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["paso_verificacion"] is not None
    assert resultado["paso_verificacion"]["coincide"] is True
    assert "Comprobación" in resultado["paso_verificacion"]["descripcion"]
    assert "c_1" in resultado["paso_verificacion"]["detalle_latex"]


def test_verificacion_unica_muestra_marca_de_coincidencia():
    """El detalle LaTeX muestra la marca cuando coincide el objetivo."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert "\\checkmark" in resultado["paso_verificacion"]["detalle_latex"]
    assert resultado["paso_verificacion"]["coincide"] is True


def test_contrato_completo_en_combinacion_exitosa():
    """La respuesta exitosa contiene todas las claves contratadas."""
    v1 = Matriz(2, 1, [[1], [0]])
    objetivo = Matriz(2, 1, [[3], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1])
    assert _CLAVES_RESPUESTA.issubset(resultado.keys())


def test_contrato_completo_en_combinacion_erronea():
    """El error conserva la misma estructura del contrato."""
    objetivo = Matriz(2, 1, [[1], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [])
    assert _CLAVES_RESPUESTA.issubset(resultado.keys())


def test_sustitucion_regresiva_utiliza_nombres_personalizados():
    """Los pasos de sustitución incorporan los nombres recibidos."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2], nombres_variables=["alpha", "beta"])
    texto = " ".join(resultado["pasos_sustitucion_regresiva"])
    assert "alpha" in texto or "beta" in texto


def test_combinacion_delega_pasos_matriciales_en_gauss():
    """Los pasos delegados incluyen matriz y descripción de operación."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert len(resultado["pasos_gauss"]) > 0
    for paso in resultado["pasos_gauss"]:
        assert paso.get("matriz") is not None
        assert paso.get("descripcion")


def test_verificacion_latex_separa_filas_sin_comas():
    """Las matrices de comprobación usan separadores de fila válidos."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    detalle = resultado["paso_verificacion"]["detalle_latex"]
    assert "\\\\" in detalle
    matrices = re.findall(r"\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}", detalle)
    assert len(matrices) >= 2
    for contenido in matrices:
        assert "," not in contenido


def test_mensaje_singular_para_combinacion_unica():
    """Una combinación de un solo vector utiliza el singular."""
    v1 = Matriz(3, 1, [[2], [4], [6]])
    objetivo = Matriz(3, 1, [[6], [12], [18]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1])
    assert resultado["estado"] == "UNICA"
    assert "del vector" in resultado["mensaje"]
    assert "de los 1 vectores" not in resultado["mensaje"]


def test_mensaje_singular_para_combinacion_sin_solucion():
    """La incompatibilidad de un solo vector utiliza el singular."""
    v1 = Matriz(3, 1, [[2], [4], [6]])
    objetivo = Matriz(3, 1, [[1], [0], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1])
    assert resultado["estado"] == "SIN_SOLUCION"
    assert "del vector" in resultado["mensaje"]
    assert "de los 1 vectores" not in resultado["mensaje"]


def test_mensaje_singular_para_combinacion_infinita():
    """La familia generada por un solo vector utiliza el singular."""
    v1 = Matriz(3, 1, [[0], [0], [0]])
    objetivo = Matriz(3, 1, [[0], [0], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1])
    assert resultado["estado"] == "INFINITA"
    assert "del vector" in resultado["mensaje"]
    assert "de los 1 vectores" not in resultado["mensaje"]


def test_combinacion_resuelve_sin_dependencia_de_operaciones_vectoriales():
    """El resolutor de combinación obtiene por sí mismo los coeficientes."""
    from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [4]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "UNICA"
    assert resultado["coeficientes"] == [Fraction(3), Fraction(4)]
