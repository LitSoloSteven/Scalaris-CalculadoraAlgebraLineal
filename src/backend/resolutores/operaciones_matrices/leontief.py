"""Resolutor del Modelo de Insumo-Producto de Leontief con viabilidad de Hawkins-Simon."""

from fractions import Fraction

from src.backend.constantes import CERO_EPSILON, ERROR, EXITO, SINGULAR
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
)
from src.backend.utilidades.formateadores import formatear_fraccion_texto


class ResolutorModeloLeontief:
    """Modela sistemas economicos insumo-producto (I - C) x = d calculando produccion total."""

    def __init__(self, eps: float = CERO_EPSILON) -> None:
        """Inicializa el resolutor con operaciones matriciales e inversion."""
        self.eps = eps
        self._operaciones_matrices = ResolutorOperacionesMatrices()
        self._inv = ResolutorInversa()

    def _identidad(self, dimension: int) -> Matriz:
        """Genera una matriz identidad de orden n."""
        return Matriz(dimension, dimension, [[Fraction(1 if i == j else 0) for j in range(dimension)] for i in range(dimension)])

    def _hawkins_simon(self, matriz_leontief: Matriz, dimension: int) -> dict:
        """Verifica la condicion de viabilidad economica calculando menores principales."""
        menores = []
        es_viable = True
        for k in range(1, dimension + 1):
            sub_datos = [[matriz_leontief.obtener(i, j) for j in range(k)] for i in range(k)]
            sub_m = Matriz(k, k, sub_datos)
            determinante_k = self._operaciones_matrices.determinante(sub_m)
            pos = determinante_k > 0
            if not pos:
                es_viable = False
            menores.append({
                "orden": k,
                "determinante": formatear_fraccion_texto(determinante_k),
                "es_positivo": pos,
            })
        return {
            "es_economicamente_viable": es_viable,
            "menores_principales": menores,
            "conclusion": _conclusion_viabilidad(es_viable, menores),
        }

    def _analisis_sectorial(
        self,
        matriz_c: Matriz,
        vector_produccion: list[Fraction],
        vector_demanda: list[Fraction],
        sectores: list[str],
    ) -> list[dict]:
        """Calcula el consumo intermedio y valor anadido para cada sector economico."""
        dimension = matriz_c.filas
        tabla = []
        for i in range(dimension):
            producto_i = vector_produccion[i]
            dem_i = vector_demanda[i]
            consumo_intermedio = sum(matriz_c.obtener(i, j) * vector_produccion[j] for j in range(dimension))
            valor_anadido = producto_i - consumo_intermedio
            tabla.append({
                "sector": sectores[i],
                "produccion_total": formatear_fraccion_texto(producto_i),
                "demanda_final": formatear_fraccion_texto(dem_i),
                "consumo_intermedio": formatear_fraccion_texto(consumo_intermedio),
                "valor_anadido": formatear_fraccion_texto(valor_anadido),
            })
        return tabla

    @staticmethod
    def _validar_dimensiones(matriz_c: Matriz, vector_demanda: list[Fraction]) -> str | None:
        """Verifica que la matriz sea cuadrada y concuerde con el vector de demanda."""
        if matriz_c.filas != matriz_c.columnas:
            return "La matriz de coeficientes debe ser cuadrada (n×n)."
        if len(vector_demanda) != matriz_c.filas:
            return f"El vector de demanda debe tener {matriz_c.filas} componentes; se recibieron {len(vector_demanda)}."
        return None

    def _empaquetar_exito(
        self,
        matrices: tuple[Matriz, Matriz, Matriz, Matriz],
        datos: tuple[list[Fraction], list[Fraction], list[str], Fraction],
        pasos: list[dict],
    ) -> dict:
        """Construye el diccionario de resultado exitoso del modelo de Leontief."""
        matriz_c, identidad, matriz_leontief, multiplicador = matrices
        vector_produccion, vector_demanda, sectores, determinante_m = datos
        dimension = matriz_c.filas
        mensaje_resultado = f"Modelo de Leontief resuelto correctamente ({dimension} sectores)."
        return {
            "estado": EXITO,
            "mensaje": mensaje_resultado,
            "numero_sectores": dimension,
            "nombres_sectores": sectores,
            "determinante_leontief": formatear_fraccion_texto(determinante_m),
            "matriz_leontief_latex": matriz_a_latex(matriz_leontief),
            "matriz_multiplicador_latex": matriz_a_latex(multiplicador),
            "matriz_identidad_latex": matriz_a_latex(identidad),
            "vector_produccion": [formatear_fraccion_texto(valor) for valor in vector_produccion],
            "vector_demanda": [formatear_fraccion_texto(valor) for valor in vector_demanda],
            "hawkins_simon": self._hawkins_simon(matriz_leontief, dimension),
            "analisis_sectorial": self._analisis_sectorial(
                matriz_c, vector_produccion, vector_demanda, sectores
            ),
            "pasos": pasos,
        }

    def _resultado_singular(
        self, matriz_leontief: Matriz, dimension: int, sectores: list[str], determinante_m: Fraction
    ) -> dict:
        """Genera la respuesta cuando la matriz de Leontief es singular."""
        mensaje_resultado = "det(I − C) = 0. El sistema de Leontief es singular: no existe multiplicador (la economía no tiene solución única)."
        return {
            "estado": SINGULAR,
            "mensaje": mensaje_resultado,
            "numero_sectores": dimension,
            "nombres_sectores": sectores,
            "determinante_leontief": str(determinante_m),
            "hawkins_simon": self._hawkins_simon(matriz_leontief, dimension),
            "pasos": [],
        }

    def _calcular_produccion(
        self, multiplicador: Matriz, vector_demanda: list[Fraction], dimension: int
    ) -> list[Fraction]:
        """Calcula el vector de producción x = (I - C)^-1 d."""
        d_columna = Matriz(dimension, 1, [[Fraction(valor)] for valor in vector_demanda])
        x_columna = self._operaciones_matrices.multiplicar(multiplicador, d_columna)["matriz_resultado"]
        return [Fraction(x_columna.obtener(i, 0)) for i in range(dimension)]

    def resolver(
        self,
        matriz_coeficientes: Matriz,
        vector_demanda: list[Fraction],
        nombres_sectores: list[str] | None = None,
    ) -> dict:
        """Resuelve el sistema x = (I - C)^-1 d y genera el analisis sectorial."""
        error = self._validar_dimensiones(matriz_coeficientes, vector_demanda)
        if error:
            return {"estado": ERROR, "mensaje": error}

        dimension = matriz_coeficientes.filas
        sectores = (
            nombres_sectores
            if (nombres_sectores and len(nombres_sectores) == dimension)
            else [f"Sector {i + 1}" for i in range(dimension)]
        )
        identidad = self._identidad(dimension)
        matriz_leontief = self._operaciones_matrices.restar(identidad, matriz_coeficientes)["matriz_resultado"]
        determinante_m = self._operaciones_matrices.determinante(matriz_leontief)

        if abs(determinante_m) < self.eps:
            return self._resultado_singular(matriz_leontief, dimension, sectores, determinante_m)

        resultado_inversa = self._inv.resolver(matriz_leontief, construir_detalle_latex=False)
        if resultado_inversa["estado"] != EXITO:
            mensaje_resultado = f"No se pudo invertir (I − C): {resultado_inversa.get('mensaje', '')}."
            return {"estado": ERROR, "mensaje": mensaje_resultado}
        multiplicador = resultado_inversa["inversa"]
        vector_produccion = self._calcular_produccion(multiplicador, vector_demanda, dimension)

        return self._empaquetar_exito(
            (matriz_coeficientes, identidad, matriz_leontief, multiplicador),
            (vector_produccion, vector_demanda, sectores, determinante_m),
            [],
        )


def _conclusion_viabilidad(es_viable: bool, menores: list[dict]) -> str:
    """Explica la viabilidad conservando los órdenes de los menores no positivos."""
    if es_viable:
        return (
            "✓ Se satisface la condición de Hawkins-Simon: todos los menores "
            "principales de (I − C) son positivos. La economía puede producir "
            "cualquier vector de demanda final positivo."
        )
    fallidos = [menor["orden"] for menor in menores if not menor["es_positivo"]]
    return (
        "✗ No se satisface la condición de Hawkins-Simon: los menores de "
        f"orden {fallidos} no son positivos. El modelo puede ser inviable "
        "para ciertos vectores de demanda."
    )
