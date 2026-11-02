"""Agrupación visual de secuencias ya calculadas por el dominio."""


def agrupar_traza(traza: list[dict], identificar) -> tuple[list[dict], tuple[int, ...]]:
    """Devuelve fases contiguas e índice de fase por paso mediante identificar(paso, índice)."""
    grupos = []
    posiciones = []
    anterior = None
    for indice, paso in enumerate(traza):
        clave, titulo, tipo = identificar(paso, indice)
        if not grupos or clave != anterior:
            grupos.append({"titulo": titulo, "tipo": tipo, "indices_pasos": []})
        grupos[-1]["indices_pasos"].append(indice)
        posiciones.append(len(grupos) - 1)
        anterior = clave
    return grupos, tuple(posiciones)
