"""Captura estable y delegacion de la resolucion de sistemas para la vista."""
from . import ControladorGauss, ControladorGaussJordan


def entrada_actual(vista) -> dict:
    """Captura modo, metodo y texto sin compartir los caches editables."""
    entrada = {'modo': vista.pestanas_modo.value, 'metodo': vista.pestanas_metodo.value}
    if entrada['modo'] == 'Ecuaciones':
        entrada['ecuaciones'] = [campo.value for campo in vista.entradas_ecuaciones]
    else:
        entrada['A'], entrada['b'] = vista.cuadricula.obtener_datos_matriz()
    return entrada


def procesar_carga_sistema(carga: str, metodo: str) -> str:
    """Elige el controlador del metodo canonico y delega la resolucion serializada."""
    controlador = ControladorGauss if metodo == 'gauss' else ControladorGaussJordan
    return controlador.procesar_sistema(carga)
