"""Resolutor de eliminacion gaussiana con aritmetica exacta de fracciones."""

from fractions import Fraction

from src.backend.constantes import (
    CERO_EPSILON,
    SIN_SOLUCION,
    SOLUCION_UNICA,
    SOLUCIONES_INFINITAS,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.analisis_rouche import (
    analizar_sistema_rouche,
)
from src.backend.resolutores.sistemas_lineales.sustitucion import (
    ejecutar_sustitucion_hacia_atras,
)
from src.backend.utilidades.formateadores import formatear_fraccion_texto


def verificar_estado_sistema(
    matriz: Matriz, numero_variables: int, rango: int, eps: float
) -> tuple[str, str]:
    """Evalua si el sistema es inconsistente, indeterminado o determinado."""
    numero_filas = matriz.filas
    for r in range(numero_filas):
        todos_ceros = all(abs(matriz.obtener(r, c)) < eps for c in range(numero_variables))
        termino_no_nulo = abs(matriz.obtener(r, numero_variables)) >= eps
        if todos_ceros and termino_no_nulo:
            return SIN_SOLUCION, "Sistema Inconsistente: Sin Solución."

    if rango < numero_variables:
        return SOLUCIONES_INFINITAS, "Sistema Consistente Indeterminado: Presenta Infinitas Soluciones"
    return SOLUCION_UNICA, "Sistema Consistente Determinado: Presenta Solución Única."


def eliminar_fila_exacta(
    fila_pivote: list,
    fila_destino: list,
    columna_indice: int,
    indice_destino: int,
    indice_pivote: int,
) -> tuple[list, str]:
    """Aplica la operacion elemental exacta F_dest = F_dest - c * F_piv."""
    pivote_valor = Fraction(fila_pivote[columna_indice])
    destino_valor = Fraction(fila_destino[columna_indice])
    if destino_valor == 0:
        return fila_destino, ""

    factor = destino_valor / pivote_valor
    nueva_fila = [Fraction(tv) - factor * Fraction(pv) for tv, pv in zip(fila_destino, fila_pivote)]
    desc = (
        f"Fila {indice_destino + 1} = Fila {indice_destino + 1} − "
        f"({formatear_fraccion_texto(factor)}) · Fila {indice_pivote + 1}"
    )
    return nueva_fila, desc


class ResolutorGauss:
    """Implementa el metodo de eliminacion de Gauss y analisis completo del sistema."""

    REDUCCION_COMPLETA: bool = False

    def __init__(
        self,
        matriz_aumentada: Matriz,
        eps: float = CERO_EPSILON,
        nombres_variables: list[str] | None = None,
        numero_terminos_independientes: int = 1,
    ) -> None:
        """Inicializa el resolutor con la matriz aumentada y parametros de control."""
        if type(numero_terminos_independientes) is not int or numero_terminos_independientes < 1:
            raise ValueError("numero_terminos_independientes debe ser un entero >= 1.")
        if numero_terminos_independientes >= matriz_aumentada.columnas:
            raise ValueError(
                "numero_terminos_independientes debe ser menor que las columnas de la matriz."
            )
        self.matriz_inicial = matriz_aumentada.clonar()
        self.matriz = matriz_aumentada.clonar()
        self.eps = eps
        self.nombres_variables = nombres_variables
        self.numero_terminos_independientes = numero_terminos_independientes
        self.pasos: list[dict] = []

    def _numero_variables(self) -> int:
        """Cantidad de columnas tratadas como variables del sistema."""
        return self.matriz.columnas - self.numero_terminos_independientes

    def _registrar_paso(self, descripcion: str) -> None:
        """Registra un paso intermedio con la copia de la matriz actual."""
        copia = self.matriz.clonar()
        self.pasos.append({
            "descripcion": descripcion,
            "matriz": copia,
        })

    def _seleccionar_pivote(self, columna: int, fila_pivote: int) -> int | None:
        """Busca la fila con el maximo valor absoluto en la columna indicada."""
        max_fila = fila_pivote
        max_valor = abs(self.matriz.obtener(fila_pivote, columna))
        for r in range(fila_pivote + 1, self.matriz.filas):
            valor = abs(self.matriz.obtener(r, columna))
            if valor > max_valor:
                max_valor = valor
                max_fila = r
        if max_valor < self.eps:
            return None
        return max_fila

    def _normalizar_pivotes(self, columnas_pivote: list[int], reduccion_completa: bool) -> None:
        """Escala cada fila pivote para que su coeficiente principal sea 1."""
        prefijo = "Normalizar pivote a 1" if reduccion_completa else "Normalizar pivote"
        for r, c in enumerate(columnas_pivote):
            valor = self.matriz.obtener(r, c)
            if abs(valor) >= self.eps and abs(valor - 1) > self.eps:
                escala = Fraction(1) / Fraction(valor)
                nueva_fila = [self.matriz.obtener(r, columna) * escala for columna in range(self.matriz.columnas)]
                for columna_indice, elem in enumerate(nueva_fila):
                    self.matriz.establecer(r, columna_indice, elem)
                self._registrar_paso(
                    f"{prefijo}: Fila {r + 1} = Fila {r + 1} / {formatear_fraccion_texto(valor)}"
                )

    def _registrar_seleccion_pivote(
        self, columna: int, fila_pivote: int, reduccion_completa: bool
    ) -> list[int]:
        """Registra el pivote seleccionado y devuelve las filas objetivo a eliminar."""
        numero_filas = self.matriz.filas
        if reduccion_completa:
            self._registrar_paso(f"Pivote seleccionado en Fila {fila_pivote + 1}, Columna {columna + 1}")
            return [r for r in range(numero_filas) if r != fila_pivote]
        valor_texto = formatear_fraccion_texto(self.matriz.obtener(fila_pivote, columna))
        self._registrar_paso(
            f"Pivote seleccionado en Fila {fila_pivote + 1}, Columna {columna + 1} (valor = {valor_texto})"
        )
        return list(range(fila_pivote + 1, numero_filas))

    def _eliminar_filas_objetivo(
        self, fila_pivote: int, columna: int, filas_objetivo: list[int]
    ) -> None:
        """Aplica la operacion de eliminacion exacta sobre cada fila objetivo."""
        fila_pivote_datos = [self.matriz.obtener(fila_pivote, c) for c in range(self.matriz.columnas)]
        for r in filas_objetivo:
            if abs(self.matriz.obtener(r, columna)) > self.eps:
                fila_destino_datos = [self.matriz.obtener(r, c) for c in range(self.matriz.columnas)]
                nueva_f, desc = eliminar_fila_exacta(
                    fila_pivote_datos, fila_destino_datos, columna, r, fila_pivote
                )
                for c_indice, elem in enumerate(nueva_f):
                    self.matriz.establecer(r, c_indice, elem)
                self._registrar_paso(desc)

    def _eliminar(self, reduccion_completa: bool) -> tuple[int, list[int]]:
        """Ejecuta la eliminacion progresiva con aritmetica exacta de fracciones."""
        numero_filas = self.matriz.filas
        fila_pivote = 0
        columnas_pivote: list[int] = []
        self._registrar_paso("Matriz inicial aumentada [A|b]:")

        for columna in range(self._numero_variables()):
            if fila_pivote >= numero_filas:
                break
            max_fila = self._seleccionar_pivote(columna, fila_pivote)
            if max_fila is None:
                continue

            if max_fila != fila_pivote:
                self.matriz.intercambiar_filas(fila_pivote, max_fila)
                self._registrar_paso(f"Intercambio: Fila {fila_pivote + 1} ↔ Fila {max_fila + 1}")

            filas_objetivo = self._registrar_seleccion_pivote(columna, fila_pivote, reduccion_completa)
            self._eliminar_filas_objetivo(fila_pivote, columna, filas_objetivo)
            columnas_pivote.append(columna)
            fila_pivote += 1

        self._normalizar_pivotes(columnas_pivote, reduccion_completa)
        return fila_pivote, columnas_pivote

    def resolver_reduccion(self) -> dict:
        """Ejecuta eliminacion sin sustitucion para inversion o sistemas multiples."""
        rango, columnas_pivote = self._eliminar(reduccion_completa=self.REDUCCION_COMPLETA)
        return {
            "matriz_reducida": self.matriz,
            "rango": rango,
            "columnas_pivote": columnas_pivote,
            "pasos": self.pasos,
        }

    def resolver(self) -> dict:
        """Resuelve el sistema Ax = b completo reportando clasificacion y pasos."""
        if self.numero_terminos_independientes != 1:
            raise ValueError(
                f"resolver() requiere numero_terminos_independientes=1 (recibido {self.numero_terminos_independientes}). "
                "Usa resolver_reduccion() para multiples terminos independientes."
            )

        rango, columnas_pivote = self._eliminar(reduccion_completa=self.REDUCCION_COMPLETA)
        numero_variables = self._numero_variables()
        estado, mensaje = verificar_estado_sistema(self.matriz, numero_variables, rango, self.eps)
        es_homogeneo = all(
            abs(self.matriz_inicial.obtener(r, numero_variables)) < self.eps
            for r in range(self.matriz_inicial.filas)
        )
        analisis = analizar_sistema_rouche(estado, rango, numero_variables, es_homogeneo, columnas_pivote)

        if estado == SIN_SOLUCION:
            return _empaquetar_respuesta_sin_solucion(self.matriz, estado, mensaje, analisis, self.pasos)

        sol_datos = ejecutar_sustitucion_hacia_atras(
            self.matriz, columnas_pivote, numero_variables, self.nombres_variables
        )
        return _empaquetar_respuesta_con_solucion(
            (self.matriz, estado, mensaje), analisis, self.pasos, sol_datos
        )


def _empaquetar_respuesta_sin_solucion(
    matriz: Matriz, estado: str, mensaje: str, analisis: dict, pasos: list[dict]
) -> dict:
    """Construye el diccionario de salida cuando el sistema es inconsistente."""
    return {
        "estado": SIN_SOLUCION,
        "mensaje": mensaje,
        "clasificacion": mensaje,
        "matriz_escalonada": matriz,
        "solucion": None,
        "solucion_exacta": None,
        "columnas_libres": [],
        "parametros_solucion": None,
        "analisis_sistema": analisis,
        "pasos": pasos,
        "pasos_sustitucion_regresiva": [],
    }


def _empaquetar_respuesta_con_solucion(
    info_sistema: tuple[Matriz, str, str],
    analisis: dict,
    pasos: list[dict],
    sol_datos: tuple[list[str], list[Fraction], list[str], list[int], dict | None],
) -> dict:
    """Construye el diccionario de salida para soluciones únicas o infinitas."""
    matriz, estado, mensaje = info_sistema
    sol, sol_exacta, pasos_sust, libres, parametros_solucion = sol_datos
    estado_calculo = SOLUCION_UNICA if estado == SOLUCION_UNICA else SOLUCIONES_INFINITAS
    return {
        "estado": estado_calculo,
        "mensaje": mensaje,
        "clasificacion": mensaje,
        "matriz_escalonada": matriz,
        "solucion": sol,
        "solucion_exacta": sol_exacta,
        "columnas_libres": libres,
        "parametros_solucion": parametros_solucion,
        "analisis_sistema": analisis,
        "pasos": pasos,
        "pasos_sustitucion_regresiva": pasos_sust,
    }
