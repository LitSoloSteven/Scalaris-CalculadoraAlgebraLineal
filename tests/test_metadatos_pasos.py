"""Pruebas unitarias para la extracción de metadatos pedagógicos de pasos."""
from src.frontend.controladores.sistemas_lineales import construir_metadatos_pasos


class MatrizSimulada:
    """Simulador mínimo de matriz para pruebas de extracción de metadatos."""

    def __init__(self, datos):
        self.datos = datos
        self.filas = len(datos)
        self.columnas = len(datos[0])

    def obtener(self, r, c):
        """Devuelve el valor simulado de la celda solicitada."""
        return self.datos[r][c]


def test_construir_metadatos_pasos():
    """Valida la generación de metadatos de filas y tipo de operación."""
    pasos = [
        {"descripcion": "Intercambio: Fila 1 ↔ Fila 2", "matriz": MatrizSimulada([[1, 2], [3, 4]])},
        {"descripcion": "Fila 2 = Fila 2 − (3) · Fila 1", "matriz": MatrizSimulada([[1, 2], [0, -2]])},
    ]
    meta = construir_metadatos_pasos(pasos)
    assert len(meta) == 2
    assert meta[0]["tipo"] == "intercambio"
    assert meta[1]["tipo"] == "eliminacion"
    assert meta[1]["indice"] == 2
    assert meta[1]["total"] == 2
