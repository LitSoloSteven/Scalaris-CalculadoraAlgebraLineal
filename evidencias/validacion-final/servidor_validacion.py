"""Servidor local de validación; solo retrasa el trabajador para reproducir carreras."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nicegui import ui
from src.frontend.aplicacion import inicializar_aplicacion
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante

procesar_original = ControladorDeterminante.procesar_captura


def procesar_con_espera(captura):
    """Mantiene el cálculo original y añade una espera observable de 800 ms."""
    time.sleep(0.8)
    return procesar_original(captura)


ControladorDeterminante.procesar_captura = staticmethod(procesar_con_espera)
inicializar_aplicacion()
ui.run(host='127.0.0.1', port=8080, show=False, reload=False,
       storage_secret='validacion-final-local')
