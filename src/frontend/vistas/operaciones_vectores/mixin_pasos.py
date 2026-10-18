"""Adaptador entre los resultados de vectores y el reproductor interactivo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from nicegui import ui
from src.frontend.componentes.glosa_foco import crear_accion_explicacion

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)


@dataclass(frozen=True)
class OpcionesReproductorVectores:
    """Agrupa identificación, ayuda y leyenda de un procedimiento vectorial."""

    identificador: str
    titulo: str = "Procedimiento paso a paso"
    lineas_ayuda: Sequence[str] = ()
    tipos_leyenda: Sequence[str] = ()


class MixinPasosVectores:
    """Configura el reproductor compartido para las operaciones vectoriales."""

    def _renderizar_reproductor(
        self,
        pasos: Sequence[PasoReproductor],
        grupos: Sequence[GrupoReproductor],
        opciones: OpcionesReproductorVectores,
    ) -> None:
        """Instancia y monta el reproductor interactivo de pasos."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()

        accion_glosa = crear_accion_explicacion(self.panel_ia, pasos)

        self.reproductor_pasos = ReproductorPasos(pasos, grupos, renderizar_cuerpo=self._renderizar_cuerpo_vectores, identificador=opciones.identificador, opciones={'titulo': opciones.titulo, 'lineas_ayuda': opciones.lineas_ayuda or _LINEAS_AYUDA_VECTORES, 'tipos_leyenda': opciones.tipos_leyenda, 'al_explicar': accion_glosa, 'esta_ocupado': lambda: bool(
                getattr(self.panel_ia, "_esta_enviando", False)
            )})
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_vectores(self, paso: PasoReproductor, contenedor: Any) -> None:
        """Pinta el cuerpo del paso (tabla aumentada HTML, bloque LaTeX o texto)."""
        with contenedor:
            cuerpo = paso.cuerpo
            if callable(cuerpo):
                cuerpo()
            elif isinstance(cuerpo, str):
                if cuerpo.strip().startswith("<"):
                    ui.html(cuerpo)
                else:
                    renderizar_latex(cuerpo)
            else:
                renderizar_latex(str(cuerpo))




_LINEAS_AYUDA_VECTORES = (
    "• Cada paso evalúa una componente o fase de la operación vectorial.",
    "• En combinación lineal se formula el sistema, se escalona [A | b] y se comprueba y = b.",
    "• Colores: fila resaltada = fila modificada · celda con borde = pivote.",
    "• Puedes usar los controles de navegación o reproducir automáticamente.",
)
