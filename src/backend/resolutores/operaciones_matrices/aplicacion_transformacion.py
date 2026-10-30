"""Cálculo exacto de la aplicación lineal T(v) = Av para transformaciones."""
import math
from fractions import Fraction

from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex
from .comprobacion_productos import crear_paso_analisis

def aplicar_vector(matriz: Matriz, vector: Matriz) -> dict:
    """Calcula T(v) = A·v con exactitud racional y devuelve el contrato serializable."""
    _validar_dimensiones(matriz, vector)
    resultado = _multiplicar_matriz_vector(matriz, vector)
    pasos = _construir_pasos(matriz, vector, resultado)
    
    return {
        "estado": "EXITO",
        "mensaje": f"Transformación aplicada correctamente (R^{matriz.columnas} → R^{matriz.filas}).",
        "matriz_a": matriz,
        "vector_original": _serializar_vector(vector),
        "vector_transformado": _serializar_vector(resultado),
        "aproximacion": False,
        "pasos": pasos,
    }

def _validar_dimensiones(matriz: Matriz, vector: Matriz) -> None:
    """Verifica que A sea m×n y v sea n×1, lanzando error si no coinciden."""
    if not isinstance(matriz, Matriz) or not isinstance(vector, Matriz):
        raise ValueError("La matriz y el vector deben ser instancias de Matriz.")
    if vector.columnas != 1:
        raise ValueError("El vector debe ser una matriz columna (n×1).")
    if matriz.columnas != vector.filas:
        raise ErrorDiscrepanciaDimension(
            "aplicación T(v)=Av",
            forma_a=(matriz.filas, matriz.columnas),
            forma_b=(vector.filas, vector.columnas),
        )

def _multiplicar_matriz_vector(matriz: Matriz, vector: Matriz) -> Matriz:
    """Multiplica A por v celda a celda usando Fraction."""
    datos = []
    for fila in range(matriz.filas):
        suma = sum(
            (matriz.obtener(fila, col) * vector.obtener(col, 0) for col in range(matriz.columnas)),
            start=Fraction(0),
        )
        datos.append([suma])
    return Matriz(matriz.filas, 1, datos)

def _serializar_vector(vector: Matriz) -> dict:
    """Devuelve las componentes del vector en formato exacto y aproximado."""
    exacta = [str(vector.obtener(i, 0)) for i in range(vector.filas)]
    aproximado = [float(vector.obtener(i, 0)) for i in range(vector.filas)]
    return {"aproximado": aproximado, "exacta": exacta}

def _construir_pasos(matriz: Matriz, vector: Matriz, resultado: Matriz) -> list[dict]:
    """Genera los pasos detallados de la multiplicación fila por columna."""
    pasos = []
    for fila in range(matriz.filas):
        detalle_latex = _latex_fila(matriz, vector, resultado, fila)
        descripcion = f"Cálculo de la componente y_{{{fila + 1}}}"
        pasos.append(crear_paso_analisis(descripcion, detalle_latex, tipo="operacion"))
    return pasos

def _latex_fila(matriz: Matriz, vector: Matriz, resultado: Matriz, fila: int) -> str:
    """Formatea en LaTeX el producto de la fila i de A por el vector v."""
    terminos = [
        f"({numero_a_latex(matriz.obtener(fila, col))})({numero_a_latex(vector.obtener(col, 0))})"
        for col in range(matriz.columnas)
    ]
    suma_latex = " + ".join(terminos)
    valor_final = numero_a_latex(resultado.obtener(fila, 0))
    return f"y_{{{fila + 1}}} = {suma_latex} = {valor_final}"

def matriz_rotacion(grados: Fraction | int | str) -> tuple[Matriz, bool]:
    """Devuelve la matriz de rotación en R2 y si es exacta (múltiplos de 90°)."""
    angulo = Fraction(grados)
    if angulo % 90 == 0:
        return _rotacion_exacta(angulo), True
    return _rotacion_aproximada(float(angulo)), False


def _rotacion_exacta(angulo: Fraction) -> Matriz:
    """Construye la matriz exacta para múltiplos de 90 grados."""
    grados_efectivos = int(angulo % 360)
    uno, cero, menos_uno = Fraction(1), Fraction(0), Fraction(-1)
    if grados_efectivos == 0:
        return Matriz(2, 2, [[uno, cero], [cero, uno]])
    if grados_efectivos == 90:
        return Matriz(2, 2, [[cero, menos_uno], [uno, cero]])
    if grados_efectivos == 180:
        return Matriz(2, 2, [[menos_uno, cero], [cero, menos_uno]])
    return Matriz(2, 2, [[cero, uno], [menos_uno, cero]])


def _rotacion_aproximada(grados_float: float) -> Matriz:
    """Construye la matriz de rotación aproximada usando trigonometría."""
    radianes = math.radians(grados_float)
    coseno = math.cos(radianes)
    seno = math.sin(radianes)
    return Matriz(2, 2, [[coseno, -seno], [seno, coseno]])


def matriz_reflexion(eje: str = "x") -> Matriz:
    """Devuelve la matriz de reflexión exacta respecto al eje indicado."""
    matrices = {
        "x": [[1, 0], [0, -1]],
        "y": [[-1, 0], [0, 1]],
        "y=x": [[0, 1], [1, 0]],
        "y = x": [[0, 1], [1, 0]],
        "y=-x": [[0, -1], [-1, 0]],
        "y = -x": [[0, -1], [-1, 0]],
        "origen": [[-1, 0], [0, -1]],
    }
    if eje not in matrices:
        raise ValueError("Eje no válido. Usa 'x', 'y', 'y=x', 'y=-x' u 'origen'.")
    return Matriz(2, 2, matrices[eje])


def matriz_escala(kx: Fraction | int, ky: Fraction | int) -> Matriz:
    """Devuelve la matriz de escala exacta por los factores dados."""
    return Matriz(2, 2, [[Fraction(kx), 0], [0, Fraction(ky)]])


def matriz_cizalladura(k: Fraction | int, eje: str = "x") -> Matriz:
    """Devuelve la matriz de cizalladura exacta."""
    k_frac = Fraction(k)
    if eje == "x":
        return Matriz(2, 2, [[1, k_frac], [0, 1]])
    elif eje == "y":
        return Matriz(2, 2, [[1, 0], [k_frac, 1]])
    else:
        raise ValueError("Eje de cizalladura debe ser 'x' o 'y'.")