"""Operaciones algebraicas vectoriales con trazabilidad paso a paso."""

from typing import Any

from src.backend.constantes import ERROR, EXITO
from src.backend.excepciones import ErrorVectorInvalido
from src.backend.modelos.matriz import Matriz, Numerico
from src.backend.resolutores.operaciones_vectores.base import (
    _BaseResolutorVectores,
)
from src.backend.resolutores.operaciones_vectores.formateadores import (
    formatear_vector_latex,
    vector_a_latex,
)
from src.backend.utilidades.formateadores import (
    formatear_fraccion_texto,
    numero_a_latex,
)
from src.backend.utilidades.validadores import ValidadorMatriz


def _formatear_latex_binario(
    resultado: Matriz,
    v1: Matriz,
    v2: Matriz,
    nombres_simbolo: tuple[str, str, str],
) -> tuple[str, str]:
    """Genera el formateo LaTeX del resultado vectorial y de la ecuación final."""
    nombre1, nombre2, latex_simbolo = nombres_simbolo
    resultado_latex = vector_a_latex(resultado)
    v1_latex = vector_a_latex(v1)
    v2_latex = vector_a_latex(v2)
    v1_nombre = formatear_vector_latex(nombre1)
    v2_nombre = formatear_vector_latex(nombre2)
    vector_final_latex = (
        rf"\mathbf{{w}} = {v1_nombre} {latex_simbolo} {v2_nombre} = {v1_latex} {latex_simbolo} {v2_latex} = {resultado_latex}"
    )
    return resultado_latex, vector_final_latex


def _formatear_latex_escalar(
    resultado: Matriz,
    vector: Matriz,
    escalar_info: tuple[Numerico, str, str, str],
) -> tuple[str, str]:
    """Genera el formateo LaTeX para el resultado de multiplicación escalar."""
    k_frac, k_latex, nombre, nombre_resultado = escalar_info
    resultado_latex = vector_a_latex(resultado)
    v_latex = vector_a_latex(vector)
    v_nombre = formatear_vector_latex(nombre)
    resultado_nombre = formatear_vector_latex(nombre_resultado)
    denominador = getattr(k_frac, "denominator", 1)
    k_paren = rf"\left({k_latex}\right)" if denominador != 1 else f"({k_latex})"
    valores = vector.datos if vector.columnas == 1 else [vector.datos[0]]
    productos = [f"({k_latex}) \\cdot ({numero_a_latex(valor)})" for fila in valores for valor in fila]
    separador = r" \\ " if vector.columnas == 1 else r" & "
    producto_latex = r"\begin{bmatrix} " + separador.join(productos) + r" \end{bmatrix}"
    vector_final_latex = rf"{resultado_nombre} = {k_latex} \cdot {v_nombre} = {k_paren} {v_latex} = {producto_latex} = {resultado_latex}"
    return resultado_latex, vector_final_latex


def _empaquetar_error_vector(mensaje: str) -> dict:
    """Construye la respuesta de error para operaciones vectoriales."""
    return {
        "estado": ERROR,
        "mensaje": mensaje,
        "matriz_resultado": None,
        "pasos": [],
        "detalles_latex": [],
    }


def _empaquetar_exito_vector(
    mensaje: str,
    informacion_resultado: tuple[Matriz, str, str],
    pasos: list[dict],
    detalles_latex: list[str],
) -> dict:
    """Construye la respuesta de éxito para operaciones vectoriales."""
    resultado, resultado_latex, vector_final_latex = informacion_resultado
    return {
        "estado": EXITO,
        "mensaje": mensaje,
        "matriz_resultado": resultado,
        "matriz_resultado_latex": resultado_latex,
        "vector_resultado_latex": vector_final_latex,
        "pasos": pasos,
        "detalles_latex": detalles_latex,
    }


