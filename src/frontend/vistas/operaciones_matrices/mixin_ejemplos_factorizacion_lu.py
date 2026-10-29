"""Carga de ejemplos etiquetados de factorización LU."""
from src.frontend.componentes.captura_modelos import construir_ejemplos
from src.frontend.textos import LU_EJEMPLOS
from ._ejemplos_factorizacion_lu import EJEMPLOS_FACTORIZACION_LU


class MixinEjemplosFactorizacionLU:
    """Ofrece ejemplos que se cargan sin calcular resultados."""

    def _construir_ejemplos(self) -> None:
        construir_ejemplos(EJEMPLOS_FACTORIZACION_LU, self._cargar_ejemplo, LU_EJEMPLOS)

    def _cargar_ejemplo(self, ejemplo: dict) -> None:
        self.panel_matriz.cargar_matriz(ejemplo["datos"])
