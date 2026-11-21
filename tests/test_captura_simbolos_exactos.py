"""Comprueba la notación tipográfica en números exactos, bases y sistemas lineales."""
from fractions import Fraction

import pytest

from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.geometria.preparacion.captura import parsear_par_vectores
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.celdas_exactas import parsear_celda_exacta
from src.backend.resolutores.sistemas_lineales.captura_ecuaciones import preparar_ecuaciones
from src.backend.resolutores.sistemas_lineales.vista_previa import preparar_vista_previa
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.backend.utilidades.validacion.analizadores import AnalizadorSistema
from src.backend.utilidades.validacion.reglas_dominio import validar_entrada_base
from src.frontend.componentes.portapapeles_matricial import filtrar_matriz_numerica
from src.frontend.controladores.sistemas_lineales.presentacion_solucion import formatear_elemento_solucion


@pytest.mark.parametrize(("texto", "razon"), [
    ("−3÷5", "-3/5"), ("2⁄3", "2/3"), ("3∕4", "3/4"), ("−12.5‰", "-1/80"),
    ("¼", "1/4"), ("½", "1/2"), ("¾", "3/4"), ("⅐", "1/7"), ("⅑", "1/9"), ("⅒", "1/10"),
    ("⅓", "1/3"), ("⅔", "2/3"), ("⅕", "1/5"), ("⅖", "2/5"), ("⅗", "3/5"), ("⅘", "4/5"),
    ("⅙", "1/6"), ("⅚", "5/6"), ("⅛", "1/8"), ("⅜", "3/8"), ("⅝", "5/8"), ("⅞", "7/8"), ("↉", "0"),
])
def test_celdas_exactas_conservan_literales_unicode(texto, razon):
    """El pegado, la captura de celda y el modelo conservan el valor exacto."""
    datos = filtrar_matriz_numerica([[texto]])
    assert datos == [[texto]]
    assert parsear_celda_exacta(texto, "A[1, 1]") == Fraction(razon)
    assert Matriz(1, 1, datos).obtener(0, 0) == Fraction(razon)


@pytest.mark.parametrize(("texto", "mensaje"), [
    ("1÷0", "División por cero"), ("1‰‰", "fracción válida"), ("2½", "fracción válida"),
    ("1e2", "científica"), ("1" * LONGITUD_MAXIMA_CADENA_NUMERO + "‰", "longitud máxima"),
])
def test_celda_exacta_rechaza_literales_invalidos(texto, mensaje):
    """El dominio conserva el rechazo granular y los límites de captura."""
    with pytest.raises(ValueError, match=mensaje):
        parsear_celda_exacta(texto, "A[1, 1]")


def test_visualizador_recibe_coordenadas_exactas():
    """La captura geométrica de vectores interpreta la misma notación de celdas."""
    datos, error = parsear_par_vectores([["−½", "250‰"], ["2÷3", "0"]])
    assert error is None
    assert datos == [[Fraction(-1, 2), Fraction(1, 4)], [Fraction(2, 3), Fraction(0)]]


@pytest.mark.parametrize(("metodo", "base", "texto"), [
    ("decimal_a_todo", 10, "−42"), ("binario_a_todo", 2, "−0b101010"),
    ("octal_a_todo", 8, "−0o52"), ("hexadecimal_a_todo", 16, "−0x2a"),
])
def test_conversor_admite_menos_tipografico(metodo, base, texto):
    """La validación y el conversor aceptan el signo con o sin prefijo de base."""
    assert validar_entrada_base(texto, base)[0]
    resultado = getattr(ConversorBases(), metodo)(texto)
    assert resultado["decimal"] == "-42"
    assert not validar_entrada_base("−-1", base)[0]


@pytest.mark.parametrize("operador", ["×", "·", "⋅", "∙"])
def test_productos_lineales_con_literales_exactos(operador):
    """Admite el escalar a ambos lados de la incógnita y traslada la constante."""
    texto = f"−½ {operador} α₂ + Β {operador} 3 + 250‰ = 3∕4"
    resultado = preparar_ecuaciones([texto])
    assert resultado["variables"] == ["α2", "Β"]
    assert resultado["matriz_a"] == [["-1/2", "3"]]
    assert resultado["vector_b"] == ["1/2"]


@pytest.mark.parametrize("division", ["÷", "⁄", "∕"])
def test_division_y_subindices_en_vista_previa(division):
    """La vista previa usa la misma identidad para los índices ASCII y Unicode."""
    texto = f"β₁₂ {division} 2 + β12 = 1 {division} 2"
    vista = preparar_vista_previa({"ecuaciones": [texto]})
    assert vista["estado"] == "ok"
    assert r"\frac{3}{2}" in vista["matriz_latex"]
    assert r"β_{12}" in vista["sistema_latex"]
    assert formatear_elemento_solucion("β12", "1/3") == ("<i>β</i><sub>12</sub>", "β_{12}", "1/3")


@pytest.mark.parametrize("texto", ["α²=1", "√α=1", "α×β=1", "α÷β=1", "α÷0=1", "α 2=1", "₂α=1"])
def test_sistema_rechaza_terminos_no_lineales_o_invalidos(texto):
    """Las ampliaciones de notación no convierten sintaxis inválida en coeficientes."""
    correcto, matriz, variables, mensaje = AnalizadorSistema.parsear_sistema(texto)
    assert not correcto and matriz is None and not variables
    assert mensaje.startswith("Línea 1:")
