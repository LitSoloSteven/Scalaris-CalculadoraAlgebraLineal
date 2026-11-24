"""Traza didactica construida desde los calculos exactos ya guardados."""
from fractions import Fraction
from typing import TypedDict

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.compartido.formateadores import matriz_a_latex
from src.backend.utilidades.formato.formateadores import numero_a_latex
from .contrato_adjunta import ComprobacionAdjunta, DetalleCofactor, PasoAdjunta


class ContextoTrazaAdjunta(TypedDict):
    """Instantaneas y resultados exactos que alimentan los pasos sin recalcular."""

    matriz_a: Matriz
    determinante: Fraction
    menores: Matriz
    cofactores: Matriz
    adjunta: Matriz
    inversa: Matriz | None
    detalles: tuple[DetalleCofactor, ...]
    comprobaciones: tuple[ComprobacionAdjunta, ...]
    fila_expansion: int


def construir_traza_adjunta(contexto: ContextoTrazaAdjunta) -> tuple[PasoAdjunta, ...]:
    """Devuelve planteamiento, cofactores, adjunta, division, verificaciones y cierre."""
    pasos = [_paso_planteamiento(0, contexto["matriz_a"])]
    for detalle in contexto["detalles"]:
        pasos.append(_paso_cofactor(len(pasos), detalle))
    pasos.append(_paso_determinante(len(pasos), contexto))
    pasos.append(_paso_cofactores(len(pasos), contexto["cofactores"]))
    pasos.append(_paso_transposicion(len(pasos), contexto["adjunta"]))
    pasos.append(_paso_division(len(pasos), contexto))
    for comprobacion in contexto["comprobaciones"]:
        pasos.append(_paso_verificacion(len(pasos), comprobacion))
    pasos.append(_paso_conclusion(len(pasos), contexto))
    return tuple(pasos)


def _paso(
    indice: int,
    tipo: str,
    descripcion: str,
    explicacion: str,
    **opcional: object,
) -> PasoAdjunta:
    return {
        "indice": indice,
        "tipo": tipo,
        "descripcion": descripcion,
        "explicacion": explicacion,
        "matriz": opcional.get("matriz"),
        "coordenada": opcional.get("coordenada"),
        "valor": opcional.get("valor"),
        "detalle": opcional.get("detalle"),
    }


def _paso_planteamiento(indice: int, matriz_a: Matriz) -> PasoAdjunta:
    detalle = r"A^{-1}=\frac{1}{\det(A)}\operatorname{adj}(A)"
    return _paso(
        indice,
        "planteamiento",
        "Inversa por la matriz adjunta",
        "Calculamos todos los menores y cofactores de A, transponemos la matriz de "
        "cofactores y dividimos entre el determinante solo cuando no es cero.",
        matriz=matriz_a.clonar(),
        detalle=detalle,
    )


def _paso_cofactor(indice: int, detalle_cofactor: DetalleCofactor) -> PasoAdjunta:
    fila = detalle_cofactor["fila"] + 1
    columna = detalle_cofactor["columna"] + 1
    if detalle_cofactor["menor_vacio"]:
        explicacion = (
            "En orden 1 no se construye una matriz de orden 0: el determinante del "
            "menor vacio vale 1 por convencion y el cofactor es ese mismo valor."
        )
        detalle = rf"C_{{{fila},{columna}}}=1,\quad M_{{{fila},{columna}}}\text{{ vacio}}"
    else:
        explicacion = (
            f"Eliminamos la fila {fila} y la columna {columna}. El signo usa los indices "
            "originales de A y conserva el orden de las filas y columnas restantes."
        )
        valor = numero_a_latex(detalle_cofactor["valor_menor"])
        cofactor = numero_a_latex(detalle_cofactor["cofactor"])
        signo = detalle_cofactor["signo"]
        detalle = (
            rf"C_{{{fila},{columna}}}=(-1)^{{{fila}+{columna}}}\det(M_{{{fila},{columna}}})"
            rf"=({signo})({valor})={cofactor}"
        )
    matriz_menor = detalle_cofactor["matriz_menor"]
    return _paso(
        indice,
        "cofactor",
        f"Cofactor C_{{{fila},{columna}}}",
        explicacion,
        matriz=matriz_menor.clonar() if matriz_menor is not None else None,
        coordenada=(detalle_cofactor["fila"], detalle_cofactor["columna"]),
        valor=detalle_cofactor["cofactor"],
        detalle=detalle,
    )


