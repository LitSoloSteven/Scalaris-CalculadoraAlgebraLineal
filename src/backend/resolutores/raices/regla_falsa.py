"""Motor clasico de regla falsa (falsa posicion) con la preparacion compartida."""
from dataclasses import asdict, dataclass, replace

from .aritmetica_regla_falsa import punto_cruce
from .contrato_biseccion import ContextoFallo
from .contrato_continuidad import InformeContinuidad
from .contrato_regla_falsa import (
    EntradaReglaFalsa,
    IteracionReglaFalsa,
    ResultadoReglaFalsa,
)
from .decision_biseccion import signo_producto
from .criterios_biseccion import CriterioParada
from .parada_regla_falsa import decidir_parada_regla_falsa
from .evaluador_funcion import evaluar
from .preparacion_regla_falsa import (
    IntervaloReglaFalsaPreparado,
    preparar_intervalo_regla_falsa,
)
from .traza_regla_falsa import (
    construir_error,
    construir_resultado,
    crear_iteracion,
)
from .validacion_regla_falsa import validar_entrada_regla_falsa


@dataclass(frozen=True)
class _MuestraCruce:
    """Aproximacion de la secante y su evaluacion."""

    c: float
    valor_c: float


@dataclass
class _EstadoIteracion:
    """Intervalo, valores de los extremos y aproximacion previa."""

    inferior: float
    superior: float
    valor_inferior: float
    valor_superior: float
    previo: float | None = None
    valor_previo: float | None = None

    @property
    def intervalo(self) -> tuple[float, float]:
        """Devuelve el par (inferior, superior) del estado."""
        return (self.inferior, self.superior)

    def extremos(self) -> tuple[float, float, float, float]:
        """Devuelve los cuatro valores que recibe crear_iteracion."""
        return (self.inferior, self.superior, self.valor_inferior, self.valor_superior)

    def avanzar(self, fila: IteracionReglaFalsa) -> None:
        """Reemplaza el extremo indicado por el signo del producto y guarda el previo."""
        if fila.signo_producto == -1:
            self.superior, self.valor_superior = fila.aproximacion, fila.valor_aproximacion
        else:
            self.inferior, self.valor_inferior = fila.aproximacion, fila.valor_aproximacion
        self.previo = fila.aproximacion
        self.valor_previo = fila.valor_aproximacion


def regla_falsa(entrada: EntradaReglaFalsa) -> ResultadoReglaFalsa:
    """Resuelve la entrada con regla falsa clasica o devuelve un error del dominio."""
    try:
        if not isinstance(entrada, EntradaReglaFalsa):
            raise ValueError("La entrada debe cumplir el contrato de regla falsa.")
        entrada = validar_entrada_regla_falsa(asdict(entrada))
    except ValueError as error:
        return construir_error(error, codigo="ENTRADA_INVALIDA", motivo="entrada_invalida")
    preparado = preparar_intervalo_regla_falsa(entrada)
    return resolver_intervalo_regla_falsa(preparado)


def resolver_intervalo_regla_falsa(
    preparado: IntervaloReglaFalsaPreparado, criterio: CriterioParada | None = None,
    cero_preferido: float | None = None,
) -> ResultadoReglaFalsa:
    """Ejecuta un intervalo preparado con política opcional ya validada por el llamador."""
    entrada = preparado.entrada
    if preparado.fallo is not None:
        return preparado.fallo
    if preparado.admite_cero:
        resultado = _resultado_raiz_extremo(entrada, preparado)
        if cero_preferido is not None:
            resultado = replace(resultado, aproximacion=cero_preferido,
                                intervalo_final=(cero_preferido, cero_preferido))
        return resultado
    if preparado.restriccion is not None:
        return _resultado_restriccion(entrada, preparado)
    return _iterar(entrada, preparado, criterio)


def _resultado_raiz_extremo(
    entrada: EntradaReglaFalsa, preparado: IntervaloReglaFalsaPreparado
) -> ResultadoReglaFalsa:
    ceros = [evaluacion for evaluacion in preparado.evaluaciones if evaluacion["valor"] == 0]
    extremo = ceros[0]["abscisa"] if ceros else preparado.intervalo[0]
    extras: list[str] = []
    if len(ceros) == 2:
        extras.append("Ambos extremos se evaluan como cero; no se infiere unicidad de la raiz.")
    if preparado.restriccion is not None:
        extras.append(preparado.restriccion["mensaje"])
    advertencias = tuple(dict.fromkeys(entrada.advertencias + tuple(extras)))
    return ResultadoReglaFalsa(
        entrada=entrada,
        estado="EXITO",
        mensaje="La funcion se evaluo como cero en un extremo; no se infiere unicidad.",
        aproximacion=extremo,
        residuo=0.0,
        intervalo_final=(extremo, extremo),
        iteraciones=(),
        iteraciones_totales=0,
        motivo_parada="raiz_en_extremo",
        codigo_diagnostico="RAIZ_EN_EXTREMO",
        advertencias=advertencias,
        informe_continuidad=preparado.informe,
    )


