"""Ejecución del cliente geométrico con Node y un DOM simulado."""
import shutil
import subprocess
import pytest
from tests.comun import RAIZ


def test_deslizador_errores_foco_y_limpieza_de_cliente():
    """Comprueba actualización 2D/3D, avisos, foco y liberación de oyentes y cuadros."""
    ejecutable = shutil.which('node')
    if ejecutable is None:
        pytest.skip('Node no está disponible; no se instalan herramientas para esta prueba.')
    resultado = subprocess.run([
        ejecutable, str(RAIZ / 'tests/geometria_cliente_simulado.js'),
        str(RAIZ / 'src/frontend/recursos/js/geometria.js'),
    ], capture_output=True, text=True, timeout=10)
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
