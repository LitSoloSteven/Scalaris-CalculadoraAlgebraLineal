"""Persistencia y revocación del extremo cero elegido en una captura real."""
import pytest

from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_preferencia_cero_sobrevive_recientes_y_cambio_de_criterio(monkeypatch):
    async def comprobar(vista):
        captura = captura_regla_falsa(expresion="x*(x-1)", extremo_izquierdo="0", extremo_derecho="1", cero_preferido=1)
        vista.cargar_captura(captura)
        await vista.resolver()
        assert vista.ultimo_resultado["aproximacion"] == 1
        assert vista.ultimo_resultado["iteraciones"] == ()
        registro = vista.historial[0]["captura"]
        assert registro["cero_preferido"] == 1
        vista.criterio.set_value("iteraciones")
        assert vista.capturar()["cero_preferido"] == 1
        vista.cargar_captura(registro)
        await vista.resolver()
        assert vista.ultimo_resultado["aproximacion"] == 1
        vista.limpiar_todo()
        assert "cero_preferido" not in vista.capturar()
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("atributo,valor", [("expresion", "x"), ("inferior", "-.1"),
                                           ("superior", "2"), ("unidad_angular", "grados")])
def test_edicion_incompatible_revoca_cero_y_resultado(monkeypatch, atributo, valor):
    async def comprobar(vista):
        vista.cargar_captura(captura_regla_falsa(expresion="x*(x-1)", extremo_izquierdo="0",
                                               extremo_derecho="1", cero_preferido=1))
        await vista.resolver()
        getattr(vista, atributo).set_value(valor)
        assert "cero_preferido" not in vista.capturar()
        assert vista.ultimo_resultado is vista.ultimo_ampliado is None
    ejecutar_escenario(monkeypatch, comprobar)
