"""Casos de captura y factorización LU con dimensiones y números extremos."""
import pytest

from src.frontend.controladores.operaciones_matrices.controlador_factorizacion_lu import ControladorFactorizacionLU
from src.frontend.vistas.operaciones_matrices._presentacion_factorizacion_lu import adaptar_traza_factorizacion_lu


@pytest.mark.parametrize("datos", [
    [["0"]],
    [["1001/1000", "-0.125", "7/9999", "2", "3", "4", "5", "6", "7", "8"]],
    [[str(indice)] for indice in range(10)],
    [["1" if fila == columna else "0" for columna in range(10)] for fila in range(10)],
    [["0"] * 3 for _ in range(3)],
    [["1", "2"], ["2", "4"]],
    [["1234567890123456789012345678901234567890", "1/1001"]],
])
def test_factoriza_capturas_limite(datos):
    """Conserva dimensiones y comprueba PA = LU en capturas límite exactas."""
    resultado = ControladorFactorizacionLU.procesar_captura({"matriz_a": datos})
    assert resultado["estado"] == "EXITO" and resultado["comprobacion"]["coincide"]
    assert (resultado["filas"], resultado["columnas"]) == (len(datos), len(datos[0]))
    pasos, grupos = adaptar_traza_factorizacion_lu(resultado)
    assert [indice for grupo in grupos for indice in grupo.indices_pasos] == list(range(len(pasos)))


def test_entrada_muy_larga_devuelve_error():
    """Rechaza una celda mayor que el límite del dominio con coordenadas."""
    resultado = ControladorFactorizacionLU.procesar_captura({"matriz_a": [["9" * 300]]})
    assert resultado["estado"] == "ERROR" and "1" in resultado["mensaje"]
