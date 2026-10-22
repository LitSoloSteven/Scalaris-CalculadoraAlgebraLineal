"""Presentacion del procedimiento de inversion."""

from nicegui import ui

from src.frontend.componentes.reproductor_pasos import ReproductorPasos
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_aumentada
from src.frontend.vistas.operaciones_inversas._adaptador_pasos import _CuerpoPasoInversa, adaptar_pasos_inversa


class MixinPasosOperacionesInversas:
    """Configura el reproductor compartido para los pasos de inversión."""

    def _renderizar_seccion_pasos(self, resultado: dict) -> None:
        """Adapta los datos del controlador y construye el reproductor de inversa."""
        if self.reproductor_pasos is not None:
            self.reproductor_pasos.detener()
        pasos, grupos = adaptar_pasos_inversa(resultado)
        if not pasos:
            return
        accion_glosa = (
            self._crear_accion_glosa(resultado["pasos"], len(pasos))
            if getattr(self, "panel_ia", None)
            else None
        )
        self.reproductor_pasos = ReproductorPasos(pasos, grupos, renderizar_cuerpo=self._renderizar_cuerpo_inversa, identificador="inv", opciones={'titulo': "Procedimiento paso a paso", 'lineas_ayuda': _LINEAS_AYUDA, 'tipos_leyenda': ("inicial", "intercambio", "pivote", "eliminacion", "normalizacion"), 'al_explicar': accion_glosa, 'esta_ocupado': lambda: bool(
                getattr(getattr(self, "panel_ia", None), "_esta_enviando", False)
            )})
        self.reproductor_pasos.construir()

    def _renderizar_cuerpo_inversa(self, paso, contenedor) -> None:
        """Pinta la tabla aumentada correspondiente al paso seleccionado."""
        datos: _CuerpoPasoInversa = paso.cuerpo
        paso_fuente = datos.paso
        tabla = html_tabla_aumentada(paso_fuente["matriz"], datos.dimension, opciones={'filas_cambiadas': paso_fuente.get("filas_cambiadas", ()), 'pivote': paso_fuente.get("pivote"), 'filas_intercambio': paso_fuente.get("filas_intercambiadas") or (), 'bloque_resultado': paso.indice == datos.total_pasos - 1})
        with contenedor:
            ui.label('Bloque izquierdo: A → I · Bloque derecho: I → A⁻¹').classes(
                'texto-secundario fuente-pequena mb-2'
            )
            ui.html(tabla)

    def _crear_accion_glosa(self, pasos_fuente: list[dict], total: int):
        """Crea la acción de Glosa y añade el foco exacto del controlador."""
        def explicar(paso):
            """Envía al asistente los metadatos del paso seleccionado."""
            from src.frontend.controladores.operaciones_inversas import (
                ControladorOperacionesInversas,
            )

            foco = ControladorOperacionesInversas.construir_foco_paso(pasos_fuente, paso.indice)
            self.panel_ia.disparar_explicacion_paso({
                "indice": paso.indice + 1,
                "total": total,
                **paso.meta_explicar,
                **foco,
            })

        return explicar


_LINEAS_AYUDA = (
    "• La tabla es la matriz aumentada [A | I]: a la izquierda va A y a la derecha la identidad. La línea verde las separa.",
    "• Cada paso aplica UNA operación elemental de fila a la fila completa (ambos bloques a la vez).",
    "• Meta: que el bloque izquierdo quede igual a I. Cuando eso pasa, el bloque derecho es A⁻¹.",
    "• Colores: fila resaltada = fila modificada en ese paso · celda con borde = pivote · ámbar = filas intercambiadas · verde (último paso) = A⁻¹.",
)
