"""Construcción y redimensión de entradas de coeficientes y términos independientes."""
from typing import Any
from nicegui import ui
from .cuadricula_base import propiedades_celda_accesible
from .redimension_rectangular import actualizar_rectangulo


def crear_coeficiente(cuadricula: Any, fila: int, columna: int) -> ui.input:
    """Crea un coeficiente con valor exacto, coordenadas y nombre accesible."""
    propiedades = propiedades_celda_accesible(fila, columna, nombre_campo=f'r{fila}c{columna}')
    celda = ui.input(value=cuadricula._cache_coeficientes.get((fila, columna), ''), placeholder='',
                     on_change=lambda evento: cuadricula._actualizar_celda(False, fila, columna, evento.value))
    return celda.classes('matriz-entrada cuadricula-celda').props(propiedades)


def crear_fila_ecuaciones(cuadricula: Any, indice: int) -> None:
    """Añade una fila con coeficientes, igualdad y término independiente."""
    with ui.row().classes('items-center gap-2 mb-2 no-wrap').props(f'data-cuadricula-fila="{indice}"') as fila:
        entradas = [crear_coeficiente(cuadricula, indice, columna) for columna in range(cuadricula.columnas)]
        ui.label('=').classes('w-8 text-center matematicas-etiqueta text-xl flex-shrink-0')
        valor = '0' if cuadricula.modo_homogeneo else cuadricula._cache_independientes.get(indice, '')
        propiedades = propiedades_celda_accesible(indice, cuadricula.columnas, nombre_campo=f'r{indice}cb')
        independiente = ui.input(value=valor, placeholder='', on_change=lambda evento: cuadricula._actualizar_celda(
            True, indice, 0, evento.value)).classes('matriz-entrada cuadricula-celda').props(propiedades)
        if cuadricula.modo_homogeneo:
            independiente.props('readonly')
    cuadricula.entradas_coeficientes.append(entradas)
    cuadricula.entradas_independientes.append(independiente)
    cuadricula.filas_interfaz.append(fila)


def redimensionar_ecuaciones(cuadricula: Any, anterior: tuple[int, int]) -> bool:
    """Actualiza el borde y las coordenadas de b; indica si se conservó el interior."""
    estado = {'entradas': cuadricula.entradas_coeficientes, 'filas_interfaz': cuadricula.filas_interfaz,
              'contenido': getattr(cuadricula, 'contenido_celdas', None)}
    actual = cuadricula.filas, cuadricula.columnas
    def _agregar_coeficiente(fila, columna):
        celda = crear_coeficiente(cuadricula, fila, columna)
        celda.move(target_index=columna)
        return celda
    if not actualizar_rectangulo(estado, anterior, actual,
                                lambda indice: crear_fila_ecuaciones(cuadricula, indice), _agregar_coeficiente):
        return False
    del cuadricula.entradas_independientes[cuadricula.filas:]
    for indice, entrada in enumerate(cuadricula.entradas_independientes):
        entrada.props(propiedades_celda_accesible(indice, cuadricula.columnas, nombre_campo=f'r{indice}cb'))
    return True


def actualizar_presentacion(cuadricula: Any) -> None:
    """Actualiza la forma visible y disponibilidad de los controles de dimensión."""
    texto_forma = 'Sistema Cuadrado' if cuadricula.filas == cuadricula.columnas else 'Sistema Rectangular'
    if cuadricula.etiqueta_forma:
        cuadricula.etiqueta_forma.set_content(
            f'{texto_forma} <span class="separador-punto">·</span> {cuadricula.filas} &times; {cuadricula.columnas}')
    cuadricula._actualizar_botones_dimension()
