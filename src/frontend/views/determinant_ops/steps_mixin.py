"""Adaptador entre los resultados de determinantes y el reproductor compartido."""
from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

from nicegui import ui

from src.frontend.components.reproductor_pasos import ReproductorPasos, render_latex
from src.frontend.components.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.components.reproductor_pasos.modelo import PasoReproductor
from src.frontend.controllers.determinant_ops import DeterminantOpsController
from src.frontend.views.determinant_ops._adaptador_pasos import (
    CuerpoPasoDeterminante,
    adaptar_pasos_determinante,
    recortar_columnas,
    tipos_leyenda,
)
from src.frontend.views.determinant_ops._tabla_cofactor import html_tabla_cofactor

logger = logging.getLogger(__name__)

UID_REPRODUCTOR = "det"
TITULO_REPRODUCTOR = "Procedimiento paso a paso"
MENSAJE_ERROR_PASO = "No se pudo dibujar este paso. Avanza al siguiente o vuelve a calcular."

_LINEAS_AYUDA = (
    "• La tabla muestra la matriz tal como queda en cada paso. Usa los controles del reproductor para avanzar o retroceder.",
    "• Fila resaltada: la fila que cambia en ese paso. Celda con borde: el pivote o el coeficiente elegido. Ámbar: filas intercambiadas.",
    "• En cofactores, la fila y la columna tachadas se descartan y las celdas con fondo suave forman el menor que se calcula.",
    "• Sumar un múltiplo de una fila a otra no cambia el determinante. Cada intercambio de filas le cambia el signo.",
)


def _matriz_del_paso(paso: Mapping[str, Any], cuerpo: CuerpoPasoDeterminante) -> Any:
    """Devuelve la matriz propia del paso o, si no trae una, la matriz A original."""
    matriz = paso.get("matrix")
    return matriz if matriz is not None else cuerpo.matriz_a


def _latex_si_existe(texto: Any) -> None:
    """Pinta un bloque LaTeX solo cuando el paso trae contenido no vacío."""
    if isinstance(texto, str) and texto.strip():
        render_latex(texto)


def _pintar_tabla(matriz: Any, paso: Mapping[str, Any]) -> None:
    """Dibuja la matriz con las filas, el pivote y los intercambios del paso."""
    if matriz is None:
        return
    pivote = paso.get("pivot")
    ui.html(
        html_tabla_aumentada(
            matriz,
            matriz.cols,
            filas_cambiadas=paso.get("rows_changed") or (),
            # La tabla compara el pivote como tupla.
            pivote=tuple(pivote) if pivote else None,
            filas_intercambio=paso.get("swap_rows") or (),
        )
    )


def _cuerpo_tabla_eliminacion(paso: Mapping[str, Any], cuerpo: CuerpoPasoDeterminante) -> None:
    """Pinta la matriz triangularizada del paso de eliminación con pivoteo."""
    matriz = recortar_columnas(_matriz_del_paso(paso, cuerpo), cuerpo.dimension)
    _pintar_tabla(matriz, paso)


def _cuerpo_triangular(paso: Mapping[str, Any], cuerpo: CuerpoPasoDeterminante) -> None:
    """Pinta la matriz triangular final y el cálculo del producto de la diagonal."""
    _cuerpo_tabla_eliminacion(paso, cuerpo)
    _latex_si_existe(paso.get("detail_latex"))


def _cuerpo_planteamiento(paso: Mapping[str, Any], cuerpo: CuerpoPasoDeterminante) -> None:
    """Pinta A con la fila 1 resaltada y la fórmula de la expansión."""
    _pintar_tabla(_matriz_del_paso(paso, cuerpo), paso)
    _latex_si_existe(paso.get("detail_latex"))


