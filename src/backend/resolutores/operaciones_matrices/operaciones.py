"""Operaciones algebraicas fundamentales entre matrices con trazabilidad paso a paso."""

from fractions import Fraction
from typing import Any

from src.backend.constantes import ERROR, EXITO
from src.backend.excepciones import ErrorDiscrepanciaDimension
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.determinante import (
    ResolutorDeterminante,
)
from src.backend.resolutores.trazado import TrazadorPasos
from src.backend.utilidades.formateadores import (
    formatear_fraccion_texto,
    numero_a_latex,
)
from src.backend.utilidades.validadores import (
    ValidadorMatriz,
    validar_dimensiones_multiplicacion,
    validar_mismas_dimensiones,
)


class ResolutorOperacionesMatrices(TrazadorPasos):
    """Ejecuta suma, resta, producto escalar, producto matricial, transpuesta y determinante."""

    def _procesar_celda_binaria(
        self,
        matriz_a: Matriz,
        matriz_b: Matriz,
        resultado: Matriz,
        posicion_operacion: tuple[int, int, str],
    ) -> str:
        """Calcula el valor de la celda y registra el paso correspondiente."""
        r, c, simbolo_operacion = posicion_operacion
        valor_a = matriz_a.obtener(r, c)
        valor_b = matriz_b.obtener(r, c)
        resultado_valor = valor_a + valor_b if simbolo_operacion == "+" else valor_a - valor_b
        resultado.establecer(r, c, resultado_valor)
        a_latex, b_latex, resultado_latex = numero_a_latex(valor_a), numero_a_latex(valor_b), numero_a_latex(resultado_valor)
        detalle = (
            f"C_{{{r+1},{c+1}}} = A_{{{r+1},{c+1}}} {simbolo_operacion} B_{{{r+1},{c+1}}} "
            f"= ({a_latex}) {simbolo_operacion} ({b_latex}) = {resultado_latex}"
        )
        self._registrar_paso(
            f"Celda ({r+1}, {c+1}): {formatear_fraccion_texto(valor_a)} {simbolo_operacion} "
            f"{formatear_fraccion_texto(valor_b)} = {formatear_fraccion_texto(resultado_valor)}",
            matriz_actual=resultado,
            detalle_latex=detalle,
        )
        return detalle

    def _operacion_binaria_elemento_a_elemento(
        self,
        matriz_a: Matriz,
        matriz_b: Matriz,
        *,
        simbolo_operacion: str,
        palabra_operacion: str,
    ) -> dict:
        """Helper para realizar suma o resta celda a celda."""
        self.pasos = []
        try:
            validar_mismas_dimensiones(matriz_a, matriz_b)
        except ValueError as error:
            return {"estado": ERROR, "mensaje": str(error), "matriz_resultado": None, "pasos": []}

        numero_filas, numero_columnas = matriz_a.filas, matriz_a.columnas
        resultado = Matriz(numero_filas, numero_columnas)
        self._registrar_paso(f"Iniciando {palabra_operacion} de matrices {numero_filas}×{numero_columnas}")

        detalles_latex = [
            self._procesar_celda_binaria(matriz_a, matriz_b, resultado, (r, c, simbolo_operacion))
            for r in range(numero_filas)
            for c in range(numero_columnas)
        ]

        return {
            "estado": EXITO,
            "mensaje": f"{palabra_operacion.capitalize()} completada con éxito ({numero_filas}×{numero_columnas}).",
            "matriz_resultado": resultado,
            "pasos": self.pasos,
            "detalles_latex": detalles_latex,
        }

    def sumar(self, matriz_a: Matriz, matriz_b: Matriz) -> dict:
        """Suma matricial elemento a elemento: C_{i,j} = A_{i,j} + B_{i,j}."""
        return self._operacion_binaria_elemento_a_elemento(
            matriz_a, matriz_b, simbolo_operacion="+", palabra_operacion="suma"
        )

    def restar(self, matriz_a: Matriz, matriz_b: Matriz) -> dict:
        """Resta matricial elemento a elemento: C_{i,j} = A_{i,j} - B_{i,j}."""
        return self._operacion_binaria_elemento_a_elemento(
            matriz_a, matriz_b, simbolo_operacion="-", palabra_operacion="resta"
        )

    def multiplicar_escalar(self, escalar: Any, matriz_a: Matriz) -> dict:
        """Multiplica un escalar por una matriz conservando precision exacta."""
        self.pasos = []
        correcto, escalar_frac, error = ValidadorMatriz.parsear_numero_exacto(escalar)
        if not correcto:
            return {"estado": ERROR, "mensaje": f"Escalar inválido: {error}", "matriz_resultado": None, "pasos": []}

        numero_filas, numero_columnas = matriz_a.filas, matriz_a.columnas
        resultado = Matriz(numero_filas, numero_columnas)
        escalar_texto = formatear_fraccion_texto(escalar_frac)
        self._registrar_paso(f"Iniciando multiplicación escalar: {escalar_texto} · A ({numero_filas}×{numero_columnas})")

        detalles_latex = []
        for r in range(numero_filas):
            for c in range(numero_columnas):
                valor_a = matriz_a.obtener(r, c)
                producto = escalar_frac * valor_a
                resultado.establecer(r, c, producto)
                k_latex, a_latex, resultado_latex = numero_a_latex(escalar_frac), numero_a_latex(valor_a), numero_a_latex(producto)
                detalle = f"C_{{{r+1},{c+1}}} = ({k_latex}) \\cdot A_{{{r+1},{c+1}}} = ({k_latex})({a_latex}) = {resultado_latex}"
                detalles_latex.append(detalle)
                self._registrar_paso(
                    f"Celda ({r+1}, {c+1}): {escalar_texto} · {formatear_fraccion_texto(valor_a)} = {formatear_fraccion_texto(producto)}",
                    matriz_actual=resultado,
                    detalle_latex=detalle,
                )

        return {
            "estado": EXITO,
            "mensaje": f"Multiplicación escalar completada con éxito ({numero_filas}×{numero_columnas}).",
            "matriz_resultado": resultado,
            "pasos": self.pasos,
            "detalles_latex": detalles_latex,
        }

    def _calcular_celda_producto(
        self,
        matriz_a: Matriz,
        matriz_b: Matriz,
        r: int,
        c: int,
        numero_columnas: int,
    ) -> tuple[Fraction, str, str]:
        """Calcula el producto punto de una fila y una columna."""
        suma_celda = Fraction(0)
        terminos_texto, terminos_latex = [], []
        for k in range(numero_columnas):
            valor_a = matriz_a.obtener(r, k)
            valor_b = matriz_b.obtener(k, c)
            suma_celda += valor_a * valor_b
            terminos_texto.append(f"({formatear_fraccion_texto(valor_a)})·({formatear_fraccion_texto(valor_b)})")
            terminos_latex.append(f"({numero_a_latex(valor_a)})({numero_a_latex(valor_b)})")

        exp_texto = f"{' + '.join(terminos_texto)} = {formatear_fraccion_texto(suma_celda)}"
        exp_latex = f"C_{{{r+1},{c+1}}} = {' + '.join(terminos_latex)} = {numero_a_latex(suma_celda)}"
        return suma_celda, exp_texto, exp_latex

    def multiplicar(self, matriz_a: Matriz, matriz_b: Matriz) -> dict:
        """Multiplicacion matricial C = A * B con desglose algebraico celda a celda."""
        self.pasos = []
        try:
            validar_dimensiones_multiplicacion(matriz_a, matriz_b)
        except ValueError as error:
            return {"estado": ERROR, "mensaje": str(error), "matriz_resultado": None, "pasos": []}

        numero_filas, numero_intermedias, numero_columnas = matriz_a.filas, matriz_a.columnas, matriz_b.columnas
        resultado = Matriz(numero_filas, numero_columnas)
        self._registrar_paso(
            f"Multiplicación de A ({numero_filas}×{numero_intermedias}) por B ({numero_intermedias}×{numero_columnas}). Matriz resultante C de {numero_filas}×{numero_columnas}."
        )

        detalles_latex = []
        for r in range(numero_filas):
            for c in range(numero_columnas):
                suma_valor, exp_t, exp_l = self._calcular_celda_producto(matriz_a, matriz_b, r, c, numero_intermedias)
                resultado.establecer(r, c, suma_valor)
                detalles_latex.append(exp_l)
                self._registrar_paso(
                    f"Fila {r+1} de A × Columna {c+1} de B: {exp_t}",
                    matriz_actual=resultado,
                    detalle_latex=exp_l,
                )

        return {
            "estado": EXITO,
            "mensaje": f"Multiplicación completada con éxito. Matriz resultante de {numero_filas}×{numero_columnas}.",
            "matriz_resultado": resultado,
            "pasos": self.pasos,
            "detalles_latex": detalles_latex,
        }

    def transponer(self, matriz_a: Matriz) -> Matriz:
        """Devuelve la matriz transpuesta (Aᵀ)_{i,j} = A_{j,i} sin registrar pasos."""
        nuevos_datos = [
            [matriz_a.obtener(i, j) for i in range(matriz_a.filas)]
            for j in range(matriz_a.columnas)
        ]
        return Matriz(matriz_a.columnas, matriz_a.filas, nuevos_datos)

    def determinante(self, matriz_a: Matriz) -> Fraction:
        """Calcula el determinante de una matriz cuadrada delegando en el resolutor LU."""
        if matriz_a.filas != matriz_a.columnas:
            raise ErrorDiscrepanciaDimension(
                "determinante",
                (matriz_a.filas, matriz_a.columnas),
                (matriz_a.filas, matriz_a.filas),
            )
        resultado = ResolutorDeterminante.resolver_lu(matriz_a)
        return resultado["determinante"]