def _resultado_restriccion(
    entrada: EntradaReglaFalsa, preparado: IntervaloReglaFalsaPreparado
) -> ResultadoReglaFalsa:
    advertencias = tuple(dict.fromkeys(
        entrada.advertencias + (preparado.restriccion["mensaje"],)
    ))
    return ResultadoReglaFalsa(
        entrada=entrada,
        estado="ERROR",
        mensaje=preparado.restriccion["mensaje"],
        codigo_diagnostico=preparado.restriccion["codigo"],
        motivo_parada="evaluacion_invalida",
        aproximacion=None,
        residuo=None,
        intervalo_final=preparado.intervalo,
        iteraciones=(),
        iteraciones_totales=0,
        advertencias=advertencias,
        contexto_fallo={"etapa": "estructura", "x_fallo": None, "intervalo_valido": preparado.intervalo},
        informe_continuidad=preparado.informe,
    )


def _iterar(
    entrada: EntradaReglaFalsa, preparado: IntervaloReglaFalsaPreparado,
    criterio: CriterioParada | None = None,
) -> ResultadoReglaFalsa:
    estado = _abrir_iteracion(preparado)
    if estado is None:
        return _sin_cambio_signo(entrada, preparado.informe)
    iteraciones: list[IteracionReglaFalsa] = []
    resultado = _ciclo(entrada, preparado, estado, iteraciones, criterio)
    return replace(resultado, informe_continuidad=preparado.informe)


def _abrir_iteracion(
    preparado: IntervaloReglaFalsaPreparado,
) -> _EstadoIteracion | None:
    inferior, superior = preparado.intervalo
    valor_inferior = preparado.evaluaciones[0]["valor"]
    valor_superior = preparado.evaluaciones[1]["valor"]
    if signo_producto(valor_inferior, valor_superior) != -1:
        return None
    return _EstadoIteracion(inferior, superior, valor_inferior, valor_superior)


def _sin_cambio_signo(
    entrada: EntradaReglaFalsa, informe: InformeContinuidad
) -> ResultadoReglaFalsa:
    return ResultadoReglaFalsa(
        entrada=entrada,
        estado="SIN_CAMBIO_DE_SIGNO",
        mensaje="Los valores f(a) y f(b) tienen el mismo signo. Elige otro intervalo.",
        codigo_diagnostico="SIN_CAMBIO_DE_SIGNO",
        motivo_parada="sin_cambio_de_signo",
        aproximacion=None,
        residuo=None,
        intervalo_final=None,
        iteraciones=(),
        iteraciones_totales=0,
        advertencias=entrada.advertencias,
        informe_continuidad=informe,
    )


def _ciclo(
    entrada: EntradaReglaFalsa,
    preparado: IntervaloReglaFalsaPreparado,
    estado: _EstadoIteracion,
    iteraciones: list[IteracionReglaFalsa],
    criterio: CriterioParada | None = None,
) -> ResultadoReglaFalsa:
    """Itera delegando cada paso en `_paso` y conserva el contexto de fallo."""
    contexto: ContextoFallo = {
        "etapa": "iteracion",
        "x_fallo": None,
        "intervalo_valido": estado.intervalo,
    }
    for indice in range(1, entrada.limite_iteraciones + 1):
        fila, motivo, cruce, error = _paso(entrada, preparado, estado, indice, criterio)
        if error is not None:
            if cruce is not None:
                contexto["x_fallo"] = cruce
            else:
                contexto["etapa"] = "capacidad"
            return _error_contextual(error, contexto, iteraciones)
        iteraciones.append(fila)
        if motivo:
            return construir_resultado(entrada, motivo, iteraciones)
        estado.avanzar(fila)
        contexto["intervalo_valido"] = estado.intervalo
    return construir_resultado(entrada, "limite_iteraciones", iteraciones)


def _paso(
    entrada: EntradaReglaFalsa,
    preparado: IntervaloReglaFalsaPreparado,
    estado: _EstadoIteracion,
    indice: int,
    criterio: CriterioParada | None = None,
) -> tuple[IteracionReglaFalsa | None, str, float | None, ValueError | None]:
    """Ejecuta una iteracion y devuelve (fila, motivo, cruce, error) segun la prioridad de cierre."""
    cruce: float | None = None
    try:
        cruce = punto_cruce(
            estado.inferior, estado.superior, estado.valor_inferior, estado.valor_superior
        )
        valor_cruce = _valor_en_cruce(estado, cruce, preparado)
        fila_base = crear_iteracion(indice, estado.extremos(), (cruce, valor_cruce), estado.previo)
        fila, motivo = decidir_parada_regla_falsa(entrada, fila_base, estado.previo, criterio)
        return fila, motivo, cruce, None
    except ValueError as error:
        return None, "", cruce, error


def _valor_en_cruce(
    estado: _EstadoIteracion, cruce: float, preparado: IntervaloReglaFalsaPreparado
) -> float:
    """Devuelve el valor evaluado, reutilizando el cache si el cruce coincide con extremo o previo."""
    if cruce == estado.inferior:
        return estado.valor_inferior
    if cruce == estado.superior:
        return estado.valor_superior
    if cruce == estado.previo:
        return estado.valor_previo
    return evaluar(preparado.funcion, cruce)


def _error_contextual(
    error: ValueError,
    contexto: ContextoFallo,
    iteraciones: list[IteracionReglaFalsa],
) -> ResultadoReglaFalsa:
    resultado = construir_error(error, iteraciones)
    return replace(
        resultado,
        contexto_fallo=contexto,
        intervalo_final=contexto.get("intervalo_valido"),
    )
