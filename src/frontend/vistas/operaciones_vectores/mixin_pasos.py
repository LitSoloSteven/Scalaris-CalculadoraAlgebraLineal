"""Adaptador entre los resultados de vectores y el reproductor interactivo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from nicegui import ui

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.cuerpos import render_latex
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

        accion_glosa = (
            self._crear_accion_glosa_vectores(pasos)
            if self.panel_ia
            else None
        )

        self.reproductor_pasos = ReproductorPasos(
            pasos,
            grupos,
            renderizar_cuerpo=self._renderizar_cuerpo_vectores,
            uid=opciones.identificador,
            titulo=opciones.titulo,
            lineas_ayuda=opciones.lineas_ayuda or _LINEAS_AYUDA_VECTORES,
            tipos_leyenda=opciones.tipos_leyenda,
            al_explicar=accion_glosa,
            esta_ocupado=lambda: bool(
                getattr(self.panel_ia, "_is_sending", False)
            ),
        )
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
                    render_latex(cuerpo)
            else:
                render_latex(str(cuerpo))

    def _crear_accion_glosa_vectores(self, pasos: Sequence[PasoReproductor]):
        """Crea el callback para explicar el paso actual con el panel de Glosa."""
        def explicar(paso: PasoReproductor) -> None:
            if not self.panel_ia:
                return
            meta = paso.meta_explicar or {}
            self.panel_ia.disparar_explicacion_paso({
                "index": paso.indice + 1,
                "total": len(pasos),
                **meta,
            })

        return explicar


_LINEAS_AYUDA_VECTORES = (
    "• Cada paso evalúa una componente o fase de la operación vectorial.",
    "• En combinación lineal se formula el sistema, se escalona [A | b] y se comprueba y = b.",
    "• Colores: fila resaltada = fila modificada · celda con borde = pivote.",
    "• Puedes usar los controles de navegación o reproducir automáticamente.",
)
