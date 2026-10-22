"""Adaptación del panel vectorial para identificar celdas de las escenas."""
from nicegui import ui
from src.frontend.componentes.captura_vectores import PanelCapturaVectores


class PanelVectoresGeometria(PanelCapturaVectores):
    """Añade referencias de celda al componente existente sin duplicar su captura."""

    def _nombre_celda_error(self, nombre: str) -> str:
        posicion = list(self.vectores).index(nombre)
        if self.etiqueta_fija_primer_vector:
            return 'b' if posicion == 0 else f'v_{posicion}'
        return ('u', 'v')[posicion]

    def renderizar_cuadricula_vector(self, nombre: str) -> None:
        """Renderiza las componentes y vincula cada celda con el selector de errores."""
        super().renderizar_cuadricula_vector(nombre)
        contenedor = self.vectores[nombre].get('contenedor')
        if not contenedor:
            return
        entradas = [elemento for elemento in contenedor.descendants() if isinstance(elemento, ui.input)]
        for indice, entrada in enumerate(entradas):
            entrada.props.update({
                'data-geometria-vector': f'{self.identificador_panel}_{self._nombre_celda_error(nombre)}',
                'data-geometria-indice': str(indice),
                'data-geometria-orientacion': 'columna' if self.vectores[nombre]['orientacion'] == 'columna' else 'fila',
            })
