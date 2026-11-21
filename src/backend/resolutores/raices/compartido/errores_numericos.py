"""Diagnósticos estables de capacidad y singularidades en funciones reales."""
from src.backend.excepciones import ErrorDominio, ErrorNoFinito


class ErrorCapacidadNumerica(ErrorNoFinito):
    """Indica una evaluación no representable con un código independiente del mensaje."""

    def __init__(self, mensaje: str, codigo: str = "EVALUACION_NO_FINITA") -> None:
        """Guarda el diagnóstico y el mensaje castellano del fallo de representación."""
        self.codigo = codigo
        super().__init__(mensaje)


class ErrorSingularidad(ErrorDominio):
    """Indica una singularidad localizada estructuralmente en el intervalo solicitado."""

    codigo = "SINGULARIDAD_DETECTADA"
