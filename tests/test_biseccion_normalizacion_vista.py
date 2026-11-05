"""Normalización visible con historial, huella y respuestas asíncronas vigentes."""
import pytest
from nicegui import run

from src.ai.huellas import calcular_huella
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def _invertida():
    return {**captura_criterio(), "extremo_izquierdo": "2", "extremo_derecho": "1"}


def _textos(vista):
    return [getattr(elemento, "text", "") for elemento in vista.contenedor_resultados.descendants()]


def test_normalizacion_conserva_resultado_huella_historial_y_contexto(monkeypatch):
    """Los campos se ordenan al publicar sin disparar la limpieza de resultados."""
    async def comprobar(vista):
        """Resuelve y restaura la captura canónica guardada en el historial."""
        vista.cargar_captura(_invertida())
        await vista.resolver()
        resultado = vista.ultimo_resultado
        assert resultado["estado"] == "EXITO"
        assert (float(vista.inferior.value), float(vista.superior.value)) == (1, 2)
        assert vista._huella_resultado == calcular_huella(vista.capturar())
        assert vista.reproductor_pasos is not None
        assert vista.obtener_contexto_ia().resultado["diagnostico"] == resultado["diagnostico"]
        assert any("Se intercambiaron" in texto for texto in _textos(vista))
        guardada = vista.historial[0]["captura"]
        assert (float(guardada["extremo_izquierdo"]), float(guardada["extremo_derecho"])) == (1, 2)
        vista.formato.set_value(9)
        assert vista.ultimo_resultado is resultado
        assert any("Se intercambiaron" in texto for texto in _textos(vista))
        vista.cargar_captura(guardada)
        assert vista.ultimo_resultado is None
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
        assert not vista.ultimo_resultado["advertencias"]
        vista.superior.set_value("3")
        assert vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_normalizacion_tambien_es_visible_ante_error_del_motor(monkeypatch):
    """El aviso no desaparece cuando una entrada canónica falla al evaluar su función."""
    async def comprobar(vista):
        """Comprueba campos y advertencias de un error de sintaxis con extremos invertidos."""
        vista.cargar_captura({**_invertida(), "expresion": "sin()"})
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert (float(vista.inferior.value), float(vista.superior.value)) == (1, 2)
        assert vista._huella_resultado == calcular_huella(vista.capturar())
        assert any("Se intercambiaron" in texto for texto in _textos(vista))
        assert not vista.historial
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("restaurar", [False, True])
def test_respuesta_obsoleta_no_normaliza_campos_ni_publica(monkeypatch, restaurar):
    """Editar durante el trabajo impide aplicar la normalización de una captura anterior."""
    async def comprobar(vista):
        """Altera los campos mientras trabaja y comprueba su estado tras descartar la respuesta."""
        vista.cargar_captura(_invertida())
        async def trabajar(funcion, captura):
            """Calcula con los datos anteriores y simula ediciones antes de devolverlos."""
            respuesta = funcion(captura)
            vista.inferior.set_value("3")
            if restaurar:
                vista.inferior.set_value("2")
            return respuesta
        monkeypatch.setattr(run, "io_bound", trabajar)
        await vista.resolver()
        assert vista.inferior.value == ("2" if restaurar else "3")
        assert vista.superior.value == "1"
        assert vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
        assert not vista.historial
    ejecutar_escenario(monkeypatch, comprobar)
