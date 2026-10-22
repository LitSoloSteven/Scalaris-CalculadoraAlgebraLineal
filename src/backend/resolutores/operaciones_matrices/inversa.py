"""Orquestacion de inversion y presentacion de sus comprobaciones."""
from src.backend.constantes import ERROR, SINGULAR
from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import identidad
from .comprobacion_productos import comprobar_producto, desarrollar_producto
from src.backend.resolutores.operaciones_matrices.calculo_inversa import calcular_inversa
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_particionada_a_latex
from src.backend.resolutores.operaciones_matrices.operaciones import ResolutorOperacionesMatrices
from src.backend.resolutores.operaciones_matrices.presentacion_inversa import (
    formatear_pasos_inversa, presentar_inversa, presentar_producto_inversa, presentar_propiedad_transpuesta,
)
from src.backend.resolutores.sistemas_lineales.pasos_reduccion import RegistroPasosSistema
from .pasos_determinante import RegistroPasosDeterminante
from .formateadores import matriz_a_latex
from .comprobacion_productos import crear_paso_analisis


class ResolutorInversa:
    """Valida la matriz, delega el calculo exacto y entrega pasos y comprobaciones."""

    def __init__(self) -> None:
        """Inicializa el servicio de operaciones utilizado por las comprobaciones."""
        self.resolutor_operaciones_matrices = ResolutorOperacionesMatrices()

    def _verificar_producto(self, matriz_a: Matriz, inversa: Matriz, dimension: int, inverso: bool) -> dict:
        izquierda = inversa if inverso else matriz_a
        derecha = matriz_a if inverso else inversa
        producto = self.resolutor_operaciones_matrices.multiplicar(izquierda, derecha).get("matriz_resultado")
        comprobacion = desarrollar_producto(izquierda, derecha, producto, identidad(dimension), "A^{-1}A=I" if inverso else "AA^{-1}=I")
        resultado = presentar_producto_inversa(comprobacion["producto"], dimension, inverso)
        resultado["traza"] = comprobacion["traza"]
        return resultado

    def _verificar_propiedad_transpuesta(self, matriz_a: Matriz, inversa: Matriz) -> dict:
        transpuesta_original = self.resolutor_operaciones_matrices.transponer(matriz_a)
        transpuesta_inversa = self.resolutor_operaciones_matrices.transponer(inversa)
        comprobacion = comprobar_producto(transpuesta_inversa, transpuesta_original, identidad(matriz_a.filas), "(A^{-1})^TA^T=I")
        resultado = presentar_propiedad_transpuesta(comprobacion["producto"], transpuesta_inversa)
        resultado["traza"] = comprobacion["traza"]
        conclusion = ("Como el producto es la identidad, (A^-1)^T es la inversa de A^T por unicidad. "
                      if comprobacion["coincide"] else "El producto difiere de la identidad; no se certifica la candidata. ")
        resultado["traza"][-1]["explicacion"] += (
            " " + conclusion + "Se ha comprobado por multiplicacion; no se ha invertido A^T con otro algoritmo.")
        return resultado

    @staticmethod
    def _validar_cuadrada(matriz: Matriz) -> str | None:
        if not isinstance(matriz, Matriz):
            return "Se esperaba una instancia de Matriz."
        if matriz.filas != matriz.columnas:
            return f"La matriz debe ser cuadrada para tener inversa: recibido {matriz.filas}×{matriz.columnas}."
        return None

    def resolver(self, matriz_a: Matriz, *, construir_detalle_latex: bool = True) -> dict:
        """Devuelve inversa y comprobaciones de matriz_a o error; controla solo el LaTeX de los pasos."""
        error = self._validar_cuadrada(matriz_a)
        if error:
            return _respuesta_sin_inversa(ERROR, error)
        dimension = matriz_a.filas
        registro = RegistroPasosSistema(True)
        registro_determinante = RegistroPasosDeterminante("primero")
        calculo = calcular_inversa(matriz_a, registro.registrar, registro_determinante.registrar)
        determinante, inversa = calculo["determinante"], calculo["inversa"]
        if calculo["aumentada"] is None:
            return _presentar_singularidad(calculo, registro_determinante)
        aumentada_latex = matriz_particionada_a_latex(calculo["aumentada"], dimension)
        pasos = formatear_pasos_inversa(registro.pasos, dimension, construir_detalle_latex)
        if inversa is None:
            return _respuesta_singular(determinante, f"La matriz es singular (rango {calculo['rango']} < {dimension}). No tiene inversa.", aumentada_latex, pasos)
        comprobaciones = (self._verificar_producto(matriz_a, inversa, dimension, False),
                         self._verificar_producto(matriz_a, inversa, dimension, True),
                         self._verificar_propiedad_transpuesta(matriz_a, inversa))
        return presentar_inversa(inversa, (determinante, aumentada_latex, pasos), comprobaciones)


def _respuesta_singular(determinante, mensaje: str, aumentada: str | None = None, pasos: list | None = None) -> dict:
    resultado = _respuesta_sin_inversa(SINGULAR, mensaje)
    resultado.update(determinante=determinante, matriz_aumentada_inicial_latex=aumentada, pasos=pasos if pasos is not None else [])
    return resultado


def _respuesta_sin_inversa(estado: str, mensaje: str) -> dict:
    return {"estado": estado, "mensaje": mensaje, "determinante": None,
            "matriz_aumentada_inicial_latex": None, "inversa": None, "inversa_latex": None,
            "pasos": [], "paso_verificacion": None, "paso_verificacion_inverso": None,
            "paso_propiedad_transpuesta": None}


def _presentar_singularidad(calculo: dict, registro: RegistroPasosDeterminante) -> dict:
    resultado = _respuesta_singular(calculo["determinante"], "La matriz es singular (det = 0). No tiene inversa.")
    triangular = registro.traza[-1]["matriz"]
    intercambios = sum(paso["tipo"] == "intercambio" for paso in registro.traza)
    registro.cerrar({"matriz_reducida": triangular, "intercambios": intercambios}, calculo["determinante"])
    traza = []
    for paso in registro.traza:
        detalle = paso.get("detalle_latex", "")
        if not detalle and triangular.filas <= DIMENSION_MAXIMA_LATEX_INVERSA:
            detalle = matriz_a_latex(paso["matriz"])
        analisis = crear_paso_analisis(paso["descripcion"], detalle, paso["explicacion"], "verificacion")
        if triangular.filas > DIMENSION_MAXIMA_LATEX_INVERSA:
            analisis.update(matriz=paso["matriz"], operacion=paso.get("operacion", {}))
        traza.append(analisis)
    traza[-1]["explicacion"] += " Por det(A)=0, A no tiene inversa. Este es el calculo previo a la inversion, no un segundo metodo."
    resultado["traza_determinante"] = traza
    return resultado
