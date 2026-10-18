"""Estado de sesion y actualizacion cancelable de las herramientas matriciales."""
import asyncio
import copy
import time

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.ai.huellas import calcular_huella

MAXIMO_CALCULOS_RECIENTES = 5

_ESTADOS_HISTORIAL = {
    'SOLUCION_UNICA': ('Solución Única', 'texto-acento'),
    'SOLUCIONES_INFINITAS': ('Infinitas Soluciones', 'texto-advertencia'),
    'SIN_SOLUCION': ('Sin Solución', 'sesion-error'),
    'EXITO': ('Invertible', 'texto-acento'),
    'SINGULAR': ('Singular', 'sesion-error'),
}


def registrar_calculo(historial: list[dict], datos: dict) -> None:
    """Retiene una copia independiente del calculo y los cinco registros recientes."""
    historial.insert(0, {**copy.deepcopy(datos), 'hora': time.strftime('%H:%M')})
    del historial[MAXIMO_CALCULOS_RECIENTES:]


def describir_registro(datos: dict) -> dict:
    """Devuelve etiquetas y clases de presentacion de un registro de historial."""
    filas = datos.get('filas', datos.get('dimension', 0))
    columnas = datos.get('columnas', filas)
    texto, clase = _ESTADOS_HISTORIAL.get(datos['estado'], ('Error', 'sesion-error'))
    detalle = ''
    if 'metodo' in datos:
        detalle = f"Método: {datos['metodo'].replace('-', ' ').title()}"
    elif datos.get('determinante') is not None:
        detalle = f"det = {datos['determinante']}"
    return {'dimensiones': f'{filas}×{columnas}', 'estado': texto, 'clase': clase, 'detalle': detalle}


def cancelar_vista_previa(vista) -> None:
    """Cancela la tarea pendiente de la vista sin afectar otros clientes."""
    tarea = getattr(vista, 'tarea_vista_previa', None)
    if tarea is not None and not tarea.done():
        tarea.cancel()
    vista.tarea_vista_previa = None


def programar_vista_previa(vista) -> None:
    """Reemplaza la espera anterior si el contenedor de la vista sigue montado."""
    cancelar_vista_previa(vista)
    contenedor = getattr(vista, 'contenedor_vista_previa', None)
    if contenedor is None or contenedor.is_deleted:
        return
    vista.tarea_vista_previa = asyncio.create_task(_esperar_actualizacion(vista, contenedor))


async def _esperar_actualizacion(vista, contenedor) -> None:
    await asyncio.sleep(ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)
    if contenedor.is_deleted or contenedor is not vista.contenedor_vista_previa:
        return
    await vista._actualizar_vista_previa()


def invalidar_resultado(vista) -> None:
    """Retira el resultado y la huella; detiene el reproductor que los presentaba."""
    reproductor = getattr(vista, 'reproductor_pasos', None)
    if reproductor is not None:
        reproductor.detener()
    vista.reproductor_pasos = None
    vista.ultimo_resultado = None
    vista._huella_resultado = None
    vista._identificador_calculo = getattr(vista, '_identificador_calculo', 0) + 1
    notificar_edicion(vista)


def notificar_edicion(vista) -> None:
    """Incrementa la revision para descartar calculos anteriores incluso tras restaurar texto."""
    vista._revision_captura = getattr(vista, '_revision_captura', 0) + 1


def captura_sigue_vigente(vista, revision: int, huella: str, entrada: dict) -> bool:
    """Comprueba que el resultado pertenece a la revision y captura aun visibles."""
    return revision == vista._revision_captura and huella == calcular_huella(entrada)


def calculo_sigue_vigente(vista, identificador: int) -> bool:
    """Comprueba que ninguna solicitud o limpieza ha reemplazado este calculo."""
    return identificador == getattr(vista, '_identificador_calculo', 0)


def actualizar_contexto(vista) -> None:
    """Notifica a Glosa una captura o resultado actualizado cuando esta disponible."""
    panel = getattr(vista, 'panel_ia', None)
    if panel and hasattr(panel, 'programar_actualizacion_contexto'):
        panel.programar_actualizacion_contexto()
