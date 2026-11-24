"""Ejemplos editables de operaciones usuales, trasladadas y fallidas."""
from dataclasses import dataclass

from .presentacion_espacio_vectorial import variables_operacion

TerminosCaptura = list[list[dict[str, str]]]


@dataclass(frozen=True)
class EjemploEspacioVectorial:
    """Describe el conjunto y el tipo de operaciones de un ejemplo editable."""

    dimension: int
    ecuaciones: str = ""
    traslado: bool = False
    diferencia: bool = False


EJEMPLOS_OPERACIONES = {
    "Recta real con operaciones usuales": EjemploEspacioVectorial(1),
    "Recta y = 1 con operaciones trasladadas": EjemploEspacioVectorial(2, "x2 = 1", traslado=True),
    "Recta y = 1 con operaciones usuales": EjemploEspacioVectorial(2, "x2 = 1"),
    "Recta real con la resta como suma": EjemploEspacioVectorial(1, diferencia=True),
    "Restricciones incompatibles": EjemploEspacioVectorial(1, "x1 = 0\nx1 = 1"),
}


def terminos_ejemplo(ejemplo: EjemploEspacioVectorial, campo: str) -> TerminosCaptura:
    """Devuelve las coordenadas de la operación indicada como borradores de términos."""
    cantidad = len(variables_operacion(campo, ejemplo.dimension))
    return [_coordenada(ejemplo, campo, indice, cantidad) for indice in range(ejemplo.dimension)]


def _coordenada(ejemplo: EjemploEspacioVectorial, campo: str, indice: int, cantidad: int) -> list[dict[str, str]]:
    if campo == "suma":
        signo = "-1" if ejemplo.diferencia else "1"
        terminos = [_termino("1", cantidad, indice), _termino(signo, cantidad, ejemplo.dimension + indice)]
        if ejemplo.traslado and indice == 1:
            terminos.append(_termino("-1", cantidad))
        return terminos
    terminos = [_termino("1", cantidad, 0, indice + 1)]
    if ejemplo.traslado and indice == 1:
        terminos += [_termino("1", cantidad), _termino("-1", cantidad, 0)]
    return terminos


def _termino(coeficiente: str, cantidad: int, *indices: int) -> dict[str, str]:
    exponentes = " ".join("1" if indice in indices else "0" for indice in range(cantidad))
    return {"coeficiente": coeficiente, "exponentes": exponentes}
