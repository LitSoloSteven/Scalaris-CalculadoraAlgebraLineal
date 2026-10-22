"""Representaciones únicas, dependientes e incompatibles de vectores."""
from fractions import Fraction
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal


def test_representacion_unica_con_base():
    """Una base canónica determina los coeficientes enteros exactos."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[3], [2]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "UNICA"
    assert resultado["es_combinacion_lineal"] is True
    assert resultado["coeficientes"] == [Fraction(3), Fraction(2)]
    assert resultado["coeficientes_texto"] == ["3", "2"]
    assert resultado["parametros_libres"] == []


def test_representacion_unica_con_fracciones():
    """La combinación obtiene coeficientes racionales sin aproximarlos."""
    v1 = Matriz(2, 1, [[2], [0]])
    v2 = Matriz(2, 1, [[0], [3]])
    objetivo = Matriz(2, 1, [[1], [1]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "UNICA"
    assert resultado["coeficientes"] == [Fraction(1, 2), Fraction(1, 3)]
    assert resultado["coeficientes_texto"] == ["1/2", "1/3"]


def test_representacion_unica_conserva_denominador_grande():
    """El coeficiente con denominador mayor que mil permanece exacto."""
    v1 = Matriz(2, 1, [[1001], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[1], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "UNICA"
    assert resultado["coeficientes"][0] == Fraction(1, 1001)


def test_representacion_unica_en_tres_dimensiones():
    """Dos vectores tridimensionales representan el objetivo indicado."""
    v1 = Matriz(3, 1, [[1], [-2], [-5]])
    v2 = Matriz(3, 1, [[2], [5], [6]])
    objetivo = Matriz(3, 1, [[7], [4], [-3]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "UNICA"
    assert resultado["coeficientes"] == [Fraction(3), Fraction(2)]


def test_vectores_dependientes_producen_representaciones_infinitas():
    """Los vectores proporcionales conservan un coeficiente libre."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(2, 1, [[2], [4]])
    objetivo = Matriz(2, 1, [[3], [6]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "INFINITA"
    assert resultado["es_combinacion_lineal"] is True
    assert resultado["coeficientes"] is None
    assert resultado["solucion_parametrica"] is not None
    assert resultado["parametros_libres"] == ["c_2"]
    assert "infinitas" in resultado["mensaje"].lower()


def test_representacion_infinita_no_incluye_verificacion_unica():
    """La verificación de coeficientes únicos no se aplica a familias."""
    v1 = Matriz(2, 1, [[1], [2]])
    v2 = Matriz(2, 1, [[2], [4]])
    objetivo = Matriz(2, 1, [[3], [6]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["paso_verificacion"] is None


def test_objetivo_fuera_del_espacio_generado_no_tiene_solucion():
    """Un objetivo fuera del eje generado no admite coeficientes."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[2], [0]])
    objetivo = Matriz(2, 1, [[0], [1]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "SIN_SOLUCION"
    assert resultado["es_combinacion_lineal"] is False
    assert resultado["coeficientes"] is None
    assert resultado["paso_verificacion"] is None


def test_objetivo_fuera_del_plano_no_tiene_solucion():
    """Tres vectores coplanares no generan un objetivo exterior."""
    v1 = Matriz(3, 1, [[1], [0], [0]])
    v2 = Matriz(3, 1, [[0], [1], [0]])
    v3 = Matriz(3, 1, [[1], [1], [0]])
    objetivo = Matriz(3, 1, [[0], [0], [1]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2, v3])
    assert resultado["estado"] == "SIN_SOLUCION"


def test_objetivo_nulo_tiene_coeficientes_nulos_con_base():
    """Una base representa el vector nulo con coeficientes cero."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    objetivo = Matriz(2, 1, [[0], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "UNICA"
    assert resultado["coeficientes"] == [Fraction(0), Fraction(0)]


def test_objetivo_nulo_tiene_familia_con_vectores_dependientes():
    """La dependencia produce infinitas representaciones del vector nulo."""
    v1 = Matriz(2, 1, [[1], [1]])
    v2 = Matriz(2, 1, [[2], [2]])
    objetivo = Matriz(2, 1, [[0], [0]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2])
    assert resultado["estado"] == "INFINITA"


def test_columnas_libres_determinan_parametros_exactos():
    """El tercer vector dependiente aporta el tercer coeficiente libre."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    v3 = Matriz(2, 1, [[1], [1]])
    objetivo = Matriz(2, 1, [[2], [3]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [v1, v2, v3])
    assert resultado["estado"] == "INFINITA"
    assert resultado["parametros_libres"] == ["c_3"]


def test_columnas_libres_respetan_nombres_personalizados():
    """El nombre del parámetro libre procede del consumidor."""
    v1 = Matriz(2, 1, [[1], [0]])
    v2 = Matriz(2, 1, [[0], [1]])
    v3 = Matriz(2, 1, [[1], [1]])
    objetivo = Matriz(2, 1, [[2], [3]])
    resultado = ResolutorCombinacionLineal().resolver(
        objetivo, [v1, v2, v3], nombres_variables=["alpha", "beta", "gamma"])
    assert resultado["parametros_libres"] == ["gamma"]
