"""Controles de captura para familias de generadores en Espacios y subespacios."""
from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_VECTORES, DIMENSION_MINIMA
from src.frontend.componentes.captura.nucleo.cuadricula_base import (
    actualizar_estados_botones_dimension,
)
from src.frontend.componentes.captura.vectores.captura_vectores import (
    PanelCapturaVectores,
    _clave_orden_vector,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    ETIQUETA_EJEMPLO,
    MODO_GENERADORES,
)
from src.frontend.controladores.algebra.operaciones_vectores.controlador_subespacios import (
    ejemplo_generadores,
)


class CapturaGeneradores:
    """Administra vectores columna de generadores, ejemplo, limpieza y diagnósticos."""

    def __init__(self, al_editar: Callable[[], None]) -> None:
        self.al_editar = al_editar
        self.panel = PanelCapturaVectores(
            "subespacios_generadores",
            opciones={
                "minimo_vectores": DIMENSION_MINIMA,
                "maximo_vectores": DIMENSION_MAXIMA_VECTORES,
                "permitir_orientacion": False,
                "orientacion_inicial": "columna",
            },
        )
        self._sincronizando = False
        self._campo_marcado = None
        self.es_ejemplo = False
        self.aviso_ejemplo = None
        self.aviso_diagnostico = None
        self.contenedor_panel = None

    def inyectar_recursos_cliente(self) -> None:
        """Registra los adaptadores de cliente requeridos por el panel vectorial."""
        self.panel.inyectar_recursos_cliente()

    def construir(self) -> None:
        """Monta el panel de generadores y los avisos accesibles de ejemplo y error."""
        self.contenedor_panel = ui.column().classes("w-full min-w-0")
        self.panel.construir(self.contenedor_panel)
        self.panel.al_cambiar_datos = self._al_cambiar_panel
        self.aviso_ejemplo = ui.label(ETIQUETA_EJEMPLO).classes(
            "text-sm texto-secundario"
        ).props("role=status")
        self.aviso_ejemplo.set_visibility(False)
        self.aviso_diagnostico = ui.label().classes(
            "subespacios-numero text-sm texto-secundario"
        ).props("role=status aria-live=polite")

    def cargar_ejemplo(self) -> None:
        """Carga los tres generadores del ejemplo oficial y marca su procedencia."""
        self.cargar_generadores(ejemplo_generadores(), marcar_ejemplo=True)

    def cargar_generadores(
        self, datos_vectores: dict[str, list[str]], *, marcar_ejemplo: bool = False
    ) -> None:
        """Reemplaza la captura conservando ceros explícitos y etiquetas exactas."""
        if not datos_vectores:
            return
        self._sincronizando = True
        try:
            primer_vector = next(iter(datos_vectores.values()))
            self.panel.vectores.clear()
            self.panel.dimension = len(primer_vector)
            for etiqueta, valores in datos_vectores.items():
                self.panel.vectores[etiqueta] = _nuevo_vector_columna(valores)
            if self.panel.etiqueta_dimension is not None:
                self.panel.etiqueta_dimension.set_text(str(self.panel.dimension))
            self.panel.renderizar_todos_vectores()
            actualizar_estados_botones_dimension(
                self.panel.boton_reducir_dimension,
                self.panel.boton_aumentar_dimension,
                self.panel.dimension,
                DIMENSION_MINIMA,
                DIMENSION_MAXIMA_VECTORES,
            )
        finally:
            self._sincronizando = False
        self._finalizar_cambio_programatico(marcar_ejemplo)

    def limpiar(self) -> None:
        """Vacía las componentes conservando dimensión ambiente y etiquetas activas."""
        self._sincronizando = True
        try:
            for vector in self.panel.vectores.values():
                vector["celdas"].clear()
            self.panel.renderizar_todos_vectores()
        finally:
            self._sincronizando = False
        self._finalizar_cambio_programatico(False)

    def _finalizar_cambio_programatico(self, marcar_ejemplo: bool) -> None:
        self.marcar_diagnostico(None)
        self.es_ejemplo = marcar_ejemplo
        if self.aviso_ejemplo is not None:
            self.aviso_ejemplo.set_visibility(marcar_ejemplo)
        self.al_editar()

    def _al_cambiar_panel(self) -> None:
        if self._sincronizando:
            return
        self.es_ejemplo = False
        if self.aviso_ejemplo is not None:
            self.aviso_ejemplo.set_visibility(False)
        self.marcar_diagnostico(None)
        self.al_editar()

    def obtener(self) -> dict:
        """Devuelve la instantánea serializable actual en el orden visible de vectores."""
        claves = sorted(self.panel.vectores.keys(), key=_clave_orden_vector)
        return {
            "modo": MODO_GENERADORES,
            "dimension_ambiente": self.panel.dimension,
            "vectores": {
                etiqueta: {
                    "orientacion": "columna",
                    "datos": [
                        self.panel.vectores[etiqueta]["celdas"].get(indice, "")
                        for indice in range(self.panel.dimension)
                    ],
                }
                for etiqueta in claves
            },
        }

    def campos_entrada(self) -> list[ui.input]:
        """Devuelve las entradas de componente actualmente montadas."""
        campos: list[ui.input] = []
        for vector in self.panel.vectores.values():
            contenedor = vector.get("contenedor")
            if contenedor is not None:
                campos.extend(
                    elemento for elemento in contenedor.descendants() if isinstance(elemento, ui.input)
                )
        return campos

    def marcar_diagnostico(self, diagnostico: dict | None) -> None:
        """Resalta la componente afectada cuando existe coordenada y preserva la captura."""
        if self._campo_marcado is not None and not self._campo_marcado.is_deleted:
            self._campo_marcado.props(remove="error aria-invalid")
        self._campo_marcado = None
        if self.aviso_diagnostico is not None:
            self.aviso_diagnostico.set_text(
                str(diagnostico.get("mensaje") or "") if diagnostico else ""
            )
        if not diagnostico:
            return
        campo = _localizar_componente(
            self.panel.vectores, diagnostico.get("etiqueta"), diagnostico.get("componente")
        )
        if campo is not None:
            campo.props("error aria-invalid=true")
            self._campo_marcado = campo


def _nuevo_vector_columna(valores: list[str]) -> dict:
    celdas = {indice: str(valor).strip() for indice, valor in enumerate(valores)}
    return {
        "orientacion": "columna",
        "celdas": celdas,
        "contenedor": None,
        "etiqueta_dimension": None,
        "boton_orientacion": None,
    }


def _localizar_componente(
    vectores: dict[str, dict], etiqueta: object, componente: object
) -> ui.input | None:
    if not isinstance(etiqueta, str) or type(componente) is not int:
        return None
    vector = vectores.get(etiqueta)
    contenedor = vector.get("contenedor") if vector else None
    if contenedor is None:
        return None
    campos = [elemento for elemento in contenedor.descendants() if isinstance(elemento, ui.input)]
    return campos[componente] if 0 <= componente < len(campos) else None
