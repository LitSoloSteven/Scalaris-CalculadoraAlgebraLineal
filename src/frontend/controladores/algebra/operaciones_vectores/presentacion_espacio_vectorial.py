"""Formato exacto de operaciones, certificados y contraejemplos."""
from fractions import Fraction

from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.contrato_espacio_vectorial import (
    ComprobacionAxioma, OperacionPolinomica, TerminoPolinomico, TestigoAxioma,
)

_MAXIMO_RESUMEN_EVIDENCIA = 160


def variables_operacion(campo: str, dimension: int) -> tuple[str, ...]:
    """Devuelve los nombres en el orden de exponentes del contrato."""
    variables_u = tuple(f"u{indice}" for indice in range(1, dimension + 1))
    if campo == "producto_escalar":
        return ("α", *variables_u)
    return (*variables_u, *(f"v{indice}" for indice in range(1, dimension + 1)))


def _monomio(termino: TerminoPolinomico, variables: tuple[str, ...]) -> str:
    factores = [
        f"{variable}^{exponente}" if exponente > 1 else variable
        for variable, exponente in zip(variables, termino["exponentes"])
        if exponente
    ]
    magnitud = abs(termino["coeficiente"])
    if magnitud != 1 or not factores:
        factores.insert(0, str(magnitud))
    return "·".join(factores)


def formatear_polinomios(operacion: OperacionPolinomica, variables: tuple[str, ...]) -> tuple[str, ...]:
    """Expresa cada coordenada como un polinomio en texto, con racionales exactos."""
    return tuple(_polinomio(terminos, variables) for terminos in operacion)


def _polinomio(terminos: tuple[TerminoPolinomico, ...], variables: tuple[str, ...]) -> str:
    partes = []
    for termino in terminos:
        negativo = termino["coeficiente"] < 0
        separador = (" − " if negativo else " + ") if partes else ("−" if negativo else "")
        partes.append(separador + _monomio(termino, variables))
    return "".join(partes) or "0"


def formatear_vector(vector: tuple[Fraction, ...]) -> str:
    """Presenta un vector en coordenadas racionales exactas."""
    return "(" + ", ".join(map(str, vector)) + ")"


def evidencia_axioma(comprobacion: ComprobacionAxioma) -> tuple[str, ...]:
    """Devuelve las identidades exactas y el testigo explícito cuando están disponibles."""
    certificado = comprobacion["certificado"]
    testigo = comprobacion["testigo"]
    lineas = []
    if certificado is not None:
        variables = certificado["variables_libres"]
        descripcion = ", ".join(variables) if variables else "ninguna"
        lineas.append(f"Variables libres · {descripcion}")
        for indice, residuo in enumerate(formatear_polinomios(certificado["identidades"], variables), 1):
            lineas.append(f"Residuo {indice} = {residuo}")
    if testigo is not None:
        lineas.extend(_lineas_testigo(testigo))
    return tuple(lineas)


def resumir_evidencia_axioma(comprobacion: ComprobacionAxioma) -> str:
    """Proporciona a Glosa un término exacto de la evidencia sin enviar toda la expansión."""
    certificado = comprobacion["certificado"]
    if certificado is None:
        return ""
    for indice, terminos in enumerate(certificado["identidades"], 1):
        if terminos:
            muestra = _polinomio(terminos[:1], certificado["variables_libres"])
            if len(muestra) > _MAXIMO_RESUMEN_EVIDENCIA:
                return f"El residuo {indice} tiene {len(terminos)} términos y es distinto de cero."
            if len(terminos) == 1:
                return f"Residuo {indice} = {muestra}."
            return f"El residuo {indice} tiene {len(terminos)} términos e incluye {muestra}."
    return "Todos los residuos del certificado son cero."


def _lineas_testigo(testigo: TestigoAxioma) -> tuple[str, ...]:
    vectores = ", ".join(formatear_vector(vector) for vector in testigo["vectores"])
    return (
        f"Vectores · {vectores}",
        f"Escalares · {formatear_vector(testigo['escalares'])}",
        f"Lado izquierdo = {formatear_vector(testigo['lado_izquierdo'])}",
        f"Lado derecho = {formatear_vector(testigo['lado_derecho'])}",
    )
