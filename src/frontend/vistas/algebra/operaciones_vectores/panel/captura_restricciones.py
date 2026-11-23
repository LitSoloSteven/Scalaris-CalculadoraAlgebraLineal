"""Controles de captura en Matriz y Ecuaciones para el modo restricciones."""
from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS,
    DIMENSION_MINIMA,
    MAXIMO_CARACTERES_ECUACIONES,
)
from src.frontend.componentes.aplicacion.base.sonido import emitir_sonido
from src.frontend.componentes.captura.ecuaciones.cuadricula_ecuaciones import (
    CuadriculaEcuaciones,
    _aplicar_tamano,
)
from src.frontend.componentes.captura.nucleo.cuadricula_base import (
    actualizar_estados_botones_dimension,
)
from src.frontend.controladores.algebra.operaciones_vectores.captura_restricciones import (
    ErrorCapturaRestricciones,
    ayuda_variables_restricciones,
    ejemplo_restricciones,
    interpretar_ecuaciones_restricciones,
    redactar_ecuaciones_restricciones,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    EJEMPLO_RESTRICCIONES,
    ETIQUETA_EJEMPLO_RESTRICCIONES,
    MODO_RESTRICCIONES,
    superindice_dimension,
)


def _cargar_matriz_exacta(
    cuadricula: CuadriculaEcuaciones, matriz_a: list[list[str]], vector_b: list[str]
) -> None:
    cuadricula.cargar_datos(matriz_a, vector_b)
    for fila, valores in enumerate(matriz_a):
        for columna, valor in enumerate(valores):
            if str(valor).strip() == "0":
                cuadricula._cache_coeficientes[(fila, columna)] = "0"
                cuadricula.entradas_coeficientes[fila][columna].value = "0"
    for fila, valor in enumerate(vector_b):
        if str(valor).strip() == "0":
            cuadricula._cache_independientes[fila] = "0"
            cuadricula.entradas_independientes[fila].value = "0"


def _localizar_celda_restriccion(
    cuadricula: CuadriculaEcuaciones, diagnostico: dict
) -> ui.input | None:
    campo = diagnostico.get("campo")
    fila = diagnostico.get("fila")
    columna = diagnostico.get("columna")
    if type(fila) is not int or not (1 <= fila <= len(cuadricula.entradas_independientes)):
        return None
    if campo == "vector_b":
        return cuadricula.entradas_independientes[fila - 1]
    if campo == "matriz_a" and type(columna) is int and 1 <= columna <= cuadricula.columnas:
        return cuadricula.entradas_coeficientes[fila - 1][columna - 1]
    return None


def _actualizar_indicadores_dimension(captura: CapturaRestricciones) -> None:
    if captura.etiqueta_dimension is not None:
        captura.etiqueta_dimension.set_text(
            f"Dimensión ambiente: ℝ{superindice_dimension(captura.dimension_ambiente)}"
        )
    if captura.etiqueta_ayuda_variables is not None:
        captura.etiqueta_ayuda_variables.set_text(ayuda_variables_restricciones(captura.dimension_ambiente))
    actualizar_estados_botones_dimension(
        captura.boton_reducir_dimension, captura.boton_aumentar_dimension,
        captura.dimension_ambiente, DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS,
    )


def _construir_controles_dimension(captura: CapturaRestricciones) -> None:
    with ui.row().classes("subespacios-restricciones-dimension w-full items-center justify-between"):
        captura.etiqueta_dimension = ui.label().classes("font-semibold texto-principal")
        with ui.row().classes("items-center gap-2"):
            captura.boton_reducir_dimension = ui.button(
                icon="remove", on_click=lambda: captura.ajustar_dimension_ambiente(-1), color=None
            ).classes("boton-icono").props('ripple=false aria-label="Reducir dimensión ambiente"')
            captura.boton_aumentar_dimension = ui.button(
                icon="add", on_click=lambda: captura.ajustar_dimension_ambiente(1), color=None
            ).classes("boton-icono").props('ripple=false aria-label="Aumentar dimensión ambiente"')
    captura.etiqueta_ayuda_variables = ui.label().classes("text-xs texto-secundario")
    _actualizar_indicadores_dimension(captura)


def _sincronizar_formato_restricciones(captura: CapturaRestricciones, destino: str) -> None:
    if destino == "ecuaciones":
        if captura.cuadricula.esta_completamente_vacio():
            return
        matriz_a, vector_b = captura.cuadricula.obtener_datos_matriz()
        texto = redactar_ecuaciones_restricciones(matriz_a, vector_b)
        interpretar_ecuaciones_restricciones(texto, captura.dimension_ambiente)
        captura.ecuaciones.set_value(texto)
        return
    texto = (captura.ecuaciones.value or "").strip() if captura.ecuaciones is not None else ""
    if not texto:
        return
    capturada = interpretar_ecuaciones_restricciones(texto, captura.dimension_ambiente)
    _cargar_matriz_exacta(captura.cuadricula, capturada.matriz_a, capturada.vector_b)


