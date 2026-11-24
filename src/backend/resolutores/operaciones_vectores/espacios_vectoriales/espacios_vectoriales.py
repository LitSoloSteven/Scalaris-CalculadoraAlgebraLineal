"""Verifica espacios vectoriales reales con operaciones polinómicas exactas."""
from dataclasses import dataclass, field

from .captura_espacio_vectorial import crear_diagnostico, validar_entrada_espacio_vectorial
from .conjunto_espacio import caracterizar_conjunto
from .contrato_espacio_vectorial import (
    AXIOMAS_ESPACIO_VECTORIAL, AxiomaEspacioVectorial, CodigoEspacioVectorial, ComprobacionAxioma,
    DiagnosticoEspacioVectorial, EntradaEspacioVectorial, ErrorCapturaEspacioVectorial,
    ResultadoEspacioVectorial, VectorExacto,
)
from .identidades_espacio import IdentidadesEspacio
from .limites_espacio_vectorial import LimiteAritmeticoEspacio
from .polinomios_espacio import normalizar_residuos

_AXIOMAS_ADITIVOS = ("NEUTRO_SUMA", "INVERSO_SUMA")
_AXIOMAS_DIRECTOS = tuple(axioma for axioma in AXIOMAS_ESPACIO_VECTORIAL if axioma not in _AXIOMAS_ADITIVOS)
_FALTA_NEUTRO = "La comprobación requiere un neutro aditivo certificado."
_MENSAJE_LIMITE = "El cálculo exacto alcanzó uno de sus límites antes de obtener un veredicto."
_MENSAJE_INTERNO = "No se pudo completar la verificación exacta del conjunto y sus operaciones."
_CRITERIOS: dict[AxiomaEspacioVectorial, str] = {
    "CIERRE_SUMA": "La suma de dos elementos debe pertenecer al conjunto.",
    "CIERRE_ESCALAR": "El producto de un escalar real por un elemento debe pertenecer al conjunto.",
    "CONMUTATIVIDAD_SUMA": "Intercambiar los sumandos debe conservar el resultado.",
    "ASOCIATIVIDAD_SUMA": "Las dos agrupaciones de tres sumandos deben dar el mismo resultado.",
    "NEUTRO_SUMA": "En un espacio vectorial, 0 ⊙ p pertenece al conjunto y actúa como neutro bilateral.",
    "INVERSO_SUMA": "En un espacio vectorial, (−1) ⊙ u pertenece al conjunto y cancela a u por ambos lados.",
    "IDENTIDAD_ESCALAR": "Multiplicar un elemento por el escalar 1 debe devolver ese elemento.",
    "ASOCIATIVIDAD_ESCALAR": "Aplicar dos escalares sucesivos debe equivaler a aplicar su producto real.",
    "DISTRIBUTIVIDAD_VECTORES": "El producto por un escalar debe distribuirse sobre la suma de vectores.",
    "DISTRIBUTIVIDAD_ESCALARES": "La suma de escalares debe distribuirse sobre el producto por un vector.",
}


@dataclass
class _RevisionAxiomas:
    comprobaciones: dict[AxiomaEspacioVectorial, ComprobacionAxioma] = field(default_factory=dict)
    vector_cero: VectorExacto | None = None

    def ordenar(self) -> tuple[ComprobacionAxioma, ...]:
        """Devuelve las comprobaciones en el orden público del contrato."""
        return tuple(self.comprobaciones[axioma] for axioma in AXIOMAS_ESPACIO_VECTORIAL)


_VEREDICTOS: dict[CodigoEspacioVectorial, bool] = {
    "ESPACIO_VECTORIAL": True, "NO_ESPACIO_VECTORIAL": False, "CONJUNTO_VACIO": False,
}


def analizar_espacio_vectorial(entrada: EntradaEspacioVectorial) -> ResultadoEspacioVectorial:
    """Valida y analiza la entrada, devolviendo un veredicto tipado con sus certificados."""
    try:
        validada = validar_entrada_espacio_vectorial(entrada)
    except ErrorCapturaEspacioVectorial as error:
        return _resultado("ENTRADA_INVALIDA", diagnostico=error.diagnostico)
    dimension = validada["conjunto"]["dimension_ambiente"]
    try:
        familia = caracterizar_conjunto(validada["conjunto"])
        if familia is None:
            return _resultado("CONJUNTO_VACIO", dimension, diagnostico=crear_diagnostico(
                "Las restricciones son incompatibles y el conjunto es vacío.", "conjunto"
            ))
        revision = _revisar_axiomas(IdentidadesEspacio(validada, familia))
    except LimiteAritmeticoEspacio:
        return _resultado_inconcluso("LIMITE_ARITMETICO", dimension, _MENSAJE_LIMITE)
    except (ArithmeticError, AssertionError, ValueError):
        return _resultado_inconcluso("ERROR_INTERNO", dimension, _MENSAJE_INTERNO)
    return _concluir(dimension, revision)


