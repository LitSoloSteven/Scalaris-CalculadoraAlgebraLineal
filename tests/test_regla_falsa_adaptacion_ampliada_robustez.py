"""Aislamiento de fallos internos en la ejecución configurada y sus servicios."""
import pytest

from src.frontend.controladores.regla_falsa import ejecucion_ampliada
from tests.comun_regla_falsa_vista import captura_regla_falsa


@pytest.mark.parametrize("servicio", ["resolver_regla_falsa_configurada", "sugerir_acciones_regla_falsa"])
@pytest.mark.parametrize("error", [ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError])
def test_error_interno_no_publica_detalles_privados(monkeypatch, servicio, error):
    """Sanea errores internos de motor y sugerencias sin filtrar sus mensajes."""
    def fallar(*argumentos):
        """Provoca un fallo privado para contrastar el mensaje público del adaptador."""
        raise error("detalle privado del evaluador")
    monkeypatch.setattr(ejecucion_ampliada, servicio, fallar)
    captura = captura_regla_falsa(criterio={"tipo": "iteraciones", "parametro": 1})
    datos = ejecucion_ampliada.resolver_presentacion(captura)
    assert datos["resultado"]["codigo_diagnostico"] == "ERROR_ADAPTACION"
    assert "privado" not in datos["resultado"]["mensaje"]
    assert datos["ampliado"] is None and datos["sugerencias"] == ()


def test_error_de_parametro_sigue_siendo_orientativo():
    """Conserva la orientación del campo inválido antes de ejecutar el motor."""
    datos = ejecucion_ampliada.resolver_presentacion(captura_regla_falsa(
        criterio={"tipo": "ancho", "parametro": "nan"}))
    assert datos["resultado"]["codigo_diagnostico"] == "ENTRADA_INVALIDA"
    assert "finita" in datos["resultado"]["mensaje"]
