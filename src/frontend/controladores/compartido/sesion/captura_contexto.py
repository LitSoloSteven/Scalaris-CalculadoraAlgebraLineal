"""Capturas inmutables de entradas usadas al registrar y comparar huellas."""


def capturar_matrices(matrices: dict, expresion: str) -> dict:
    """Copia las celdas de cada matriz y recorta la expresión para comparar entradas."""
    return {
        'matrices': {nombre: dict(matriz.get('cache', {})) for nombre, matriz in matrices.items()},
        'expresion': (expresion or '').strip(),
    }


def capturar_matrices_documento(matrices: dict, expresion: str) -> dict:
    """Conserva dimensiones y representa vacíos como ceros en la entrada documental."""
    return {'expresion': expresion, 'matrices': {
        nombre: [[valor or '0' for valor in fila] for fila in matriz['datos']]
        for nombre, matriz in matrices.items()}}


def capturar_bases(vista, valor: str) -> dict:
    """Devuelve el valor íntegro y las bases activas del conversor para su huella."""
    return {'valor': valor, 'base_origen': vista.base_activa, 'base_destino': vista.base_destino}


def capturar_romanos(operando_a: str, operando_b: str, operacion: str) -> dict:
    """Normaliza ambos operandos romanos y conserva la operación para su huella."""
    return {
        'a': (operando_a or '').strip().upper(),
        'b': (operando_b or '').strip().upper(),
        'operacion': operacion,
    }