def _resultado(
    codigo: CodigoEspacioVectorial, dimension: int | None = None,
    revision: _RevisionAxiomas | None = None, diagnostico: DiagnosticoEspacioVectorial | None = None,
) -> ResultadoEspacioVectorial:
    return {
        "estado": "EXITO" if codigo in _VEREDICTOS else "ERROR",
        "codigo": codigo,
        "es_espacio_vectorial": _VEREDICTOS.get(codigo),
        "dimension_ambiente": dimension,
        "vector_cero": revision.vector_cero if revision else None,
        "comprobaciones": revision.ordenar() if revision else (),
        "diagnostico": diagnostico,
    }


def _resultado_inconcluso(
    codigo: CodigoEspacioVectorial, dimension: int, mensaje: str,
) -> ResultadoEspacioVectorial:
    revision = _RevisionAxiomas({axioma: _sin_verificar(axioma, mensaje) for axioma in AXIOMAS_ESPACIO_VECTORIAL})
    return _resultado(codigo, dimension, revision, crear_diagnostico(mensaje))


def _concluir(dimension: int, revision: _RevisionAxiomas) -> ResultadoEspacioVectorial:
    estados = {comprobacion["estado"] for comprobacion in revision.comprobaciones.values()}
    if "NO_CUMPLE" in estados:
        return _resultado("NO_ESPACIO_VECTORIAL", dimension, revision)
    if "NO_VERIFICADO" in estados:
        return _resultado("LIMITE_ARITMETICO", dimension, revision, crear_diagnostico(_MENSAJE_LIMITE))
    return _resultado("ESPACIO_VECTORIAL", dimension, revision)


def _revisar_axiomas(identidades: IdentidadesEspacio) -> _RevisionAxiomas:
    revision = _RevisionAxiomas({axioma: _comprobar(identidades, axioma) for axioma in _AXIOMAS_DIRECTOS})
    sin_violacion_directa = all(valor["estado"] != "NO_CUMPLE" for valor in revision.comprobaciones.values())
    try:
        candidato = identidades.candidato_neutro()
    except LimiteAritmeticoEspacio as error:
        revision.comprobaciones["NEUTRO_SUMA"] = _sin_verificar("NEUTRO_SUMA", str(error))
    else:
        neutro = _comprobar(identidades, "NEUTRO_SUMA", candidato, sin_violacion_directa)
        revision.comprobaciones["NEUTRO_SUMA"] = neutro
        if neutro["estado"] == "CUMPLE":
            revision.vector_cero = candidato
    revision.comprobaciones["INVERSO_SUMA"] = (
        _sin_verificar("INVERSO_SUMA", _FALTA_NEUTRO) if revision.vector_cero is None
        else _comprobar(identidades, "INVERSO_SUMA", revision.vector_cero, sin_violacion_directa)
    )
    return revision


def _comprobar(
    identidades: IdentidadesEspacio, axioma: AxiomaEspacioVectorial,
    candidato: VectorExacto | None = None, candidato_concluyente: bool = False,
) -> ComprobacionAxioma:
    try:
        variables, residuos = identidades.residuos(axioma, candidato)
    except LimiteAritmeticoEspacio as error:
        return _sin_verificar(axioma, str(error))
    tiene_residuo = any(residuos)
    if tiene_residuo and candidato is not None and not candidato_concluyente:
        return _sin_verificar(axioma, "El candidato falla y los demás axiomas no permiten decidir su existencia.")
    explicacion = "Se obtuvo un residuo polinómico no nulo." if tiene_residuo else "Todos los residuos son cero."
    return {
        "axioma": axioma,
        "estado": "NO_CUMPLE" if tiene_residuo else "CUMPLE",
        "explicacion": f"{_CRITERIOS[axioma]} {explicacion}",
        "certificado": {"variables_libres": variables, "identidades": normalizar_residuos(residuos)},
        "testigo": None,
    }


def _sin_verificar(axioma: AxiomaEspacioVectorial, explicacion: str) -> ComprobacionAxioma:
    return {
        "axioma": axioma, "estado": "NO_VERIFICADO", "explicacion": explicacion,
        "certificado": None, "testigo": None,
    }
