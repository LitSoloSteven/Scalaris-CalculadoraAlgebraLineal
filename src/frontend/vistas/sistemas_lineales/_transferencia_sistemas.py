"""Carga de una matriz transferida a los controles del sistema lineal."""
from src.frontend.componentes.transferencia import consumir_matriz, renderizar_aviso_transferencia, limpiar_url_transferencia
from src.backend.constantes import DIMENSION_MAXIMA_SISTEMAS


def procesar_transferencia_matriz(vista, token: str) -> None:
    """Consume el token válido, reconstruye la captura y retira el parámetro URL."""
    resultado = consumir_matriz(token, dimension_maxima=DIMENSION_MAXIMA_SISTEMAS)
    if resultado is None:
        return
    with vista.contenedor_transferencia:
        dimension = len(resultado.datos) if resultado.datos else 0
        renderizar_aviso_transferencia(resultado, f"Cargamos A ({dimension}×{dimension}) desde {resultado.nombre_origen}. El vector b está vacío: complétalo y presiona Resolver.")
    if resultado.estado == 'exito':
        _cargar_cuadricula(vista, resultado.datos, dimension)
    limpiar_url_transferencia()


def _cargar_cuadricula(vista, datos: list, dimension: int) -> None:
    if vista.pestanas_modo.value == 'Ecuaciones':
        vista.pestanas_modo.set_value('Matriz')
    vista.cuadricula.limpiar()
    vista.cuadricula.filas = vista.cuadricula.columnas = dimension
    vista.cuadricula._cache_coeficientes.clear()
    vista.cuadricula._cache_independientes.clear()
    for i, fila in enumerate(datos):
        for j, valor in enumerate(fila):
            if valor != "0":
                vista.cuadricula._cache_coeficientes[(i, j)] = valor
    vista.cuadricula.generar_cuadricula()
    vista._al_cambiar_cuadricula()
