"""Desarrollo del balance de Leontief y su comparacion con la demanda original."""
from src.backend.modelos.matriz import Matriz
from fractions import Fraction
from src.backend.utilidades.formateadores import numero_a_latex
from .comprobacion_productos import comprobar_producto, crear_paso_analisis


def comprobar_balance(coeficientes: Matriz, demanda: list, calculo: dict) -> list[dict]:
    """Comprueba (I-C)x=d y desarrolla x_i=(Cx)_i+d_i para todos los sectores."""
    if calculo["multiplicador"] is None:
        return []
    demanda = [Fraction(valor) for valor in demanda]
    produccion = Matriz(len(demanda), 1, [[valor] for valor in calculo["produccion"]])
    objetivo = Matriz(len(demanda), 1, [[valor] for valor in demanda])
    comprobacion = comprobar_producto(calculo["matriz_leontief"], produccion, objetivo, "(I-C)x=d")
    traza = comprobacion["traza"]
    for indice, fila in enumerate(coeficientes.datos):
        terminos = "+".join(rf"({numero_a_latex(valor)})({numero_a_latex(peso)})"
                            for valor, peso in zip(fila, calculo["produccion"]))
        consumo = calculo["consumos"][indice]
        total = consumo + demanda[indice]
        produccion_sector = calculo["produccion"][indice]
        simbolo = "=" if total == produccion_sector else r"\ne"
        detalle = (rf"x_{{{indice+1}}}=(Cx)_{{{indice+1}}}+d_{{{indice+1}}}:\quad "
                   rf"{terminos}+({numero_a_latex(demanda[indice])})={numero_a_latex(consumo)}"
                   rf"+({numero_a_latex(demanda[indice])})={numero_a_latex(total)}{simbolo}{numero_a_latex(produccion_sector)}")
        traza.append(crear_paso_analisis(f"Balance del sector {indice+1}", detalle,
                                       "La produccion debe cubrir el consumo intermedio mas la demanda final.", "verificacion"))
    return traza
