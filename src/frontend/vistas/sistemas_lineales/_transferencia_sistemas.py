"""Carga de una matriz transferida a los controles del sistema lineal."""
from functools import partial
from src.frontend.componentes.transferencia import recibir_matriz


def procesar_transferencia_matriz(vista, token: str) -> None:
    """Consume el token válido, reconstruye la captura y retira el parámetro URL."""
    recibir_matriz(token, "sistemas", partial(_cargar_cuadricula, vista), vista.contenedor_transferencia)


def _cargar_cuadricula(vista, datos: list) -> None:
    if vista.pestanas_modo.value == 'Ecuaciones':
        vista.pestanas_modo.set_value('Matriz')
    vista.casilla_homogeneo.set_value(False)
    vista.cuadricula.cargar_datos(datos, [""] * len(datos))
