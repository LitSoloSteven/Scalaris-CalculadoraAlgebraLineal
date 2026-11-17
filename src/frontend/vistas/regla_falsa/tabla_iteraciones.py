"""Tabla de regla falsa con el formato y los textos de su traza."""
from src.frontend.componentes.tabla_raices_seleccionable import FormatoTablaRaices, TablaRaicesSeleccionable
from src.frontend.controladores.regla_falsa.tabla import COLUMNAS, filas_tabla

_FORMATO = FormatoTablaRaices(
    descripcion="Selecciona una fila para ver su secante. El error relativo no está disponible en la primera fila o si c = 0.",
    nombre_region="Tabla de regla falsa con desplazamiento horizontal",
    clase_region="regla-falsa-tabla",
    preparar_filas=lambda filas, completo: (COLUMNAS, filas_tabla(filas, completo)),
)


class TablaReglaFalsa(TablaRaicesSeleccionable):
    """Configura la tabla seleccionable con los datos de regla falsa."""

    def __init__(self, filas: tuple, al_elegir):
        super().__init__(filas, al_elegir, _FORMATO)
