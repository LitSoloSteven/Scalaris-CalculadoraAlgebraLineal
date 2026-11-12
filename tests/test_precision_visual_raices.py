"""Regresión del formato compartido entre bisección y regla falsa."""
import pytest

from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario as ejecutar_biseccion
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario as ejecutar_regla_falsa


@pytest.mark.parametrize("metodo", ["biseccion", "regla_falsa"])
@pytest.mark.parametrize("precision", [0, 15])
def test_formato_recupera_un_valor_valido_sin_recalcular(monkeypatch, metodo, precision):
    """Ambas vistas aceptan cero y la precisión máxima después de un error visual sin perder el resultado."""
    async def comprobar(vista):
        """Introduce formato inválido y vuelve a un extremo permitido de la preferencia."""
        vista.cargar_captura(captura_criterio() if metodo == "biseccion" else captura_regla_falsa())
        await vista.resolver()
        respuesta, huella = vista.ultimo_resultado, vista._huella_resultado
        vista.formato.set_value(None)
        assert vista.error_formato.text and vista.ultimo_resultado is respuesta
        vista.formato.set_value(precision)
        assert vista._precision_visual == precision and not vista.error_formato.text
        assert vista.ultimo_resultado is respuesta and vista._huella_resultado == huella
        textos = [str(elemento.text) for elemento in vista.contenedor_resultados.descendants()
                  if hasattr(elemento, "text")]
        esperado = f"x ≈ {respuesta['aproximacion']:.{precision}f}"
        assert esperado in textos

    ejecutar = ejecutar_biseccion if metodo == "biseccion" else ejecutar_regla_falsa
    ejecutar(monkeypatch, comprobar)
