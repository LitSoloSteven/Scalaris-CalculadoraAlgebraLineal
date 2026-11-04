"""Restauración de criterios explícitos y capturas decimales anteriores."""
import pytest

from src.frontend.controladores.biseccion.captura_criterio import preparar_entrada
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("tipo,parametro", [
    ("decimales", 2), ("ancho", ".01"), ("relativo", "1"),
    ("residuo", ".1"), ("iteraciones", 3),
])
def test_historial_restaura_criterio_y_parametro(monkeypatch, tipo, parametro):
    """Cada registro conserva su solicitud y se carga sin ejecutar automáticamente otra resolución."""
    async def comprobar(vista):
        """Resuelve, altera y restaura el registro guardado con una captura independiente."""
        vista.cargar_captura(captura_criterio(tipo, parametro))
        await vista.resolver()
        criterio = vista.ultimo_resultado["criterio_solicitado"]
        guardada = vista.historial[0]["captura"]
        vista.criterio.set_value("decimales")
        vista.decimales.set_value(12)
        vista.cargar_captura(guardada)
        assert vista.ultimo_resultado is None
        assert preparar_entrada(vista.capturar()).criterio.tipo == criterio["tipo"]
        assert preparar_entrada(vista.capturar()).criterio.parametro == criterio["parametro"]
        assert vista.historial[0]["captura"] == guardada
    ejecutar_escenario(monkeypatch, comprobar)


def test_captura_antigua_activa_decimal_en_lugar_de_criterio_anterior(monkeypatch):
    """Un registro sin criterio explícito recupera su d aunque el selector esté en residuo."""
    async def comprobar(vista):
        """Carga datos históricos del contrato previo sin asumir la opción actual."""
        vista.cargar_captura(captura_criterio("residuo", ".1"))
        captura = captura_criterio()
        del captura["criterio"]
        captura["decimales"] = 2
        vista.cargar_captura(captura)
        assert vista.criterio.value == "decimales"
        await vista.resolver()
        assert len(vista.ultimo_resultado["iteraciones"]) == 8
    ejecutar_escenario(monkeypatch, comprobar)


def test_ejemplo_parcial_conserva_criterio_elegido(monkeypatch):
    """Cargar un ejemplo de función e intervalo conserva las opciones no indicadas."""
    async def comprobar(vista):
        """Comprueba el mismo contrato de preferencias que tenía el botón de ejemplo anterior."""
        vista.cargar_captura(captura_criterio("iteraciones", 3))
        vista.cargar_captura({"expresion": "x^2-3", "extremo_izquierdo": "1", "extremo_derecho": "2"})
        assert vista.criterio.value == "iteraciones"
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "ITERACIONES_COMPLETADAS"
        assert len(vista.ultimo_resultado["iteraciones"]) == 3
    ejecutar_escenario(monkeypatch, comprobar)
