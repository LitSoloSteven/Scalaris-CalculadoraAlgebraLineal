"""Sugerencias de aplicación separadas de las conclusiones del análisis."""
import pytest

from src.frontend.sugerencias import Senales, sugerir


@pytest.mark.parametrize("estado", ["aplicacion_sin_resultado", "aplicacion_exito"])
def test_sugerencias_tratan_aplicacion_y_dimensiones_sin_inferir_propiedades(estado):
    """Los mensajes tratan Av y dimensiones sin presentar núcleo, rango o pivotes."""
    sugerencias = sugerir(Senales("transformaciones", estado, frozenset({"aplicacion_rectangular"})))
    assert sugerencias
    assert all(sugerencia.identificador.startswith("transformaciones.aplicacion.") for sugerencia in sugerencias)
    assert any(sugerencia.identificador.endswith("rectangular") for sugerencia in sugerencias)
    assert not any(palabra in sugerencia.texto.lower() for sugerencia in sugerencias
                   for palabra in ("núcleo", "rango", "pivotes", "inyectividad"))
