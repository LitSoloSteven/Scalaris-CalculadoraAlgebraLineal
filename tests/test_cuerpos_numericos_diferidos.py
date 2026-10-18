"""Memoria y contenido exacto al generar procedimientos numéricos extensos."""
import tracemalloc
from pathlib import Path

import pytest
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.frontend.vistas.sistemas_numericos import _pasos_bases
from src.frontend.vistas.sistemas_numericos.pasos_romanos import construir_pasos_romanos
from src.backend.resolutores.sistemas_numericos.calculadora_romana import CalculadoraRomana


@pytest.mark.parametrize("base_origen,valor,base_destino,cantidad", [
    ("binario", "1" * 800, "decimal", 801),
    ("decimal", str(2 ** 800 - 1), "binario", 801),
])
def test_procedimiento_extenso_no_retiene_tablas_acumuladas(base_origen, valor, base_destino, cantidad):
    """Ochocientos bits conservan sus pasos con memoria acotada y HTML íntegro al solicitarlo."""
    resultado = getattr(ConversorBases(), f"{base_origen}_a_todo")(valor, base_destino)
    tracemalloc.start()
    try:
        pasos, grupos = _pasos_bases.construir_pasos_bases(resultado)
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert len(pasos) == cantidad
    assert len(grupos) == 1
    assert pico < 8 * 1024 * 1024
    assert "<table" in str(pasos[0].cuerpo)
    assert "<table" in str(pasos[-1].cuerpo)
    assert resultado[base_destino] in pasos[-1].cuerpo.expresion_latex


def test_creacion_no_renderiza_tablas_y_cada_cuerpo_conserva_su_indice(monkeypatch):
    """Las tablas se generan al solicitar cada paso, usando el índice de ese paso."""
    original = _pasos_bases._crear_tabla_division
    llamadas = []
    def renderizar(filas, hasta_indice):
        """Registra las tablas pedidas conservando su HTML real."""
        llamadas.append(hasta_indice)
        return original(filas, hasta_indice)
    monkeypatch.setattr(_pasos_bases, "_crear_tabla_division", renderizar)
    pasos, _ = _pasos_bases.construir_pasos_bases(ConversorBases().decimal_a_todo("42", "binario"))
    assert llamadas == []
    assert "<table" in str(pasos[0].cuerpo)
    assert "<table" in str(pasos[2].cuerpo)
    assert llamadas == [0, 2]


def test_tarjetas_didacticas_romanas_no_comparten_ocultacion_del_conversor():
    """La regla de ocultación inicial solo afecta a las tarjetas de conversión."""
    css = Path("src/frontend/recursos/css/vistas_numericos.css").read_text(encoding="utf8")
    assert ".numericos-tarjeta-conversion {" in css
    assert ".numericos-tarjeta {" not in css
    pasos, _ = construir_pasos_romanos(CalculadoraRomana.sumar("I", "I"), "suma")
    assert "numericos-tarjeta" in str(pasos[0].cuerpo)
    assert "numericos-tarjeta-conversion" not in str(pasos[0].cuerpo)
    assert "numericos-tarjeta" in str(pasos[-1].cuerpo)
