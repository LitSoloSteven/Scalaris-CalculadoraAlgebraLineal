"""Adaptación de una matriz transferida a la captura de cada modelo."""
from functools import partial
from src.frontend.componentes.transferencia import recibir_matriz
from .carga_modelos import cargar_captura_modelo


def recibir_matriz_modelo(vista, token: str) -> None:
    """Carga C o A mediante recepción común, con campos auxiliares vacíos."""
    recibir_matriz(token, vista.herramienta_modelo, partial(_cargar_matriz, vista),
                   vista.contenedor_transferencia)


def _cargar_matriz(vista, datos: list[list[str]]) -> None:
    captura = ({"matriz_coeficientes": datos, "vector_demanda": []}
               if vista.herramienta_modelo == "leontief" else {"matriz_transformacion": datos})
    cargar_captura_modelo(vista, captura)
