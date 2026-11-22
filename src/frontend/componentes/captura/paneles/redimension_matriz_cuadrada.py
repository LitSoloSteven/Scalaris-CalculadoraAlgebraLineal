"""Actualización del borde de la matriz cuadrada sin reconstruir su interior."""
DIMENSION_MAXIMA_CELDA_NORMAL = 8


def actualizar_etiqueta_dimension(panel, identificador: str) -> None:
    """Actualiza el contador y la etiqueta accesoria con la dimensión actual del panel."""
    if panel.etiqueta_dimension:
        panel.etiqueta_dimension.set_text(str(panel.dimension))
    if panel.etiqueta_dimension_matriz:
        panel.etiqueta_dimension_matriz.set_content(f'{identificador} <span class="separador-punto">·</span> {panel.dimension} &times; {panel.dimension}')


def redimensionar_celdas(panel, anterior: int) -> None:
    """Actualiza las celdas afectadas por un cambio unitario; reconstruye los saltos mayores."""
    if abs(panel.dimension - anterior) != 1 or not _estructura_completa(panel, anterior):
        panel._renderizar_completa()
        return
    if panel.dimension > anterior:
        _agregar_borde(panel, anterior)
    else:
        _quitar_borde(panel)
    if (anterior > DIMENSION_MAXIMA_CELDA_NORMAL) != (panel.dimension > DIMENSION_MAXIMA_CELDA_NORMAL):
        _actualizar_tamano_celdas(panel)


def _estructura_completa(panel, anterior: int) -> bool:
    return bool(panel.contenedor_cuadricula) and len(panel.filas_interfaz) == len(panel.celdas) == anterior and all(len(fila) == anterior for fila in panel.celdas)


def _agregar_borde(panel, anterior: int) -> None:
    for fila in range(anterior):
        with panel.filas_interfaz[fila]:
            panel.celdas[fila].append(panel._crear_celda_ui(fila, anterior))
    with panel.contenedor_cuadricula:
        panel._anadir_fila_dom(anterior)


def _quitar_borde(panel) -> None:
    panel.filas_interfaz.pop().delete()
    panel.celdas.pop()
    for fila in panel.celdas:
        fila.pop().delete()


def _actualizar_tamano_celdas(panel) -> None:
    agregar, quitar = ('cuadricula-celda-compacta', 'cuadricula-celda') if panel.dimension > DIMENSION_MAXIMA_CELDA_NORMAL else ('cuadricula-celda', 'cuadricula-celda-compacta')
    for fila in panel.celdas:
        for celda in fila:
            celda.classes(add=agregar, remove=quitar)
