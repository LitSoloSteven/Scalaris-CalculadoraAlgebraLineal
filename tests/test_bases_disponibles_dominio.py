"""Bases disponibles y validación centralizada del conversor numérico."""
from src.backend.utilidades.reglas_dominio import BASES_NUMERICAS, validar_entrada_base


def test_catalogo_conserva_las_cuatro_bases_numericas():
    """El dominio conserva las cuatro bases que usa la interfaz para capturar entradas."""
    assert 'binario' in BASES_NUMERICAS
    assert 'octal' in BASES_NUMERICAS
    assert 'decimal' in BASES_NUMERICAS
    assert 'hexadecimal' in BASES_NUMERICAS
    assert BASES_NUMERICAS == {'binario': 2, 'octal': 8, 'decimal': 10, 'hexadecimal': 16}
    for base in BASES_NUMERICAS.values():
        assert validar_entrada_base('10', base)[0] is True
