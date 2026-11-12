"""Secuencia pedagógica que conserva filas, estado y cierre del motor."""
from dataclasses import replace

from src.ai.contexto import CapturaPaso, ReferenciaPaso
from src.frontend.componentes.reproductor_pasos.modelo import GrupoReproductor, PasoReproductor
from src.frontend.controladores.biseccion.presentacion import numero
from .presentacion import titulo_estado
from .tabla import ACCIONES


def construir_pasos(respuesta: dict) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Devuelve planteamiento, filas válidas y cierre, incluso ante un error sin entrada."""
    entrada = respuesta.get("entrada")
    descripcion = "Intervalo y tolerancia de residuo"
    if entrada:
        descripcion = f"f(x) = {entrada['expresion']} · tolerancia {numero(entrada['tolerancia'], True)}"
    pasos = [PasoReproductor(0, "planteamiento", descripcion,
                            "La garantía requiere continuidad y encierro; el residuo no es una cota del error en x.")]
    pasos.extend(_paso_iteracion(fila, indice) for indice, fila in enumerate(respuesta["iteraciones"], 1))
    ultima = respuesta["iteraciones"][-1] if respuesta["iteraciones"] else None
    pasos.append(PasoReproductor(len(pasos), "final", titulo_estado(respuesta), respuesta["mensaje"], 2, ultima))
    pasos = tuple(replace(paso, meta_explicar={
        "indice": paso.indice + 1, "total": len(pasos), "tipo": paso.tipo,
        "operacion": paso.descripcion, "detalle": {"explicacion": paso.explicacion, "iteracion": paso.cuerpo},
    }) for paso in pasos)
    grupos = (
        GrupoReproductor("Planteamiento", "Intervalo y continuidad", "planteamiento", (0,)),
        GrupoReproductor("Secantes", "Aproximaciones registradas", "sustitucion", tuple(range(1, len(pasos) - 1))),
        GrupoReproductor("Cierre", titulo_estado(respuesta), "final", (len(pasos) - 1,)),
    )
    return pasos, grupos


def _paso_iteracion(fila: dict, indice: int) -> PasoReproductor:
    return PasoReproductor(indice, "sustitucion",
                          f"Iteración {fila['i']}: c ≈ {numero(fila['aproximacion'], True)}",
                          f"El motor registra: {ACCIONES[fila['accion']]}. Residuo |f(c)| = {numero(fila['residuo'], True)}.",
                          1, fila, "Secante")


def referencia_paso(paso: PasoReproductor, total: int) -> ReferenciaPaso:
    """Devuelve un foco pedagógico con el mismo índice, explicación y fila que el paso visible."""
    return ReferenciaPaso(indice=paso.indice + 1, total=total, tipo=paso.tipo, operacion=paso.descripcion,
                          captura=CapturaPaso(detalle={"explicacion": paso.explicacion, "iteracion": paso.cuerpo}))
