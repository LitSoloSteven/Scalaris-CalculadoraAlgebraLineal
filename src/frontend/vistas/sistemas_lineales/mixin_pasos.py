"""Presentacion del procedimiento de sistemas lineales."""

from __future__ import annotations

from nicegui import ui
from src.frontend.componentes.glosa_foco import crear_accion_explicacion

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.cuerpos import renderizar_latex
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor
from src.frontend.vistas.sistemas_lineales._pasos_reproductor import construir_pasos_reproductor


_TIPOS_LEYENDA_SISTEMAS = (
    "inicial",
    "intercambio",
    "pivote",
    "eliminacion",
    "normalizacion",
    "sustitucion",
    "verificacion",
)


class MixinPasosSistemasLineales:
    """Configura el reproductor compartido para los pasos de sistemas lineales."""

    def _obtener_metodo_activo(self) -> str | None:
        """Determina el método seleccionado en las pestañas."""
        if getattr(self, "pestanas_metodo", None):
            return getattr(self.pestanas_metodo, "value", "gauss")
        return None

    def _renderizar_seccion_pasos(self, resultado: dict) -> None:
        """Adapta los datos del controlador y construye el reproductor interactivo."""
        if getattr(self, "reproductor_pasos", None) is not None:
            self.reproductor_pasos.detener()

        pasos, grupos = construir_pasos_reproductor(
            resultado, metodo=self._obtener_metodo_activo()
        )
        if not pasos:
            return

        accion_glosa = crear_accion_explicacion(getattr(self, "panel_ia", None), pasos)

        self.reproductor_pasos = ReproductorPasos(pasos, grupos, renderizar_cuerpo=self._renderizar_cuerpo_sistema, identificador="sistemas", opciones={'titulo': "Procedimiento paso a paso", 'lineas_ayuda': _LINEAS_AYUDA_SISTEMAS, 'tipos_leyenda': _TIPOS_LEYENDA_SISTEMAS, 'al_explicar': accion_glosa, 'esta_ocupado': lambda: bool(
                getattr(getattr(self, "panel_ia", None), "_esta_enviando", False)
            )})
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_sistema(self, paso: PasoReproductor, contenedor) -> None:
        """Pinta la tabla aumentada o el bloque matemático según el tipo de paso."""
        with contenedor:
            if callable(paso.cuerpo):
                paso.cuerpo()
            elif paso.tipo in ("sustitucion", "verificacion"):
                renderizar_latex(str(paso.cuerpo))
            else:
                ui.html(str(paso.cuerpo))




_LINEAS_AYUDA_SISTEMAS = (
    "• La tabla es la matriz aumentada [A | b]: los coeficientes a la izquierda y el vector b a la derecha. La línea verde los separa.",
    "• Cada paso aplica una operación elemental de fila a la fila completa de [A | b].",
    "• Colores: fila resaltada = fila modificada · celda con borde = pivote · ámbar = filas intercambiadas.",
    "• Al finalizar la eliminación, se realizan la sustitución y la comprobación del sistema.",
)
