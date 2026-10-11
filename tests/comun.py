"""Utilidades comunes y compartidas para la suite de pruebas."""
from pathlib import Path
import asyncio

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVOS_CSS = [
    RAIZ / "src" / "frontend" / "assets" / "css" / "tokens.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "base.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "layout.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "componentes_entradas.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "componentes_controles.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_navegacion.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_hub_matriz.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_hub_popovers.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_hub_adaptable.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_glosa_dock.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_glosa_componentes.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_inversa.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "vistas_geometria.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "movimiento.css",
    RAIZ / "src" / "frontend" / "assets" / "css" / "reproductor_pasos.css",
]


def leer_css_completo() -> str:
    """Lee y concatena el conjunto ordenado de hojas de estilo en orden de cascada."""
    return "\n".join(archivo.read_text(encoding="utf-8") for archivo in ARCHIVOS_CSS)


async def comprobar_tarea_en_cliente(lanzador, cliente, valor_esperado):
    """Comprueba el protocolo de entrada y salida de una tarea con un cliente simulado."""
    dentro_del_cliente = False

    async def corrutina():
        nonlocal dentro_del_cliente
        if cliente.entradas == 1 and cliente.salidas == 0:
            dentro_del_cliente = True
        return valor_esperado

    tarea = lanzador(corrutina())
    assert isinstance(tarea, asyncio.Task)
    resultado = await tarea
    assert resultado == valor_esperado
    assert dentro_del_cliente is True
    assert cliente.entradas == 1
    assert cliente.salidas == 1


async def ejecutar_trabajador_simulado(funcion, *args, **kwargs):
    """Ejecuta directamente la función que una prueba delega al trabajador de NiceGUI."""
    return funcion(*args, **kwargs)


def limpiar_almacen_handoff():
    """Vacía el almacén de transferencias para aislar un escenario de prueba."""
    from src.frontend.componentes.handoff import _ALMACEN
    _ALMACEN.clear()