def _marcar_diagnostico_panel(captura: CapturaRestricciones, diagnostico: dict | None) -> None:
    if captura._campo_marcado is not None and not captura._campo_marcado.is_deleted:
        captura._campo_marcado.props(remove="error aria-invalid")
    captura._campo_marcado = None
    if captura.aviso_diagnostico is not None:
        captura.aviso_diagnostico.set_text(str(diagnostico.get("mensaje") or "") if diagnostico else "")
    if not diagnostico:
        return
    campo = (
        captura.ecuaciones
        if captura.formato == "ecuaciones" or diagnostico.get("campo") == "ecuaciones"
        else _localizar_celda_restriccion(captura.cuadricula, diagnostico)
    )
    if campo is not None:
        campo.props("error aria-invalid=true")
        captura._campo_marcado = campo


class CapturaRestricciones:
    """Administra la dimensión ambiente, Matriz/Ecuaciones y diagnósticos de restricciones."""

    def __init__(self, al_editar: Callable[[], None]) -> None:
        self.al_editar = al_editar
        self.dimension_ambiente = 3
        self.formato = "matriz"
        self.cuadricula = CuadriculaEcuaciones(filas_iniciales=2, columnas_iniciales=3, cuadrada=False)
        self._sincronizando = False
        self._campo_marcado = None
        self.es_ejemplo = False
        self.selector = None
        self.panel_matriz = None
        self.ecuaciones = None
        self.etiqueta_dimension = None
        self.etiqueta_ayuda_variables = None
        self.boton_reducir_dimension = None
        self.boton_aumentar_dimension = None
        self.aviso_ejemplo = None
        self.aviso_diagnostico = None

    def inyectar_recursos_cliente(self) -> None:
        """Registra los adaptadores de cliente requeridos por la cuadrícula."""
        self.cuadricula.inyectar_recursos_cliente()

    def construir(self) -> None:
        """Monta dimensión ambiente, pestañas Matriz/Ecuaciones y avisos accesibles."""
        _construir_controles_dimension(self)
        with ui.tabs(value="matriz").classes("pestanas-controles sistemas-pestanas-modo").props(
            'dense no-caps aria-label="Formato de captura de restricciones"'
        ) as self.selector:
            ui.tab("matriz", label="Matriz", icon="grid_4x4")
            ui.tab("ecuaciones", label="Ecuaciones", icon="functions")
        with ui.column().classes("w-full min-w-0") as self.panel_matriz:
            self.cuadricula.construir_contenedor_cuadricula()
        self.ecuaciones = ui.textarea(
            "Ecuaciones lineales de restricción, una por línea", on_change=self._al_cambiar_panel
        ).classes("w-full min-w-0").props(f"outlined maxlength={MAXIMO_CARACTERES_ECUACIONES}")
        self.ecuaciones.set_visibility(False)
        self.aviso_ejemplo = ui.label(ETIQUETA_EJEMPLO_RESTRICCIONES).classes(
            "text-sm texto-secundario"
        ).props("role=status")
        self.aviso_ejemplo.set_visibility(False)
        self.aviso_diagnostico = ui.label().classes(
            "subespacios-numero text-sm texto-secundario"
        ).props("role=status aria-live=polite")
        self.cuadricula.al_cambiar_dimension = self._al_cambiar_cuadricula_dimension
        self.cuadricula.al_cambiar_datos = self._al_cambiar_panel
        self.selector.on_value_change(lambda evento: self.cambiar_formato(evento.value))

    async def ajustar_dimension_ambiente(self, delta: int) -> None:
        """Ajusta la dimensión ambiente conservando el borrador de texto o la cuadrícula."""
        self.establecer_dimension_ambiente(self.dimension_ambiente + delta)

    def establecer_dimension_ambiente(self, nueva_dimension: int) -> None:
        """Actualiza la dimensión ambiente dentro de los límites sin perder borradores."""
        if not (DIMENSION_MINIMA <= nueva_dimension <= DIMENSION_MAXIMA_SISTEMAS):
            return
        if nueva_dimension == self.dimension_ambiente:
            return
        self._sincronizando = True
        try:
            self.dimension_ambiente = nueva_dimension
            _aplicar_tamano(self.cuadricula, self.cuadricula.filas, nueva_dimension)
            _actualizar_indicadores_dimension(self)
        finally:
            self._sincronizando = False
        self._notificar_edicion(conservar_ejemplo=False)

    def cambiar_formato(self, destino: object) -> None:
        """Convierte Matriz y Ecuaciones solo si la fuente es válida; conserva el borrador si falla."""
        if self._sincronizando or destino == self.formato or destino not in ("matriz", "ecuaciones"):
            return
        self._sincronizando = True
        try:
            _sincronizar_formato_restricciones(self, destino)
        except (ErrorCapturaRestricciones, ValueError) as error:
            self.selector.set_value(self.formato)
            diagnostico = getattr(error, "diagnostico", None) or {"mensaje": str(error), "campo": self.formato}
            self.marcar_diagnostico(diagnostico)
            emitir_sonido("aviso")
            return
        finally:
            self._sincronizando = False
        self.formato = destino
        self.panel_matriz.set_visibility(destino == "matriz")
        self.ecuaciones.set_visibility(destino == "ecuaciones")
        self._notificar_edicion(conservar_ejemplo=True)

    def _al_cambiar_cuadricula_dimension(self, _filas: int, columnas: int) -> None:
        if self._sincronizando or columnas == self.dimension_ambiente:
            return
        self.dimension_ambiente = columnas
        _actualizar_indicadores_dimension(self)

    def _al_cambiar_panel(self) -> None:
        if not self._sincronizando:
            self._notificar_edicion(conservar_ejemplo=False)

    def _notificar_edicion(self, *, conservar_ejemplo: bool) -> None:
        if not conservar_ejemplo:
            self.es_ejemplo = False
            if self.aviso_ejemplo is not None:
                self.aviso_ejemplo.set_visibility(False)
        self.marcar_diagnostico(None)
        self.al_editar()

    def cargar_ejemplo(self) -> None:
        """Carga el ejemplo oficial en ℝ³ en Matriz y Ecuaciones."""
        ejemplo = ejemplo_restricciones()
        self._sincronizando = True
        try:
            self.dimension_ambiente = ejemplo.dimension_ambiente
            _cargar_matriz_exacta(self.cuadricula, ejemplo.matriz_a, ejemplo.vector_b)
            if self.ecuaciones is not None:
                self.ecuaciones.set_value(str(EJEMPLO_RESTRICCIONES["ecuaciones"]))
            _actualizar_indicadores_dimension(self)
        finally:
            self._sincronizando = False
        self.marcar_diagnostico(None)
        self.es_ejemplo = True
        if self.aviso_ejemplo is not None:
            self.aviso_ejemplo.set_visibility(True)
        self.al_editar()

    def limpiar(self) -> None:
        """Vacía celdas y ecuaciones conservando dimensión ambiente y formato activo."""
        self._sincronizando = True
        try:
            if self.cuadricula.columnas != self.dimension_ambiente:
                _aplicar_tamano(self.cuadricula, self.cuadricula.filas, self.dimension_ambiente)
            self.cuadricula.limpiar()
            if self.ecuaciones is not None:
                self.ecuaciones.set_value("")
        finally:
            self._sincronizando = False
        self._notificar_edicion(conservar_ejemplo=False)

    def obtener(self) -> dict:
        """Devuelve la instantánea serializable actual para el controlador."""
        matriz_a, vector_b = self.cuadricula.obtener_datos_matriz()
        return {
            "modo": MODO_RESTRICCIONES,
            "formato": self.formato,
            "dimension_ambiente": self.dimension_ambiente,
            "matriz_a": matriz_a,
            "vector_b": vector_b,
            "matriz_vacia": self.cuadricula.esta_completamente_vacio(),
            "ecuaciones": (self.ecuaciones.value or "") if self.ecuaciones is not None else "",
        }

    def esta_vacia(self) -> bool:
        """Indica si el formato activo carece de contenido capturado."""
        if self.formato == "ecuaciones":
            return not bool((self.ecuaciones.value or "").strip() if self.ecuaciones is not None else "")
        return self.cuadricula.esta_completamente_vacio()

    def campos_entrada(self) -> list[ui.input]:
        """Devuelve las celdas activas de la cuadrícula de restricciones."""
        return [celda for fila in self.cuadricula.entradas_coeficientes for celda in fila] + list(
            self.cuadricula.entradas_independientes
        )

    def marcar_diagnostico(self, diagnostico: dict | None) -> None:
        """Señala la celda o el campo de ecuaciones afectado sin perder la captura."""
        _marcar_diagnostico_panel(self, diagnostico)
