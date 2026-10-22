"""Concordancia entre el numeral convertido y la lectura final del procedimiento."""
import pytest
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.frontend.vistas.sistemas_numericos._pasos_bases import construir_pasos_bases


@pytest.mark.parametrize("valor,base,esperado", [
    ("42", "binario", "101010"), ("42", "octal", "52"), ("42", "hexadecimal", "2A"),
    ("-42", "binario", "-101010"), ("-42", "octal", "-52"), ("-42", "hexadecimal", "-2A"),
    ("0", "binario", "0"), ("0", "octal", "0"), ("0", "hexadecimal", "0"),
    ("65535", "binario", "1111111111111111"), ("65535", "octal", "177777"),
    ("65535", "hexadecimal", "FFFF"),
])
def test_lectura_final_conserva_numeral_completo(valor, base, esperado):
    """La tabla, descripción y fórmula finales conservan el resultado completo y su signo."""
    bases = {"binario": 2, "octal": 8, "hexadecimal": 16}
    resultado = ConversorBases().decimal_a_todo(valor, base)
    pasos, grupos = construir_pasos_bases(resultado)
    assert resultado[base] == esperado
    assert len(grupos) == 1
    assert pasos[-1].tipo == "lectura"
    assert pasos[-1].descripcion == f"Resultado en base {bases[base]}: {esperado}"
    assert pasos[-1].cuerpo.expresion_latex == f"{esperado}_{{{bases[base]}}}"
