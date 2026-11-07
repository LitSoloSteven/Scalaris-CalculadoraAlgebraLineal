"""Motor clasico de regla falsa (falsa posicion) con la preparacion compartida."""
from dataclasses import asdict, dataclass, replace

from .aritmetica_regla_falsa import punto_cruce
from .contrato_regla_falsa import (
    EntradaReglaFalsa,
    IteracionReglaFalsa,
    ResultadoReglaFalsa,
)
from .decision_biseccion import signo_producto
from .evaluador_funcion import evaluar
from .preparacion_regla_falsa import preparar_intervalo_regla_falsa
from .traza_regla_falsa import (
    _CIERRES,
    construir_error,
    construir_resultado,
    crear_iteracion,
)
from .traza_comun_raices import registrar_accion
from .validacion_regla_falsa import validar_entrada_regla_falsa


@dataclass(frozen=True)
class _MuestraCruce:
    """Aproximacion de la secante y su evaluacion."""

    c: float
    valor_c: float


@dataclass
class _EstadoIteracion:
    """Intervalo y valores de los extremos que la secante esta usando."""

    inferior: float
    superior: float
    valor_inferior: float
    valor_superior: float

    @property
    def intervalo(self) -> tuple[float, float]:
        """Devuelve el par (inferior, superior) del estado."""
        return (self.inferior, self.superior)

    def extremos(self) -> tuple[float, float, float, float]:
        """Devuelve los cuatro valores que recibe crear_iteracion."""
        return (self.inferior, self.superior, self.valor_inferior, self.valor_superior)

    def avanzar(self, fila: IteracionReglaFalsa) -> None:
        """Reemplaza el extremo indicado por el signo del producto."""
        if fila.signo_producto == -1:
            self.superior, self.valor_superior = fila.c, fila.f_c
        else:
            self.inferior, self.valor_inferior = fila.c, fila.f_c


def regla_falsa(entrada: EntradaReglaFalsa) -> ResultadoReglaFalsa:
    """Resuelve la entrada con regla falsa clasica o devuelve un error del dominio."""
    try:
        if not isinstance(entrada, EntradaReglaFalsa):
            raise ValueError("La entrada debe cumplir el contrato de regla falsa.")
        entrada = validar_entrada_regla_falsa(asdict(entrada))
    except ValueError as error:
        return construir_error(error, codigo="ENTRADA_INVALIDA")
    preparado = preparar_intervalo_regla_falsa(entrada)
    if preparado.fallo is not None:
        return _con_advertencias(entrada, _completar_informe(preparado.fallo, preparado.informe))
    if preparado.admite_cero:
        return _con_advertencias(entrada, _resultado_raiz_extremo(entrada, preparado))
    if preparado.restriccion is not None:
        return _con_advertencias(entrada, _resultado_restriccion(preparado))
    return _con_advertencias(entrada, _iterar(entrada, preparado))


def _resultado_raiz_extremo(entrada, preparado) -> ResultadoReglaFalsa:
    extremo = preparado.intervalo[0]
    for evaluacion in preparado.evaluaciones:
        if evaluacion["valor"] == 0:
            extremo = evaluacion["abscisa"]
            break
    return _completar_informe(ResultadoReglaFalsa(
        estado="EXITO",
        mensaje="La funcion se evaluo como cero en un extremo; esto no certifica exactitud simbolica.",
        aproximacion=extremo,
        intervalo_final=preparado.intervalo,
        tolerancia=entrada.tolerancia,
        motivo_parada="raiz_en_extremo",
        codigo_diagnostico="CERO_EVALUADO",
        metricas={"iteraciones_totales": 0, "residuo_final": 0.0},
        unidad_angular=entrada.unidad_angular,
    ), preparado.informe)


def _resultado_restriccion(preparado) -> ResultadoReglaFalsa:
    return _completar_informe(ResultadoReglaFalsa(
        estado="ERROR",
        mensaje=preparado.restriccion["mensaje"],
        codigo_diagnostico=preparado.restriccion["codigo"],
        motivo_parada="evaluacion_invalida",
        intervalo_final=preparado.intervalo,
        metricas={"iteraciones_totales": 0},
        diagnostico=preparado.restriccion,
        contexto_fallo={"etapa": "estructura", "x_fallo": None, "intervalo_valido": preparado.intervalo},
    ), preparado.informe)


def _iterar(entrada, preparado) -> ResultadoReglaFalsa:
    estado = _abrir_iteracion(preparado)
    if estado is None:
        return _completar_informe(_sin_cambio_signo(entrada), preparado.informe)
    iteraciones: list[IteracionReglaFalsa] = []
    return _completar_informe(_ciclo(entrada, preparado, estado, iteraciones), preparado.informe)