def _cuerpo_menor(paso: Mapping[str, Any], cuerpo: CuerpoPasoDeterminante) -> None:
    """Pinta A con la fila 1 y la columna j tachadas, y el aporte del menor."""
    menor = paso.get("menor") or {}
    columna = int(menor.get("columna", 0))
    matriz = _matriz_del_paso(paso, cuerpo)
    if matriz is not None:
        ui.html(html_tabla_cofactor(matriz, 0, columna))
    ui.label(
        f"Tachamos la fila 1 y la columna {columna + 1}: "
        f"lo que queda es el menor M1{columna + 1}"
    ).classes("det-leyenda mb-2")
    _latex_si_existe(menor.get("termino_latex"))
    _latex_si_existe(paso.get("detail_latex"))
    _latex_si_existe(menor.get("expansion_latex"))


def _cuerpo_final(paso: Mapping[str, Any], cuerpo: CuerpoPasoDeterminante) -> None:
    """Pinta solo la fórmula del resultado, sin tabla."""
    _latex_si_existe(paso.get("detail_latex"))


_RENDERIZADORES: dict[str, Callable[[Mapping[str, Any], CuerpoPasoDeterminante], None]] = {
    "inicial": _cuerpo_tabla_eliminacion,
    "intercambio": _cuerpo_tabla_eliminacion,
    "pivote": _cuerpo_tabla_eliminacion,
    "eliminacion": _cuerpo_tabla_eliminacion,
    "producto": _cuerpo_triangular,
    "singular": _cuerpo_triangular,
    "planteamiento": _cuerpo_planteamiento,
    "menor": _cuerpo_menor,
    "final": _cuerpo_final,
}


def _asistente_ocupado(vista: Any) -> bool:
    """Indica si Glosa está respondiendo, para bloquear nuevas explicaciones."""
    panel = getattr(vista, "ai_panel", None)
    return bool(getattr(panel, "_is_sending", False))


class DeterminantOpsStepsMixin:
    """Configura el reproductor compartido para los pasos de determinantes."""

    def _render_steps_section(self, resultado: dict[str, Any]) -> None:
        """Adapta los pasos del controlador y monta el reproductor.

        Args:
            resultado: Diccionario devuelto por el controlador de determinantes.
        """
        if self.reproductor_pasos is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None
        pasos, grupos = adaptar_pasos_determinante(resultado)
        if not pasos:
            return
        con_glosa = getattr(self, "ai_panel", None) is not None
        self.reproductor_pasos = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_determinante,
            uid=UID_REPRODUCTOR,
            titulo=TITULO_REPRODUCTOR,
            lineas_ayuda=_LINEAS_AYUDA,
            tipos_leyenda=tipos_leyenda(str(resultado.get("metodo") or "")),
            al_explicar=self._crear_accion_glosa(resultado) if con_glosa else None,
            esta_ocupado=lambda: _asistente_ocupado(self),
        )
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_determinante(self, paso: PasoReproductor, contenedor: Any) -> None:
        """Pinta el cuerpo del paso según su tipo dentro del contenedor dado.

        Args:
            paso: Paso del reproductor con su CuerpoPasoDeterminante.
            contenedor: Elemento de NiceGUI que recibe el contenido.
        """
        cuerpo: CuerpoPasoDeterminante = paso.cuerpo
        renderizador = _RENDERIZADORES.get(paso.tipo, _cuerpo_final)
        with contenedor:
            try:
                renderizador(cuerpo.paso, cuerpo)
            except (ValueError, TypeError, KeyError):
                logger.error("No se pudo dibujar el paso %s", paso.indice, exc_info=True)
                ui.label(MENSAJE_ERROR_PASO).classes("badge-error")

    def _crear_accion_glosa(self, resultado: dict[str, Any]) -> Callable[[PasoReproductor], None]:
        """Crea el callback que pide a Glosa explicar el paso activo.

        Args:
            resultado: Diccionario del controlador, del que sale el foco exacto del paso.

        Returns:
            Función que recibe el paso y dispara la explicación.
        """
        total = len(resultado.get("steps") or [])

        def explicar(paso: PasoReproductor) -> None:
            foco = DeterminantOpsController.build_focus_for_step(resultado, paso.indice)
            self.ai_panel.trigger_explain_step({
                "index": paso.indice + 1,
                "total": total,
                **(paso.meta_explicar or {}),
                **foco,
            })

        return explicar
