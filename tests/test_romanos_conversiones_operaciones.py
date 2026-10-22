"""Conversiones romanas y operaciones dentro del rango representable."""
import pytest

from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    CalculadoraRomana, ErrorNumeroRomano, entero_a_romano, romano_a_entero,
)


class TestConversionesRomanas:
    """Conversiones canónicas y rechazo de entradas no representables."""

    @pytest.mark.parametrize("decimal, romano_esperado", [
        (1, "I"), (4, "IV"), (9, "IX"), (14, "XIV"), (40, "XL"),
        (44, "XLIV"), (90, "XC"), (99, "XCIX"), (400, "CD"), (900, "CM"),
        (1994, "MCMXCIV"), (2026, "MMXXVI"), (3999, "MMMCMXCIX"),
    ])
    def test_conversion_bidireccional(self, decimal: int, romano_esperado: str):
        """Cada número conserva su valor al convertir en ambos sentidos."""
        assert entero_a_romano(decimal) == romano_esperado
        assert romano_a_entero(romano_esperado) == decimal

    @pytest.mark.parametrize("romano_invalido", [
        "IIII", "VX", "IL", "IC", "MMMM", "ABC", "123", "", "   ", "VV", "LL", "DD",
    ])
    def test_conversion_rechaza_romano_invalido(self, romano_invalido: str):
        """La conversión rechaza caracteres y formas romanas no canónicas."""
        with pytest.raises(ErrorNumeroRomano):
            romano_a_entero(romano_invalido)

    @pytest.mark.parametrize("fuera_de_rango", [0, -1, -50, 4000, 5000])
    def test_conversion_rechaza_entero_fuera_de_rango(self, fuera_de_rango: int):
        """Solo se admiten enteros representables entre uno y 3999."""
        with pytest.raises(ErrorNumeroRomano):
            entero_a_romano(fuera_de_rango)


class TestSumaRomana:
    """Suma romana y límite superior de representación."""

    def test_suma_simple(self):
        """La suma simple incluye resultado decimal y pasos explicativos."""
        resultado = CalculadoraRomana.sumar("V", "III")
        assert resultado.resultado_romano == "VIII"
        assert resultado.resultado_decimal == 8
        assert len(resultado.pasos) >= 4

    def test_suma_con_acarreo(self):
        """La suma reagrupa los símbolos cuando atraviesa una decena."""
        resultado = CalculadoraRomana.sumar("XIV", "IX")
        assert resultado.resultado_romano == "XXIII"
        assert resultado.resultado_decimal == 23

    def test_suma_grandes(self):
        """La suma conserva el resultado al atravesar un millar."""
        resultado = CalculadoraRomana.sumar("MCMXC", "X")
        assert resultado.resultado_romano == "MM"
        assert resultado.resultado_decimal == 2000

    def test_suma_excede_maximo(self):
        """Una suma superior al máximo lanza el error de dominio previsto."""
        with pytest.raises(ErrorNumeroRomano, match="excede el límite"):
            CalculadoraRomana.sumar("MMM", "M")


class TestRestaRomana:
    """Resta romana y resultados que carecen de representación."""

    def test_resta_valida(self):
        """La resta conserva la equivalencia decimal y romana."""
        resultado = CalculadoraRomana.restar("XX", "VIII")
        assert resultado.resultado_romano == "XII"
        assert resultado.resultado_decimal == 12

    def test_resta_caso_borde_uno(self):
        """El resultado mínimo representable sigue siendo válido."""
        resultado = CalculadoraRomana.restar("X", "IX")
        assert resultado.resultado_romano == "I"
        assert resultado.resultado_decimal == 1

    def test_resta_da_cero_invalido(self):
        """La resta rechaza un resultado cero."""
        with pytest.raises(ErrorNumeroRomano, match="cero"):
            CalculadoraRomana.restar("V", "V")

    def test_resta_da_negativo_invalido(self):
        """La resta rechaza un resultado negativo."""
        with pytest.raises(ErrorNumeroRomano, match="negativos"):
            CalculadoraRomana.restar("III", "VII")


class TestMultiplicacionRomanaUnDigito:
    """Multiplicación de operandos de un dígito por sumas sucesivas."""

    def test_multiplicacion_valida_tres_por_cuatro(self):
        """El resultado incluye las cuatro sumas y la expresión acumulada."""
        resultado = CalculadoraRomana.multiplicar_un_digito("III", "IV")
        assert resultado.resultado_romano == "XII"
        assert resultado.resultado_decimal == 12
        assert any("Suma 1" in paso for paso in resultado.pasos)
        assert any("Suma 4" in paso for paso in resultado.pasos)
        assert any("III + III + III + III" in paso for paso in resultado.pasos)

    def test_multiplicacion_por_uno(self):
        """Multiplicar por uno conserva el operando."""
        resultado = CalculadoraRomana.multiplicar_un_digito("VII", "I")
        assert resultado.resultado_romano == "VII"
        assert resultado.resultado_decimal == 7

    def test_multiplicacion_maxima_nueve_por_nueve(self):
        """Los dos operandos máximos de un dígito producen 81."""
        resultado = CalculadoraRomana.multiplicar_un_digito("IX", "IX")
        assert resultado.resultado_romano == "LXXXI"
        assert resultado.resultado_decimal == 81

    def test_error_primer_operando_mayor_a_nueve(self):
        """El primer operando de dos dígitos se rechaza."""
        with pytest.raises(ErrorNumeroRomano, match="no es de 1 dígito"):
            CalculadoraRomana.multiplicar_un_digito("X", "II")

    def test_error_segundo_operando_mayor_a_nueve(self):
        """El segundo operando de dos dígitos se rechaza."""
        with pytest.raises(ErrorNumeroRomano, match="no es de 1 dígito"):
            CalculadoraRomana.multiplicar_un_digito("III", "XI")

    def test_error_ambos_mayores_a_nueve(self):
        """La multiplicación rechaza ambos operandos de dos dígitos."""
        with pytest.raises(ErrorNumeroRomano, match="no es de 1 dígito"):
            CalculadoraRomana.multiplicar_un_digito("XV", "XX")
