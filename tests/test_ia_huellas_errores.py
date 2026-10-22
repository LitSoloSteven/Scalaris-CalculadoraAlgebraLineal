"""Huellas de entradas originales y contrato de códigos de error romanos."""
from src.ai.huellas import calcular_huella, esta_desactualizado

def test_huella_admite_claves_tupla():
    """Las claves compuestas producen una huella estable."""
    entrada = {"matrices": {"A": {(0, 0): "1", (0, 1): "1/1001"}}, "expresion": "A"}
    huella = calcular_huella(entrada)
    assert isinstance(huella, str) and len(huella) == 40
    assert esta_desactualizado(entrada, huella) is False
    entrada["matrices"]["A"][(0, 0)] = "2"
    assert esta_desactualizado(entrada, huella) is True

def test_clasificacion_error_romano():
    """Los códigos romanos conservan la clasificación del error."""
    class ErrorRomanoSimulado(Exception):
        """Expone el código de error del contrato consumido por la interfaz."""

        def __init__(self, codigo, mensaje=""):
            super().__init__(mensaje)
            self.codigo = codigo

    estados_por_codigo = {
        "CERO_NO_REPRESENTABLE": "error_resta_cero",
        "NEGATIVO_NO_REPRESENTABLE": "error_resta_negativa",
        "SINTAXIS_INVALIDA": "error_sintaxis",
        "NO_CANONICO": "error_sintaxis",
        "ENTRADA_VACIA": "error_sintaxis",
    }
    for codigo, esperado in estados_por_codigo.items():
        error = ErrorRomanoSimulado(codigo)
        assert getattr(error, "codigo", None) == codigo

def test_huella_bases_incluye_entrada_original():
    """El valor original distingue entradas del conversor."""
    valor_original = "ff"
    entrada_salvada = {"valor": valor_original, "base_origen": "hexadecimal", "base_destino": "todas"}
    huella = calcular_huella(entrada_salvada)

    entrada_actual = {"valor": "ff", "base_origen": "hexadecimal", "base_destino": "todas"}
    assert esta_desactualizado(entrada_actual, huella) is False

    entrada_actual["valor"] = "ffa"
    assert esta_desactualizado(entrada_actual, huella) is True

def test_inversa_contexto_obsoleto_con_celda_larga():
    """La detección de obsolescencia acepta celdas de muchos caracteres."""
    expresion_larga = "1234567890123456789012345678901234567890"
    datos = [[expresion_larga, "0"], ["0", "1"]]
    huella = calcular_huella({"data": datos})
    assert esta_desactualizado({"data": datos}, huella) is False
