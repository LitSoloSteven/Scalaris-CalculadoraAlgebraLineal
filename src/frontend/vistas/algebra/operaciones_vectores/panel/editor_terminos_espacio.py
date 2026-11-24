"""Editor de coordenadas polinómicas con borradores por dimensión."""
from collections.abc import Callable
from copy import deepcopy
from functools import partial

from nicegui import ui

from src.backend.constantes import LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.resolutores.operaciones_vectores.espacios_vectoriales.limites_espacio_vectorial import (
    MAXIMO_GRADO_ENTRADA, MAXIMO_TERMINOS_ENTRADA,
)
from src.frontend.controladores.algebra.operaciones_vectores.ejemplos_espacio_vectorial import TerminosCaptura
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_espacio_vectorial import variables_operacion
from src.frontend.nucleo.textos.textos_espacio_vectorial import NOMBRES_OPERACIONES


class EditorTerminosEspacio:
    """Monta una operación y conserva sus borradores al cambiar la dimensión ambiente."""

    def __init__(self, campo: str, al_editar: Callable[[], None]) -> None:
        self.campo = campo
        self._al_editar = al_editar
        self._dimension = 0
        self._borradores: dict[int, TerminosCaptura] = {}
        self._contenedores: list[ui.column] = []
        self._campos: dict[int, list[tuple[ui.input, ui.input]]] = {}
        self._marcados: tuple[ui.input, ...] = ()
        self._contenedor = ui.column().classes("w-full min-w-0")

    @property
    def _terminos(self) -> TerminosCaptura:
        return self._borradores[self._dimension]

    def ajustar_dimension(self, dimension: int) -> None:
        """Muestra el borrador asociado a la dimensión de los vectores."""
        if dimension == self._dimension:
            return
        self._dimension = dimension
        self._borradores.setdefault(dimension, [[] for _ in range(dimension)])
        self._renderizar()

    def reemplazar(self, terminos: TerminosCaptura) -> None:
        """Reemplaza el borrador activo con coordenadas independientes."""
        self._borradores[self._dimension] = deepcopy(terminos)
        self._renderizar()

    def obtener(self) -> TerminosCaptura:
        """Devuelve una copia de las coordenadas para análisis en segundo plano."""
        return deepcopy(self._terminos)

    def campos_entrada(self) -> list[ui.input]:
        """Devuelve los campos montados del editor."""
        return [campo for filas in self._campos.values() for fila in filas for campo in fila]

    def marcar_diagnostico(self, diagnostico: dict | None) -> None:
        """Marca los campos de la ubicación indicada por el dominio."""
        for campo in self._marcados:
            if not campo.is_deleted:
                campo.props(remove="error aria-invalid")
        self._marcados = ()
        if not diagnostico or diagnostico.get("campo") != self.campo:
            return
        coordenada = diagnostico.get("coordenada")
        termino = diagnostico.get("termino")
        filas = self._campos.get(coordenada, [])
        if termino is not None and 1 <= termino <= len(filas):
            self._marcados = filas[termino - 1]
        for campo in self._marcados:
            campo.props("error aria-invalid=true")

    def _renderizar(self) -> None:
        self._contenedor.clear()
        self._contenedores.clear()
        self._campos.clear()
        with self._contenedor:
            ui.label(NOMBRES_OPERACIONES[self.campo]).classes("font-semibold texto-principal")
            variables = ", ".join(variables_operacion(self.campo, self._dimension))
            ui.label(f"Orden de los exponentes · {variables}").classes("subespacios-numero texto-secundario text-sm")
            for indice in range(self._dimension):
                self._contenedores.append(ui.column().classes("w-full min-w-0 gap-2"))
                self._renderizar_coordenada(indice)

    def _renderizar_coordenada(self, indice: int) -> ui.button:
        contenedor = self._contenedores[indice]
        contenedor.clear()
        filas = self._campos[indice + 1] = []
        terminos = self._terminos[indice]
        with contenedor:
            ui.label(f"Coordenada {indice + 1}").classes("font-medium texto-principal")
            if not terminos:
                ui.label("Polinomio cero (sin términos)").classes("text-sm texto-secundario")
            for posicion, termino in enumerate(terminos):
                filas.append(self._renderizar_termino(indice, posicion, termino))
            boton = ui.button("Añadir término", on_click=partial(self._agregar, indice), color=None)
            nombre = f"Añadir término en {NOMBRES_OPERACIONES[self.campo].lower()}, coordenada {indice + 1}"
            boton.classes("boton-discreto").props(f'ripple=false aria-label="{nombre}"')
            boton.set_enabled(len(terminos) < MAXIMO_TERMINOS_ENTRADA)
        return boton

    def _renderizar_termino(self, indice: int, posicion: int, termino: dict) -> tuple[ui.input, ui.input]:
        contexto = f"{NOMBRES_OPERACIONES[self.campo]}, coordenada {indice + 1}, término {posicion + 1}"
        cantidad = len(variables_operacion(self.campo, self._dimension))
        longitud = (len(str(MAXIMO_GRADO_ENTRADA)) + 1) * cantidad
        with ui.row().classes("w-full min-w-0 items-center flex-wrap gap-2"):
            coeficiente = self._entrada("Coeficiente", termino, "coeficiente", LONGITUD_MAXIMA_CADENA_NUMERO)
            exponentes = self._entrada("Exponentes", termino, "exponentes", longitud)
            coeficiente.props(f'aria-label="Coeficiente · {contexto}"')
            exponentes.props(f'aria-label="Exponentes · {contexto}"')
            ui.button(icon="close", on_click=partial(self._quitar, indice, posicion), color=None).classes(
                "boton-discreto shrink-0"
            ).props(f'ripple=false aria-label="Quitar término · {contexto}"')
        return coeficiente, exponentes

    def _entrada(self, etiqueta: str, termino: dict, clave: str, longitud: int) -> ui.input:
        campo = ui.input(etiqueta, value=termino[clave], on_change=partial(self._editar, termino, clave))
        return campo.classes("min-w-0 basis-32 grow").props(f"outlined dense maxlength={longitud}")

    def _editar(self, termino: dict, clave: str, evento) -> None:
        termino[clave] = evento.value or ""
        self._al_editar()

    def _agregar(self, indice: int) -> None:
        terminos = self._terminos[indice]
        if len(terminos) >= MAXIMO_TERMINOS_ENTRADA:
            return
        cantidad = len(variables_operacion(self.campo, self._dimension))
        terminos.append({"coeficiente": "1", "exponentes": " ".join(["0"] * cantidad)})
        self._renderizar_coordenada(indice)
        self._campos[indice + 1][-1][0].run_method("focus")
        self._al_editar()

    def _quitar(self, indice: int, posicion: int) -> None:
        self._terminos[indice].pop(posicion)
        boton = self._renderizar_coordenada(indice)
        boton.client.run_javascript(f"document.getElementById('{boton.html_id}')?.focus()")
        self._al_editar()
