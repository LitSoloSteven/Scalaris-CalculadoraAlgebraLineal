"""Resolutor de matriz inversa mediante Gauss-Jordan sobre [A | I] con verificacion."""

from fractions import Fraction

from src.backend.constantes import ERROR, EXITO, SINGULAR
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import (
    matriz_a_latex,
    matriz_particionada_a_latex,
)
from src.backend.resolutores.operaciones_matrices.operaciones import (
    ResolutorOperacionesMatrices,
)
from src.backend.resolutores.sistemas_lineales.gauss_jordan import (
    ResolutorGaussJordan,
)


def _construir_identidad(dimension: int) -> Matriz:
    datos = [[Fraction(1 if i == j else 0) for j in range(dimension)]
             for i in range(dimension)]
    return Matriz(dimension, dimension, datos)


class ResolutorInversa:
    """Calcula la matriz inversa A^-1 con desgloses, pasos y verificaciones algebraicas."""

    def __init__(self) -> None:
        """Inicializa el resolutor con soporte de operaciones matriciales."""
        self.resolutor_operaciones_matrices = ResolutorOperacionesMatrices()

    def _construir_aumentada(self, matriz_a: Matriz, dimension: int) -> tuple[Matriz, str]:
        """Construye la matriz [A | I] de tamano n x 2n."""
        datos = []
        for i in range(dimension):
            fila = [matriz_a.obtener(i, j) for j in range(dimension)]
            fila.extend(Fraction(1) if i == j else Fraction(0) for j in range(dimension))
            datos.append(fila)
        aumentada = Matriz(dimension, 2 * dimension, datos)
        return aumentada, matriz_particionada_a_latex(aumentada, dimension)

    def _extraer_inversa(self, reducida: Matriz, dimension: int) -> Matriz:
        """Extrae el bloque derecho n x n de la matriz reducida [I | A^-1]."""
        datos = [
            [reducida.obtener(i, dimension + j) for j in range(dimension)]
            for i in range(dimension)
        ]
        return Matriz(dimension, dimension, datos)

    def _formatear_pasos(self, pasos: list[dict], dimension: int, construir_latex: bool) -> list[dict]:
        """Formatea los pasos con matriz particionada en LaTeX si se solicita."""
        formateados = []
        for indice, paso in enumerate(pasos):
            matriz = paso.get("matriz")
            latex = matriz_particionada_a_latex(matriz, dimension) if (matriz and construir_latex) else None
            desc = paso.get("descripcion", "")
            if indice == 0:
                desc = desc.replace("[A|b]", "[A|I]")
            formateados.append({
                "descripcion": desc,
                "matriz": matriz,
                "detalle_latex": latex,
            })
        return formateados

    def _verificar_producto(
        self,
        matriz_a: Matriz,
        inversa: Matriz,
        dimension: int,
        inverso: bool,
    ) -> dict:
        """Verifica que el producto A · A^-1 o A^-1 · A coincida con la identidad."""
        izquierda = inversa if inverso else matriz_a
        derecha = matriz_a if inverso else inversa
        resultado = self.resolutor_operaciones_matrices.multiplicar(izquierda, derecha)
        producto = resultado.get("matriz_resultado")
        identidad = _construir_identidad(dimension)
        es_exacto = producto.datos == identidad.datos if producto else False
        etiq = "A^{-1} \\cdot A = I" if inverso else "A \\cdot A^{-1} = I"
        palabra_estado = "Correcto" if es_exacto else "Incorrecto"
        izquierda_nombre = "A^{-1}" if inverso else "A"
        derecha_nombre = "A" if inverso else "A^{-1}"
        producto_latex = matriz_a_latex(producto) if producto else ""
        detalle_latex = f"{izquierda_nombre} \\cdot {derecha_nombre} = {producto_latex} \\quad (\\text{{{palabra_estado}}})"
        desc = f"Verificación {'A⁻¹·A' if inverso else 'A·A⁻¹'} = I."
        return {
            "propiedad": etiq,
            "nombre_izquierdo": izquierda_nombre,
            "nombre_derecho": derecha_nombre,
            "descripcion": desc,
            "se_cumple": es_exacto,
            "coincide": es_exacto,
            "matriz_producto_latex": producto_latex,
            "detalle_latex": detalle_latex,
        }

    def _verificar_propiedad_transpuesta(self, matriz_a: Matriz, inversa: Matriz) -> dict:
        """Verifica la identidad (A^T)^-1 = (A^-1)^T mediante (A^-1)^T · A^T = I."""
        trans_a = self.resolutor_operaciones_matrices.transponer(matriz_a)
        trans_inv = self.resolutor_operaciones_matrices.transponer(inversa)
        dimension = matriz_a.filas
        resultado_multiplicacion = self.resolutor_operaciones_matrices.multiplicar(trans_inv, trans_a)
        producto = resultado_multiplicacion.get("matriz_resultado")
        identidad = _construir_identidad(dimension)
        es_exacto = producto.datos == identidad.datos if producto else False
        palabra_estado = "Coinciden" if es_exacto else "Difieren"
        producto_latex = matriz_a_latex(producto) if producto else ""
        detalle_latex = f"(A^{{-1}})^T \\cdot A^T = {producto_latex} \\quad (\\text{{{palabra_estado}}})"
        desc = "Verificación (Aᵀ)⁻¹ = (A⁻¹)ᵀ (PPT Inversa, pág. 11)."
        return {
            "propiedad": "(A^T)^{-1} = (A^{-1})^T",
            "descripcion": desc,
            "se_cumple": es_exacto,
            "coincide": es_exacto,
            "inversa_transpuesta_latex": matriz_a_latex(trans_inv),
            "detalle_latex": detalle_latex,
        }

    @staticmethod
    def _validar_cuadrada(matriz_a: Matriz) -> str | None:
        """Valida si el objeto es Matriz y si es cuadrada, devolviendo mensaje de error o None."""
        if not isinstance(matriz_a, Matriz):
            return "Se esperaba una instancia de Matriz."
        if matriz_a.filas != matriz_a.columnas:
            return f"La matriz debe ser cuadrada para tener inversa: recibido {matriz_a.filas}×{matriz_a.columnas}."
        return None

    def _construir_resultado_exito(
        self,
        matriz_a: Matriz,
        inversa: Matriz,
        meta: tuple[Fraction, str, list[dict]],
    ) -> dict:
        """Construye el diccionario de resultado exitoso con verificaciones."""
        determinante, aumentada_latex, pasos = meta
        dimension = matriz_a.filas
        v1 = self._verificar_producto(matriz_a, inversa, dimension, inverso=False)
        v2 = self._verificar_producto(matriz_a, inversa, dimension, inverso=True)
        v3 = self._verificar_propiedad_transpuesta(matriz_a, inversa)
        return {
            "estado": EXITO,
            "mensaje": f"Inversa calculada con éxito ({dimension}×{dimension}).",
            "determinante": determinante,
            "matriz_aumentada_inicial_latex": aumentada_latex,
            "inversa": inversa,
            "inversa_latex": matriz_a_latex(inversa),
            "pasos": pasos,
            "paso_verificacion": v1,
            "paso_verificacion_inverso": v2,
            "paso_propiedad_transpuesta": v3,
        }

    def resolver(
        self,
        matriz_a: Matriz,
        *,
        construir_detalle_latex: bool = True,
    ) -> dict:
        """Calcula A^-1 mediante Gauss-Jordan o reporta que la matriz es singular."""
        error = self._validar_cuadrada(matriz_a)
        if error:
            return _construir_respuesta_sin_inversa(ERROR, error)

        dimension = matriz_a.filas
        determinante = self.resolutor_operaciones_matrices.determinante(matriz_a)
        if determinante == 0:
            return _construir_respuesta_singular(
                determinante, "La matriz es singular (det = 0). No tiene inversa."
            )

        aumentada, aumentada_latex = self._construir_aumentada(matriz_a, dimension)
        reduccion = ResolutorGaussJordan(aumentada, numero_terminos_independientes=dimension).resolver_reduccion()

        if reduccion["rango"] < dimension:
            mensaje_resultado = f"La matriz es singular (rango {reduccion['rango']} < {dimension}). No tiene inversa."
            pasos_formateados = self._formatear_pasos(reduccion["pasos"], dimension, construir_detalle_latex)
            return _construir_respuesta_singular(determinante, mensaje_resultado, aumentada_latex, pasos_formateados)

        inversa = self._extraer_inversa(reduccion["matriz_reducida"], dimension)
        pasos = self._formatear_pasos(reduccion["pasos"], dimension, construir_detalle_latex)
        return self._construir_resultado_exito(matriz_a, inversa, (determinante, aumentada_latex, pasos))


def _construir_respuesta_singular(
    determinante: Fraction,
    mensaje: str,
    aumentada_latex: str | None = None,
    pasos: list[dict] | None = None,
) -> dict:
    """Construye el diccionario de salida cuando la matriz no es invertible."""
    resultado = _construir_respuesta_sin_inversa(SINGULAR, mensaje)
    resultado["determinante"] = determinante
    resultado["matriz_aumentada_inicial_latex"] = aumentada_latex
    resultado["pasos"] = pasos if pasos is not None else []
    return resultado


def _construir_respuesta_sin_inversa(estado: str, mensaje: str) -> dict:
    """Devuelve el contrato completo cuando no se puede calcular una inversa."""
    return {
        "estado": estado, "mensaje": mensaje,
        "determinante": None,
        "matriz_aumentada_inicial_latex": None,
        "inversa": None, "inversa_latex": None,
        "pasos": [], "paso_verificacion": None,
        "paso_verificacion_inverso": None,
        "paso_propiedad_transpuesta": None,
    }