def _paso_determinante(indice: int, contexto: ContextoTrazaAdjunta) -> PasoAdjunta:
    fila = contexto["fila_expansion"]
    matriz_a, cofactores = contexto["matriz_a"], contexto["cofactores"]
    terminos = " + ".join(
        rf"({numero_a_latex(matriz_a.obtener(fila, columna))})"
        rf"({numero_a_latex(cofactores.obtener(fila, columna))})"
        for columna in range(matriz_a.columnas)
    )
    valor = numero_a_latex(contexto["determinante"])
    detalle = rf"\det(A)={terminos}={valor}"
    return _paso(
        indice,
        "determinante",
        f"Determinante por expansion de la fila {fila + 1}",
        "Usamos la fila con mas ceros y los cofactores ya calculados; no repetimos el "
        "arbol de menores para mostrar el resultado.",
        matriz=matriz_a.clonar(),
        valor=contexto["determinante"],
        detalle=detalle,
    )


def _paso_cofactores(indice: int, cofactores: Matriz) -> PasoAdjunta:
    return _paso(
        indice,
        "cofactores",
        "Matriz de cofactores C",
        "Cada entrada conserva el signo de su coordenada y el valor del menor asociado.",
        matriz=cofactores.clonar(),
        detalle=matriz_a_latex(cofactores),
    )


def _paso_transposicion(indice: int, adjunta: Matriz) -> PasoAdjunta:
    return _paso(
        indice,
        "transposicion",
        "Matriz adjunta",
        "La adjunta es la transpuesta de la matriz de cofactores.",
        matriz=adjunta.clonar(),
        detalle=rf"\operatorname{{adj}}(A)=C^T={matriz_a_latex(adjunta)}",
    )


def _paso_division(indice: int, contexto: ContextoTrazaAdjunta) -> PasoAdjunta:
    determinante = contexto["determinante"]
    if contexto["inversa"] is None:
        return _paso(
            indice,
            "division",
            "Determinante nulo: no se divide",
            "Como det(A)=0, la adjunta no produce una inversa; se conserva el "
            "procedimiento completo y se informa la singularidad.",
            matriz=contexto["adjunta"].clonar(),
            valor=determinante,
            detalle=rf"\det(A)=0\Rightarrow A^{{-1}}\text{{ no existe}}",
        )
    detalle = (
        rf"A^{{-1}}=\frac{{1}}{{{numero_a_latex(determinante)}}}"
        rf"{matriz_a_latex(contexto['adjunta'])}={matriz_a_latex(contexto['inversa'])}"
    )
    return _paso(
        indice,
        "division",
        "Division de la adjunta entre el determinante",
        "Dividimos cada cofactor transpuesto entre det(A), que no es cero.",
        matriz=contexto["inversa"].clonar(),
        valor=determinante,
        detalle=detalle,
    )


def _paso_verificacion(indice: int, comprobacion: ComprobacionAdjunta) -> PasoAdjunta:
    producto = comprobacion["producto"]
    return _paso(
        indice,
        "verificacion",
        comprobacion["descripcion"],
        "El producto se compara celda a celda con la matriz esperada usando fracciones "
        "exactas; una diferencia no se redondea ni se oculta.",
        matriz=producto.clonar() if producto is not None else None,
        detalle=comprobacion["detalle_latex"],
    )


def _paso_conclusion(indice: int, contexto: ContextoTrazaAdjunta) -> PasoAdjunta:
    if contexto["inversa"] is None:
        return _paso(
            indice,
            "conclusion",
            "Conclusion: la matriz es singular",
            "El determinante es cero y la comprobacion A·adj(A)=det(A)·I se cumple; "
            "no existe inversa por adjunta.",
            matriz=contexto["adjunta"].clonar(),
            valor=contexto["determinante"],
            detalle=rf"\det(A)=0,\quad \operatorname{{adj}}(A)={matriz_a_latex(contexto['adjunta'])}",
        )
    return _paso(
        indice,
        "conclusion",
        "Conclusion: inversa calculada y comprobada",
        "Los dos productos con la identidad coinciden de forma exacta, asi que la "
        "candidata queda certificada como inversa.",
        matriz=contexto["inversa"].clonar(),
        valor=contexto["determinante"],
        detalle=rf"A^{{-1}}={matriz_a_latex(contexto['inversa'])}",
    )
