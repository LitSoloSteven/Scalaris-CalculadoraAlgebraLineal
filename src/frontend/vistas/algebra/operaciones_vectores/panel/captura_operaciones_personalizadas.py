"""Captura conjunta de la definición del conjunto y sus dos operaciones."""
from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from src.frontend.controladores.algebra.operaciones_vectores.ejemplos_espacio_vectorial import (
    EJEMPLOS_OPERACIONES, terminos_ejemplo,
)
from src.frontend.nucleo.textos.textos_espacio_vectorial import MODO_PERSONALIZADO, NOMBRES_OPERACIONES
from src.frontend.nucleo.textos.textos_espacios_subespacios import MODO_GENERADORES, MODO_RESTRICCIONES, NOMBRES_MODOS
from .captura_generadores import CapturaGeneradores
from .captura_restricciones import CapturaRestricciones
from .editor_terminos_espacio import EditorTerminosEspacio


class CapturaOperacionesPersonalizadas:
    """Reutiliza generadores y restricciones con un borrador propio para cada conjunto."""

    def __init__(self, al_editar: Callable[[], None]) -> None:
        self._al_editar = al_editar
        self._modo_conjunto = MODO_GENERADORES
        self._sincronizando = False
        self._selectores_conjunto: dict[str, ui.column] = {}
        self._conjuntos = {
            MODO_GENERADORES: CapturaGeneradores(self._editar, "espacio_vectorial_generadores"),
            MODO_RESTRICCIONES: CapturaRestricciones(self._editar),
        }
        self._operaciones: dict[str, EditorTerminosEspacio] = {}
        self._selector_conjunto = None
        self._selector_ejemplo = None
        self._aviso = None

    @property
    def conjunto(self) -> CapturaGeneradores | CapturaRestricciones:
        """Devuelve la captura activa de la definición del conjunto."""
        return self._conjuntos[self._modo_conjunto]

    def construir(self) -> None:
        """Monta la definición, el selector de ejemplos y los editores de términos."""
        self._selector_conjunto = ui.select(
            {modo: NOMBRES_MODOS[modo] for modo in self._conjuntos},
            label="Definición del conjunto", value=self._modo_conjunto,
            on_change=lambda evento: self._cambiar_conjunto(evento.value),
        ).classes("w-full min-w-0").props("outlined dense")
        for modo, conjunto in self._conjuntos.items():
            with ui.column().classes("w-full min-w-0") as self._selectores_conjunto[modo]:
                conjunto.construir()
        self._actualizar_conjuntos()
        ejemplos = list(EJEMPLOS_OPERACIONES)
        self._selector_ejemplo = ui.select(
            ejemplos, label="Ejemplo de operaciones", value=ejemplos[0],
        ).classes("w-full min-w-0").props("outlined dense")
        ui.label(
            "Escribe coeficientes racionales y un exponente entero no negativo por variable, separados por espacios."
        ).classes("texto-secundario text-sm")
        self._operaciones = {
            campo: EditorTerminosEspacio(campo, self._editar) for campo in NOMBRES_OPERACIONES
        }
        self._ajustar_operaciones()
        self._aviso = ui.label().classes("texto-secundario subespacios-numero").props("role=status aria-live=polite")

    def obtener(self) -> dict:
        """Devuelve una instantánea del conjunto activo y las dos operaciones."""
        return {
            "modo": MODO_PERSONALIZADO, "conjunto": self.conjunto.obtener(),
            **{campo: editor.obtener() for campo, editor in self._operaciones.items()},
        }

    def campos_entrada(self) -> list:
        """Devuelve las entradas montadas del conjunto y los términos activos."""
        campos = self.conjunto.campos_entrada()
        for editor in self._operaciones.values():
            campos.extend(editor.campos_entrada())
        return campos

    def marcar_diagnostico(self, diagnostico: dict | None) -> None:
        """Anuncia el diagnóstico y resalta su ubicación si señala un término o una celda."""
        es_del_conjunto = diagnostico and diagnostico.get("origen") == "conjunto"
        self.conjunto.marcar_diagnostico(diagnostico if es_del_conjunto else None)
        for editor in self._operaciones.values():
            editor.marcar_diagnostico(diagnostico)
        if self._aviso is not None:
            self._aviso.set_text(_mensaje_localizado(diagnostico))

    def cargar_ejemplo(self) -> None:
        """Carga en el editor el ejercicio seleccionado y conserva su carácter editable."""
        ejemplo = EJEMPLOS_OPERACIONES[self._selector_ejemplo.value]
        self._sincronizando = True
        try:
            if ejemplo.ecuaciones:
                self._cargar_ecuaciones_ejemplo(ejemplo.dimension, ejemplo.ecuaciones)
            else:
                self._cambiar_conjunto(MODO_GENERADORES)
                self._conjuntos[MODO_GENERADORES].cargar_generadores({"v1": ["1"]})
            self._ajustar_operaciones()
            for campo, editor in self._operaciones.items():
                editor.reemplazar(terminos_ejemplo(ejemplo, campo))
        finally:
            self._sincronizando = False
        self._editar()

    def limpiar(self) -> None:
        """Limpia el conjunto activo y deja las coordenadas sin términos."""
        self._sincronizando = True
        try:
            self.conjunto.limpiar()
            for editor in self._operaciones.values():
                editor.reemplazar([[] for _ in editor.obtener()])
        finally:
            self._sincronizando = False
        self._editar()

    def _cargar_ecuaciones_ejemplo(self, dimension: int, ecuaciones: str) -> None:
        self._cambiar_conjunto(MODO_RESTRICCIONES)
        conjunto = self._conjuntos[MODO_RESTRICCIONES]
        conjunto.limpiar()
        conjunto.establecer_dimension_ambiente(dimension)
        conjunto.cambiar_formato("ecuaciones")
        conjunto.selector.set_value("ecuaciones")
        conjunto.ecuaciones.set_value(ecuaciones)

    def _cambiar_conjunto(self, modo: object) -> None:
        if modo not in self._conjuntos or modo == self._modo_conjunto:
            return
        self._modo_conjunto = modo
        self._selector_conjunto.set_value(modo)
        self._actualizar_conjuntos()
        self._editar()

    def _actualizar_conjuntos(self) -> None:
        for modo, contenedor in self._selectores_conjunto.items():
            contenedor.set_visibility(modo == self._modo_conjunto)

    def _ajustar_operaciones(self) -> None:
        dimension = self.conjunto.obtener()["dimension_ambiente"]
        for editor in self._operaciones.values():
            editor.ajustar_dimension(dimension)

    def _editar(self) -> None:
        if self._sincronizando:
            return
        self._ajustar_operaciones()
        self.marcar_diagnostico(None)
        self._al_editar()


def _mensaje_localizado(diagnostico: dict | None) -> str:
    if not diagnostico or diagnostico.get("origen") == "conjunto":
        return ""
    coordenada = diagnostico.get("coordenada")
    termino = diagnostico.get("termino")
    partes = [NOMBRES_OPERACIONES.get(diagnostico["campo"], "")]
    if coordenada is not None:
        partes.append(f"coordenada {coordenada}")
    if termino is not None:
        partes.append(f"término {termino}")
    return " · ".join(parte for parte in (*partes, diagnostico["mensaje"]) if parte)
