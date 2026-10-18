"""Utilidades comunes y compartidas para la suite de pruebas."""
from pathlib import Path
import asyncio
import json
import shutil
import subprocess

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVOS_CSS = [
    RAIZ / "src" / "frontend" / "recursos" / "css" / "tokens.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "base.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "disposicion.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "componentes_entradas.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "componentes_controles.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_navegacion.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_inicio_matriz.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_inicio_ventanas_emergentes.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_inicio_adaptable.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_glosa_panel_lateral.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_glosa_componentes.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_glosa_bitacora.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_inversa.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_geometria.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "movimiento.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "reproductor_pasos.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "pasos_numericos.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_modelos.css",
    RAIZ / "src" / "frontend" / "recursos" / "css" / "vistas_numericos.css",
]


def leer_css_completo() -> str:
    """Lee y concatena el conjunto ordenado de hojas de estilo en orden de cascada."""
    return "\n".join(archivo.read_text(encoding="utf-8") for archivo in ARCHIVOS_CSS)


async def comprobar_tarea_en_cliente(lanzador, cliente, valor_esperado):
    """Comprueba el protocolo de entrada y salida de una tarea con un cliente simulado."""
    dentro_del_cliente = False

    async def corrutina():
        """Procesa corrutina con los datos recibidos."""
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


async def ejecutar_trabajador_simulado(funcion, *argumentos, **opciones):
    """Ejecuta directamente la función que una prueba delega al trabajador de NiceGUI."""
    return funcion(*argumentos, **opciones)


def limpiar_almacen_transferencia():
    """Vacía el almacén de transferencias para aislar un escenario de prueba."""
    from src.frontend.componentes.transferencia import _ALMACEN
    _ALMACEN.clear()


def analizar_fuentes_javascript(fuentes):
    """Mide fuentes con Acorn de Node; propaga errores de sintaxis o del proceso."""
    ejecutable = shutil.which("node")
    if ejecutable is None:
        raise RuntimeError("Node no está disponible para ejecutar la auditoría JavaScript")
    proceso = subprocess.run(
        [ejecutable, "--expose-internals", str(RAIZ / "tests/comun_auditoria_javascript.js")],
        input=json.dumps(fuentes), text=True, encoding="utf-8",
        capture_output=True, check=True, timeout=15,
    )
    return json.loads(proceso.stdout)
