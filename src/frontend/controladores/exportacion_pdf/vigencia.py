"""Contrato reutilizable de vigencia para exportaciones asíncronas."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.ai.huellas import calcular_huella
from src.frontend.controladores.sesion_matricial import captura_sigue_vigente, calculo_sigue_vigente


@dataclass(frozen=True)
class EnlacePDF:
    """Relaciona una vista, su captura actual y el contenedor que se fotografía."""
    vista: Any
    entrada: Callable[[], dict]
    raiz: str
    leer_estado: Callable[[], tuple] | None = None

    def estado(self) -> tuple:
        """Devuelve contenedor, resultado, revisión y solicitud con el contrato de la vista."""
        if self.leer_estado is not None:
            return self.leer_estado()
        return (getattr(self.vista, 'contenedor_resultados', None),
                getattr(self.vista, 'ultimo_resultado', None),
                getattr(self.vista, '_revision_captura', 0),
                getattr(self.vista, '_identificador_calculo', 0))

    def vigente(self, resultado: dict) -> bool:
        """Comprueba identidad, montaje, estado y huella con el criterio del cálculo actual."""
        contenedor, actual, _, _ = self.estado()
        if contenedor is None or contenedor.is_deleted:
            return False
        if not resultado or str(resultado.get('estado', 'ERROR')).upper() == 'ERROR':
            return False
        return (actual is resultado
                and getattr(self.vista, '_huella_resultado', None) == calcular_huella(self.entrada()))

    def testigo(self) -> tuple[int, str, int]:
        """Devuelve revisión, huella y solicitud sin almacenar la captura editable."""
        _, _, revision, solicitud = self.estado()
        return revision, self.vista._huella_resultado, solicitud

    def comprobar(self, testigo: tuple[int, str, int], resultado: dict) -> bool:
        """Descarta un trabajo si se editó, limpió o recalculó durante su ejecución."""
        revision, huella, identificador = testigo
        if self.leer_estado is not None:
            return self.vigente(resultado) and self.testigo() == testigo
        return (self.vigente(resultado) and calculo_sigue_vigente(self.vista, identificador)
                and captura_sigue_vigente(self.vista, revision, huella, self.entrada()))
