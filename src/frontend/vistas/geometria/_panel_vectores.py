"""Adaptación del panel vectorial para identificar celdas de las escenas."""
from nicegui import ui
from src.frontend.componentes.vector_capture import VectorCapturePanel


class PanelVectoresGeometria(VectorCapturePanel):
    """Añade referencias de celda al componente existente sin duplicar su captura."""

    def _nombre_celda_error(self, nombre: str) -> str:
        posicion = list(self.vectors).index(nombre)
        if self.first_vector_fixed_label:
            return 'b' if posicion == 0 else f'v_{posicion}'
        return ('u', 'v')[posicion]

    def render_vector_grid(self, nombre: str) -> None:
        """Renderiza las componentes y vincula cada celda con el selector de errores."""
        super().render_vector_grid(nombre)
        contenedor = self.vectors[nombre].get('ui_container')
        if not contenedor:
            return
        entradas = [elemento for elemento in contenedor.descendants() if isinstance(elemento, ui.input)]
        for indice, entrada in enumerate(entradas):
            entrada.props.update({
                'data-geometria-vector': f'{self.panel_id}_{self._nombre_celda_error(nombre)}',
                'data-geometria-indice': str(indice),
                'data-geometria-orientacion': 'columna' if self.vectors[nombre]['orientation'] == 'column' else 'fila',
            })
