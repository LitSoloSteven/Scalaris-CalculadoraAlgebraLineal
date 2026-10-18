"""Resolutor de transformaciones lineales T: R^n -> R^m con nucleo, imagen y rango."""

from fractions import Fraction

from src.backend.constantes import CERO_EPSILON, ERROR, EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex
from src.backend.resolutores.sistemas_lineales.gauss_jordan import (
    ResolutorGaussJordan,
)
from src.backend.utilidades.formateadores import formatear_fraccion_texto


class ResolutorTransformacionesLineales:
    """Analiza T(x) = Ax: calcula nucleo, imagen, nulidad, inyectividad y sobreyectividad."""

    def __init__(self, eps: float = CERO_EPSILON) -> None:
        """Inicializa el resolutor con la tolerancia de cero epsilon."""
        self.eps = eps

    def _base_nucleo(
        self,
        m_red: Matriz,
        columnas_pivote: list[int],
        columnas_libres: list[int],
        numero_variables: int,
        nombres: list[str],
    ) -> list[dict]:
        """Calcula la base del espacio nulo ker(T) despejando variables desde la RREF."""
        if not columnas_libres:
            return []
        m_filas = m_red.filas if m_red else 0
        base = []
        for k, libre_columna in enumerate(columnas_libres):
            vector = [Fraction(0)] * numero_variables
            vector[libre_columna] = Fraction(1)
            for r, pivote_columna in enumerate(columnas_pivote):
                if r >= m_filas:
                    break
                valor = Fraction(0)
                for columna_libre in columnas_libres:
                    valor -= Fraction(m_red.obtener(r, columna_libre)) * vector[columna_libre]
                vector[pivote_columna] = valor

            componentes = [formatear_fraccion_texto(componente) for componente in vector]
            param_etiqueta = f"t_{k+1}" if len(columnas_libres) > 1 else "t"
            variable_nombre = nombres[libre_columna] if libre_columna < len(nombres) else f"x_{libre_columna+1}"
            base.append({
                "parametro": param_etiqueta,
                "variable_libre": variable_nombre,
                "vector": componentes,
            })
        return base

    def _base_imagen(self, matriz_a: Matriz, columnas_pivote: list[int]) -> list[dict]:
        """Calcula la base del espacio columna Im(T) a partir de las columnas pivote originales."""
        base = []
        for columna in columnas_pivote:
            componentes = [
                formatear_fraccion_texto(Fraction(matriz_a.obtener(r, columna)))
                for r in range(matriz_a.filas)
            ]
            base.append({
                "indice_columna": columna + 1,
                "vector": componentes,
            })
        return base

    def _construir_conclusiones(
        self,
        es_inyectiva: bool,
        es_sobreyectiva: bool,
        nulidad: int,
        rango: int,
        numero_ecuaciones: int,
    ) -> dict[str, str | None]:
        """Genera el texto de conclusiones sobre inyectividad, sobreyectividad y biyectividad."""
        inyectiva_texto = (
            "T es INYECTIVA: ker(T) = {0} (nulidad = 0)."
            if es_inyectiva else f"T NO es inyectiva: ker(T) tiene dimensión {nulidad} > 0."
        )
        sobreyectiva_texto = (
            f"T es SOBREYECTIVA: Im(T) = R^{numero_ecuaciones} (rango = {rango} = m)."
            if es_sobreyectiva else f"T NO es sobreyectiva: Im(T) ⊊ R^{numero_ecuaciones} (rango = {rango} < {numero_ecuaciones})."
        )
        if es_inyectiva and es_sobreyectiva:
            biyectiva_texto = "T es BIYECTIVA (isomorfismo)."
        elif not es_inyectiva and not es_sobreyectiva:
            biyectiva_texto = "T no es inyectiva ni sobreyectiva."
        else:
            biyectiva_texto = None

        return {
            "inyectividad": inyectiva_texto,
            "sobreyectividad": sobreyectiva_texto,
            "biyectividad": biyectiva_texto,
        }

    def _reducir_sistema_homogeneo(self, matriz_a: Matriz, nombres: list[str]) -> dict:
        """Crea la matriz aumentada con ceros y ejecuta la reducción Gauss-Jordan."""
        numero_ecuaciones, numero_variables = matriz_a.filas, matriz_a.columnas
        datos_aumentada = [
            [matriz_a.obtener(i, j) for j in range(numero_variables)] + [Fraction(0)]
            for i in range(numero_ecuaciones)
        ]
        matriz_aumentada = Matriz(numero_ecuaciones, numero_variables + 1, datos_aumentada)
        resolutor_gj = ResolutorGaussJordan(matriz_aumentada, nombres_variables=nombres)
        return resolutor_gj.resolver_reduccion()

    def _empaquetar_resultado(
        self,
        matriz_a: Matriz,
        dimensiones: tuple[int, int, int, int],
        columnas: tuple[list[int], list[int]],
        bases: tuple[list[dict], list[dict], list[dict]],
    ) -> dict:
        """Empaqueta el diccionario completo con propiedades y conclusiones del análisis."""
        numero_ecuaciones, numero_variables, rango, nulidad = dimensiones
        columnas_pivote, columnas_libres = columnas
        base_nucleo, base_imagen, pasos_reduccion = bases
        es_inyectiva = (nulidad == 0)
        es_sobreyectiva = (rango == numero_ecuaciones)
        mensaje_resultado = f"Análisis de transformación lineal T: R^{numero_variables} → R^{numero_ecuaciones} completado."
        return {
            "estado": EXITO,
            "mensaje": mensaje_resultado,
            "dimension_codominio": numero_ecuaciones,
            "dimension_dominio": numero_variables,
            "rango": rango,
            "nulidad": nulidad,
            "columnas_pivote": columnas_pivote,
            "columnas_libres": columnas_libres,
            "es_inyectiva": es_inyectiva,
            "es_sobreyectiva": es_sobreyectiva,
            "base_nucleo": base_nucleo,
            "base_imagen": base_imagen,
            "teorema_dimension": f"rango(T) + nulidad(T) = n  →  {rango} + {nulidad} = {numero_variables}  ✓",
            "conclusiones": self._construir_conclusiones(es_inyectiva, es_sobreyectiva, nulidad, rango, numero_ecuaciones),
            "aviso_convencion": (
                "CONVENCIÓN ADOPTADA (columna estándar): la base de Im(T) está "
                "formada por las columnas pivote de A. Algunos textos usan la "
                "convención fila (vectores transpuestos); en ese caso la base "
                "visual difiere pero el espacio generado es el mismo."
            ),
            "pasos_reduccion": pasos_reduccion,
        }

    def resolver(
        self,
        matriz_a: Matriz,
        nombres_variables: list[str] | None = None,
    ) -> dict:
        """Analiza integralmente la transformacion T(x) = Ax."""
        if not isinstance(matriz_a, Matriz):
            error = "Se esperaba una instancia de Matriz."
            return {"estado": ERROR, "mensaje": error}

        numero_ecuaciones, numero_variables = matriz_a.filas, matriz_a.columnas
        nombres = (
            nombres_variables
            if (nombres_variables and len(nombres_variables) == numero_variables)
            else [f"x_{{{i+1}}}" for i in range(numero_variables)]
        )
        reduccion = self._reducir_sistema_homogeneo(matriz_a, nombres)

        columnas_pivote = reduccion["columnas_pivote"]
        rango = len(columnas_pivote)
        nulidad = numero_variables - rango
        columnas_libres = [c for c in range(numero_variables) if c not in columnas_pivote]
        m_red = reduccion["matriz_reducida"]

        base_nucleo = self._base_nucleo(m_red, columnas_pivote, columnas_libres, numero_variables, nombres)
        base_imagen = self._base_imagen(matriz_a, columnas_pivote)
        pasos_reduccion = _formatear_pasos_reduccion(reduccion["pasos"])

        return self._empaquetar_resultado(
            matriz_a,
            (numero_ecuaciones, numero_variables, rango, nulidad),
            (columnas_pivote, columnas_libres),
            (base_nucleo, base_imagen, pasos_reduccion),
        )


def _formatear_pasos_reduccion(pasos: list[dict]) -> list[dict]:
    """Formatea los pasos de reducción Gauss-Jordan con LaTeX y claves canónicas."""
    return [
        {
            "descripcion": paso.get("descripcion", ""),
            "matriz": matriz_a_latex(paso.get("matriz")),
        }
        for paso in pasos
    ]
