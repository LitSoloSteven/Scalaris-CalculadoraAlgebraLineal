"""Presentacion matematica de la expansion, generada junto al dominio."""
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex


def construir_traza_cofactores(matriz: Matriz, expansion: dict) -> list[dict]:
    """Devuelve planteamiento, un paso por menor y suma exacta, sin recalcularlos."""
    fila = expansion["fila"]
    ceros = matriz.datos[fila - 1].count(0)
    explicacion = (
        f"Expandimos por la fila {fila}, con {ceros} ceros, la mayor cantidad entre las filas. "
        "En empates elegimos la primera. Cada menor conserva el orden de las filas y columnas restantes."
    )
    formula = rf"\det(A)=\sum_{{j=1}}^{{{matriz.columnas}}}a_{{{fila}j}}(-1)^{{{fila}+j}}\det(M_{{{fila}j}})"
    if matriz.filas == 1:
        formula = r"\det(A)=a_{11}"
        explicacion = "Una matriz de orden 1 tiene como determinante su unico elemento; no construimos un menor vacio."
    pasos = [{"tipo": "planteamiento", "descripcion": f"Expansion por la fila {fila}",
              "explicacion": explicacion, "matriz": matriz.clonar(), "fila_elegida": fila,
              "detalle_latex": formula}]
    for menor in expansion["menores"]:
        pasos.append(_paso_menor(matriz, menor))
    terminos = " + ".join(f"({numero_a_latex(menor['termino'])})" for menor in expansion["menores"])
    valor = numero_a_latex(expansion["determinante"])
    detalle = rf"\det(A)={terminos}={valor}" if terminos else rf"\det(A)=a_{{11}}={valor}"
    pasos.append({"tipo": "final", "descripcion": "Resultado exacto de la expansion",
                  "explicacion": "Sumamos los terminos de la fila elegida." if terminos else "En orden 1 el determinante es el unico elemento; no hay menores.",
                  "detalle_latex": detalle})
    return pasos


def _paso_menor(matriz: Matriz, menor: dict) -> dict:
    fila, columna = menor["fila"], menor["columna"]
    indice = f"{{{fila},{columna}}}"
    elemento = numero_a_latex(menor["elemento"])
    valor = numero_a_latex(menor["valor_menor"])
    cofactor = numero_a_latex(menor["cofactor"])
    termino = numero_a_latex(menor["termino"])
    acumulado = numero_a_latex(menor["acumulado"])
    detalle = (
        rf"\det(M_{indice})={valor},\quad (-1)^{{{fila}+{columna}}}={menor['signo']},\quad "
        rf"C_{indice}=({menor['signo']})({valor})={cofactor},\quad "
        rf"a_{indice}C_{indice}=({elemento})({cofactor})={termino},\quad S_{{{columna}}}={acumulado}"
    )
    return {"tipo": "menor", "descripcion": f"Menor de la fila {fila}, columna {columna}",
            "explicacion": f"Eliminamos la fila {fila} y la columna {columna}. El signo usa estos indices de A, no los indices renumerados del menor.",
            "matriz": matriz.clonar(), "fila_elegida": fila, "elemento_actual": (fila, columna),
            "menor": menor, "detalle_latex": detalle}