def _abrir_iteracion(preparado) -> _EstadoIteracion | None:
    inferior, superior = preparado.intervalo
    valor_inferior = preparado.evaluaciones[0]["valor"]
    valor_superior = preparado.evaluaciones[1]["valor"]
    if signo_producto(valor_inferior, valor_superior) != -1:
        return None
    return _EstadoIteracion(inferior, superior, valor_inferior, valor_superior)


def _sin_cambio_signo(entrada: EntradaReglaFalsa) -> ResultadoReglaFalsa:
    return ResultadoReglaFalsa(
        estado="SIN_CAMBIO_DE_SIGNO",
        mensaje="Los valores f(a) y f(b) tienen el mismo signo. Elige otro intervalo.",
        codigo_diagnostico="SIN_CAMBIO_DE_SIGNO",
        motivo_parada="sin_cambio_signo",
        tolerancia=entrada.tolerancia,
        unidad_angular=entrada.unidad_angular,
    )


def _ciclo(entrada, preparado, estado: _EstadoIteracion, iteraciones) -> ResultadoReglaFalsa:
    contexto = {"etapa": "iteracion", "x_fallo": None, "intervalo_valido": estado.intervalo}
    previo = None
    muestra = _MuestraCruce(estado.inferior, estado.valor_inferior)
    try:
        for indice in range(1, entrada.limite_iteraciones + 1):
            try:
                cruce = punto_cruce(
                    estado.inferior, estado.superior, estado.valor_inferior, estado.valor_superior
                )
            except ValueError:
                contexto["etapa"] = "capacidad"
                raise
            if cruce in (estado.inferior, estado.superior):
                muestra = _MuestraCruce(
                    cruce,
                    estado.valor_inferior if cruce == estado.inferior else estado.valor_superior,
                )
                return _cerrar_estancamiento(entrada, estado, iteraciones, indice, muestra)
            try:
                valor_cruce = evaluar(preparado.funcion, cruce)
            except ValueError:
                contexto["x_fallo"] = cruce
                raise
            muestra = _MuestraCruce(cruce, valor_cruce)
            fila = crear_iteracion(indice, estado.extremos(), (cruce, valor_cruce), previo)
            motivo = _motivo_parada(entrada, fila)
            cierre = registrar_accion(fila, motivo, _CIERRES)
            iteraciones.append(cierre)
            if motivo:
                return construir_resultado(entrada, estado.intervalo, iteraciones, motivo, (cruce, valor_cruce))
            estado.avanzar(cierre)
            previo = cruce
        return construir_resultado(entrada, estado.intervalo, iteraciones, "limite_iteraciones", (muestra.c, muestra.valor_c))
    except ValueError as error:
        return _error_contextual(error, contexto, iteraciones)


def _cerrar_estancamiento(entrada, estado, iteraciones, indice, muestra) -> ResultadoReglaFalsa:
    fila = crear_iteracion(indice, estado.extremos(), (muestra.c, muestra.valor_c), None)
    cierre = registrar_accion(fila, "estancamiento", _CIERRES)
    iteraciones.append(cierre)
    return construir_resultado(entrada, estado.intervalo, iteraciones, "estancamiento", (muestra.c, muestra.valor_c))


def _motivo_parada(entrada: EntradaReglaFalsa, fila: IteracionReglaFalsa) -> str:
    if fila.f_c == 0:
        return "secante_exacta"
    if fila.residuo < entrada.tolerancia:
        return "tolerancia_residuo"
    if fila.i == entrada.limite_iteraciones:
        return "limite_iteraciones"
    return ""


def _completar_informe(resultado: ResultadoReglaFalsa, informe) -> ResultadoReglaFalsa:
    if informe is None:
        return resultado
    return replace(resultado, informe_continuidad=informe)


def _con_advertencias(entrada: EntradaReglaFalsa, resultado: ResultadoReglaFalsa) -> ResultadoReglaFalsa:
    if not entrada.advertencias:
        return resultado
    return replace(
        resultado,
        advertencias=tuple(dict.fromkeys(entrada.advertencias + resultado.advertencias)),
    )


def _error_contextual(error: ValueError, contexto: dict, iteraciones) -> ResultadoReglaFalsa:
    resultado = construir_error(error, iteraciones)
    diagnostico = {
        "codigo": resultado.codigo_diagnostico,
        "origen": contexto["etapa"],
        "mensaje": resultado.mensaje,
    }
    return replace(
        resultado,
        diagnostico=diagnostico,
        contexto_fallo=contexto,
        intervalo_final=contexto.get("intervalo_valido"),
    )