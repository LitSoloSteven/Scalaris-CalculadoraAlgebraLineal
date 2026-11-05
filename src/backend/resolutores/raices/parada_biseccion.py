"""Decisiones y comprobaciones del criterio activo sobre las filas del motor."""
from dataclasses import replace

from .contrato_biseccion import ESTADO_DISCONTINUIDAD, EntradaBiseccion, IteracionBiseccion, ResultadoBiseccion
from .criterios_biseccion import CriterioParada

_MOTIVOS = {"relativo": "relativo_menor_que_porcentaje", "ancho": "ancho_menor_que_E",
            "decimales": "ancho_menor_que_E", "residuo": "residuo_menor_que_delta",
            "iteraciones": "iteraciones_completadas"}


def metrica_criterio(criterio: CriterioParada, fila: IteracionBiseccion) -> float | int | None:
    """Devuelve la métrica sin redondear; el relativo indefinido conserva None."""
    valores = {"relativo": fila.error_relativo_valor, "ancho": fila.ancho,
               "decimales": fila.ancho, "residuo": fila.residuo, "iteraciones": fila.i}
    return valores[criterio.tipo]


def motivo_criterio(criterio: CriterioParada, fila: IteracionBiseccion) -> str:
    """Devuelve el motivo ordinario si la fila satisface únicamente el criterio elegido."""
    metrica = metrica_criterio(criterio, fila)
    if criterio.tipo == "iteraciones":
        cumplido = metrica == criterio.parametro
    else:
        cumplido = metrica is not None and metrica < criterio.umbral
    return _MOTIVOS[criterio.tipo] if cumplido else ""


def completar_criterio(entrada: EntradaBiseccion, resultado: ResultadoBiseccion) -> ResultadoBiseccion:
    """Añade solicitud, unidad, umbral y métrica final a un resultado de entrada validada."""
    criterio = entrada.criterio_activo
    if resultado.iteraciones:
        metrica = metrica_criterio(criterio, resultado.iteraciones[-1])
    else:
        metrica = _metrica_sin_filas(criterio, resultado)
    umbral = criterio.parametro if criterio.tipo == "iteraciones" else float(criterio.umbral)
    return replace(resultado, criterio_solicitado=criterio, unidad_criterio=criterio.unidad,
                   umbral=umbral, metrica_final=metrica)


def comprobar_cierre_criterio(resultado: ResultadoBiseccion) -> None:
    """Comprueba un cierre ordinario contra su última fila; lanza ValueError si es incoherente."""
    if resultado.estado not in {"EXITO", "ITERACIONES_COMPLETADAS", ESTADO_DISCONTINUIDAD}:
        return
    provisional = resultado.estado == ESTADO_DISCONTINUIDAD
    if not provisional and resultado.motivo_parada == "raiz_exacta":
        return
    criterio = resultado.criterio_solicitado
    if criterio is None or not resultado.iteraciones:
        raise ValueError("El resultado no contiene el criterio y la fila de cierre.")
    if provisional and resultado.motivo_parada in {"estancamiento", "limite_iteraciones"}:
        return
    _comprobar_metrica_cierre(resultado, criterio)


def _comprobar_metrica_cierre(resultado: ResultadoBiseccion, criterio: CriterioParada) -> None:
    motivo = motivo_criterio(criterio, resultado.iteraciones[-1])
    estado = "ITERACIONES_COMPLETADAS" if criterio.tipo == "iteraciones" else "EXITO"
    if not motivo or resultado.motivo_parada != motivo or resultado.estado not in {estado, ESTADO_DISCONTINUIDAD}:
        raise ValueError("El motor no cumplió el criterio de parada solicitado.")


def _metrica_sin_filas(criterio: CriterioParada, resultado: ResultadoBiseccion) -> float | int | None:
    if resultado.aproximacion is None:
        return None
    if criterio.tipo == "iteraciones":
        return 0
    if criterio.tipo == "residuo":
        return resultado.metricas.get("residuo_final")
    if criterio.tipo in {"ancho", "decimales"} and resultado.intervalo_final is not None:
        inferior, superior = resultado.intervalo_final
        return superior - inferior
    return None