class ResolutorOperacionesVectores(_BaseResolutorVectores):
    """Ejecuta suma, resta y multiplicación escalar con vectores de R^n."""

    def _calcular_celda_binaria(
        self,
        v1: Matriz,
        v2: Matriz,
        resultado: Matriz,
        posicion_operacion: tuple[int, str, str],
    ) -> str:
        """Calcula el valor de la componente y registra el paso en el trazador."""
        i, operacion_simbolo, latex_simbolo = posicion_operacion
        valor_izquierdo = v1.obtener(i, 0) if self.es_vector_columna(v1) else v1.obtener(0, i)
        valor_derecho = v2.obtener(i, 0) if self.es_vector_columna(v2) else v2.obtener(0, i)
        valor_resultado = valor_izquierdo + valor_derecho if operacion_simbolo == "+" else valor_izquierdo - valor_derecho

        if self.es_vector_columna(resultado):
            resultado.establecer(i, 0, valor_resultado)
        else:
            resultado.establecer(0, i, valor_resultado)

        a_latex = numero_a_latex(valor_izquierdo)
        b_latex = numero_a_latex(valor_derecho)
        c_latex = numero_a_latex(valor_resultado)
        detalle_latex = f"w_{{{i + 1}}} = ({a_latex}) {latex_simbolo} ({b_latex}) = {c_latex}"
        self._registrar_paso(
            f"Componente {i + 1}: {formatear_fraccion_texto(valor_izquierdo)} {operacion_simbolo} "
            f"{formatear_fraccion_texto(valor_derecho)} = {formatear_fraccion_texto(valor_resultado)}",
            matriz_actual=resultado,
            detalle_latex=detalle_latex,
        )
        return detalle_latex

    def _operacion_binaria(
        self,
        v1: Matriz,
        v2: Matriz,
        configuracion: tuple[str, str, bool, str, str, str],
    ) -> dict:
        """Implementación compartida de suma y resta vectorial."""
        nombre1, nombre2, estricto, operacion_simbolo, operacion_palabra, latex_simbolo = configuracion
        self.pasos = []
        try:
            self.validar_vector(v1, nombre1)
            self.validar_vector(v2, nombre2)
            v1, v2, mensaje_ajuste = self.armonizar_dimensiones(v1, v2, nombre1, nombre2, estricto)
        except ErrorVectorInvalido as error:
            return _empaquetar_error_vector(str(error))

        dim = self.dimension_vector(v1)
        resultado = Matriz(v1.filas, v1.columnas)
        self._registrar_paso(f"Iniciando {operacion_palabra} de vectores (dim {dim})")
        if mensaje_ajuste:
            self._registrar_paso(mensaje_ajuste)

        detalles_latex = [
            self._calcular_celda_binaria(v1, v2, resultado, (i, operacion_simbolo, latex_simbolo))
            for i in range(dim)
        ]
        resultado_latex, vector_final_latex = _formatear_latex_binario(
            resultado, v1, v2, (nombre1, nombre2, latex_simbolo)
        )
        detalles_latex.append(vector_final_latex)
        mensaje = f"{operacion_palabra.capitalize()} de vectores completada (dim {dim})."
        return _empaquetar_exito_vector(
            mensaje, (resultado, resultado_latex, vector_final_latex), self.pasos, detalles_latex
        )

    def sumar(
        self,
        v1: Matriz,
        v2: Matriz,
        *,
        nombre1: str = "v_1",
        nombre2: str = "v_2",
        estricto: bool = False,
    ) -> dict:
        """Suma vectorial componente a componente."""
        return self._operacion_binaria(
            v1, v2, (nombre1, nombre2, estricto, "+", "suma", "+")
        )

    def restar(
        self,
        v1: Matriz,
        v2: Matriz,
        *,
        nombre1: str = "v_1",
        nombre2: str = "v_2",
        estricto: bool = False,
    ) -> dict:
        """Resta vectorial componente a componente."""
        return self._operacion_binaria(
            v1, v2, (nombre1, nombre2, estricto, "-", "resta", "-")
        )

    def _calcular_celda_escalar(
        self,
        vector: Matriz,
        resultado: Matriz,
        posicion_k: tuple[int, Any, str, str],
    ) -> str:
        """Calcula el producto de una componente por el escalar y registra el paso."""
        i, k_frac, k_latex, nombre_resultado = posicion_k
        valor = vector.obtener(i, 0) if self.es_vector_columna(vector) else vector.obtener(0, i)
        producto = k_frac * valor
        if self.es_vector_columna(resultado):
            resultado.establecer(i, 0, producto)
        else:
            resultado.establecer(0, i, producto)

        valor_latex = numero_a_latex(valor)
        producto_latex = numero_a_latex(producto)
        detalle_latex = f"{nombre_resultado}_{{{i + 1}}} = ({k_latex}) \\cdot ({valor_latex}) = {producto_latex}"
        self._registrar_paso(
            f"Componente {i + 1}: {formatear_fraccion_texto(k_frac)} · {formatear_fraccion_texto(valor)} = {formatear_fraccion_texto(producto)}",
            matriz_actual=resultado,
            detalle_latex=detalle_latex,
        )
        return detalle_latex

    def _validar_y_parsear_escalar(
        self, vector: Matriz, nombre: str, escalar: Numerico
    ) -> tuple[Any, str | None]:
        """Valida el vector y convierte el escalar a Fraction exacta."""
        try:
            self.validar_vector(vector, nombre)
        except ErrorVectorInvalido as error_vector:
            return None, str(error_vector)
        correcto, k_frac, error = ValidadorMatriz.parsear_numero_exacto(escalar)
        if not correcto:
            return None, f"Escalar inválido: {error}"
        return k_frac, None

    def multiplicar_escalar(
        self,
        escalar: Numerico,
        vector: Matriz,
        *,
        nombre: str = "v",
        nombre_resultado: str = "w",
    ) -> dict:
        """Multiplicación de un escalar por un vector en R^n."""
        self.pasos = []
        k_frac, error = self._validar_y_parsear_escalar(vector, nombre, escalar)
        if error:
            return _empaquetar_error_vector(error)

        dim = self.dimension_vector(vector)
        resultado = Matriz(vector.filas, vector.columnas)
        k_latex = numero_a_latex(k_frac)
        self._registrar_paso(
            f"Iniciando multiplicación escalar: {formatear_fraccion_texto(k_frac)} · {nombre} (dim {dim})"
        )

        detalles_latex = [
            self._calcular_celda_escalar(vector, resultado, (i, k_frac, k_latex, nombre_resultado))
            for i in range(dim)
        ]
        resultado_latex, vector_final_latex = _formatear_latex_escalar(
            resultado, vector, (k_frac, k_latex, nombre, nombre_resultado)
        )
        detalles_latex.append(vector_final_latex)
        mensaje = f"Multiplicación escalar completada (dim {dim})."
        return _empaquetar_exito_vector(
            mensaje, (resultado, resultado_latex, vector_final_latex), self.pasos, detalles_latex
        )
