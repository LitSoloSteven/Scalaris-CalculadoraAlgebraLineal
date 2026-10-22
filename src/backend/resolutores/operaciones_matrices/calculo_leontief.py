"""Balance exacto de insumo-producto y menores principales iniciales."""
from fractions import Fraction

from src.backend.modelos.construcciones import identidad
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.calculo_matricial import restar_matrices, multiplicar_matrices
from .determinante import ResolutorDeterminante
from .comprobacion_productos import crear_paso_analisis
from .formateadores import matriz_a_latex
from src.backend.utilidades.formateadores import numero_a_latex
from .comprobacion_leontief import comprobar_balance
from src.backend.resolutores.operaciones_matrices.calculo_inversa import calcular_inversa
from .consistencia_leontief import resolver_balance_singular


def _menores_iniciales(matriz: Matriz) -> tuple[list, list]:
    menores = []
    traza = []
    for orden in range(1, matriz.filas + 1):
        submatriz = Matriz(orden, orden, [fila[:orden] for fila in matriz.datos[:orden]])
        resultado = ResolutorDeterminante.resolver_lu(submatriz)
        determinante = resultado["determinante"]
        menores.append((orden, determinante, determinante > 0))
        for paso in resultado["traza"]:
            detalle = paso.get("detalle_latex", matriz_a_latex(paso["matriz"]))
            traza.append(crear_paso_analisis(f"Menor principal inicial {orden}: {paso['descripcion']}", detalle,
                                           paso["explicacion"], "verificacion"))
        signo = ">" if determinante > 0 else r"\le"
        traza.append(crear_paso_analisis(f"Positividad del menor {orden}", rf"\Delta_{{{orden}}}={numero_a_latex(determinante)}{signo}0",
                                       "El criterio economico de menores principales iniciales de I-C requiere coeficientes tecnicos no negativos.", "verificacion"))
    return menores, traza


def calcular_leontief(coeficientes: Matriz, demanda: list[Fraction]) -> dict:
    """Devuelve matrices, produccion, consumos y menores exactos de coeficientes y demanda compatibles."""
    matriz_identidad = identidad(coeficientes.filas)
    matriz_leontief = restar_matrices(matriz_identidad, coeficientes)
    inversion = calcular_inversa(matriz_leontief)
    multiplicador = inversion["inversa"]
    produccion, consumos = [], []
    if multiplicador is not None:
        demanda_columna = Matriz(coeficientes.filas, 1, [[Fraction(valor)] for valor in demanda])
        produccion_columna = multiplicar_matrices(multiplicador, demanda_columna)
        produccion = [Fraction(fila[0]) for fila in produccion_columna.datos]
        consumo_columna = multiplicar_matrices(coeficientes, produccion_columna)
        consumos = [fila[0] for fila in consumo_columna.datos]
    menores, traza = _menores_iniciales(matriz_leontief)
    calculo = {"identidad": matriz_identidad, "matriz_leontief": matriz_leontief,
            "determinante": inversion["determinante"], "rango": inversion["rango"],
            "multiplicador": multiplicador, "produccion": produccion, "consumos": consumos,
            "balances": [produccion_sector - consumo for produccion_sector, consumo in zip(produccion, consumos)],
            "menores": menores, "es_viable": all(menor[2] for menor in menores),
            "coeficientes_no_negativos": all(valor >= 0 for fila in coeficientes.datos for valor in fila)}
    calculo["traza_comprobacion"] = comprobar_balance(coeficientes, demanda, calculo) + traza
    if multiplicador is None:
        calculo["balance_singular"] = resolver_balance_singular(matriz_leontief, demanda)
    return calculo
