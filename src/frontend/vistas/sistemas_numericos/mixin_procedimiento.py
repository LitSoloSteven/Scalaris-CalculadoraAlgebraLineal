"""Mixin para visualización interactiva del procedimiento de conversión de bases."""

from __future__ import annotations


from nicegui import ui
from ._cuerpo_numerico import renderizar_cuerpo_numerico
from src.frontend.componentes.glosa_foco import crear_accion_explicacion

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from ._pasos_bases import construir_pasos_bases


class MixinProcedimientoSistemasNumericos:
    """Gestiona la renderización del procedimiento matemático mediante ReproductorPasos."""

    def _mostrar_procedimiento(self) -> None:
        """Pinta el procedimiento paso a paso de la conversión activa."""
        if not hasattr(self, "resultados_completos") or "pasos" not in self.resultados_completos:
            ui.notify("Realiza una conversión válida primero", type="warning")
            return

        if getattr(self, "reproductor", None) is not None:
            self.reproductor.detener()

        self.contenedor_pasos.clear()
        self.contenedor_pasos.classes(remove="hidden")

        with self.contenedor_pasos:
            ui.label("Procedimiento Matemático").classes("text-2xl font-bold texto-principal mt-4")

            pasos_crudos = self.resultados_completos.get("pasos", [])
            if not pasos_crudos:
                ui.label("El número ya se encuentra en el sistema destino seleccionado.").classes(
                    "texto-secundario italic text-sm mb-2"
                )
                return

            self._montar_reproductor_bases(pasos_crudos)

    def _montar_reproductor_bases(self, pasos_crudos: list[dict]) -> None:
        """Construye y monta la instancia de ReproductorPasos para las conversiones calculadas."""
        pasos, grupos = construir_pasos_bases(pasos_crudos)
        if not pasos:
            return

        accion_glosa = crear_accion_explicacion(getattr(self, "panel_ia", None), pasos)

        self.reproductor = ReproductorPasos(pasos, grupos, renderizar_cuerpo=renderizar_cuerpo_numerico, identificador="bases", opciones={'titulo': "Procedimiento de conversión", 'lineas_ayuda': _LINEAS_AYUDA_BASES, 'tipos_leyenda': ("expansion", "division", "resultado", "lectura"), 'al_explicar': accion_glosa, 'esta_ocupado': lambda: bool(
                getattr(getattr(self, "panel_ia", None), "_esta_enviando", False)
            )})
        self.reproductor.construir()


_LINEAS_AYUDA_BASES = (
    "• Expansión posicional: cada dígito se multiplica por la base elevada a su posición.",
    "• Divisiones sucesivas: se divide el número repetidamente entre la base de destino.",
    "• Lectura: los residuos se leen en orden inverso (de abajo hacia arriba) para formar el resultado.",
    "• Puedes navegar paso a paso o utilizar la reproducción automática.",
)
