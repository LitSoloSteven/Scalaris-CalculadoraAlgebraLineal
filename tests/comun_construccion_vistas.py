"""Montaje de páginas con controles reales NiceGUI y transporte de cliente aislado."""
import asyncio
import importlib
import inspect
from unittest.mock import AsyncMock

from fastapi import FastAPI
from nicegui import Client, core, run, ui

from src.frontend import rutas
from src.frontend.navegacion import ruta_de
from tests.comun import ejecutar_trabajador_simulado

VISTAS_RUTAS = {
    "inicio": ("inicio.vista_inicio", "VistaInicio"),
    "sistemas": ("sistemas_lineales.vista_sistemas_lineales", "VistaSistemasLineales"),
    "vectores": ("operaciones_vectores.vista_operaciones_vectores", "VistaOperacionesVectores"),
    "matrices": ("operaciones_matrices.vista_operaciones_matrices", "VistaOperacionesMatrices"),
    "inversa": ("operaciones_inversas.vista_operaciones_inversas", "VistaOperacionesInversas"),
    "determinantes": ("operaciones_matrices.vista_determinante", "VistaDeterminante"),
    "visualizador": ("geometria.vista_geometria", "VistaGeometria"),
    "leontief": ("operaciones_matrices.vista_leontief", "VistaLeontief"),
    "transformaciones": ("operaciones_matrices.vista_transformaciones", "VistaTransformaciones"),
    "bases": ("sistemas_numericos.vista_sistemas_numericos", "VistaSistemasNumericos"),
    "romanos": ("sistemas_numericos.vista_calculadora_romana", "VistaCalculadoraRomana"),
}


class RespuestaCliente:
    """Permite esperar el transporte simulado sin crear corrutinas abandonadas."""

    def __await__(self):
        async def responder():
            """Devuelve la respuesta simulada para aislar la comunicación de red."""
            return None
        return responder().__await__()


def registrar_paginas(monkeypatch) -> dict:
    """Usa el registro real y conserva sus constructores públicos de página."""
    paginas = {}

    def registrar(ruta, **opciones):
        """Procesa registrar con los datos recibidos."""
        def decorar(funcion):
            """Procesa decorar con los datos recibidos."""
            paginas[ruta] = funcion
            return funcion
        return decorar

    monkeypatch.setattr(ui, "page", registrar)
    monkeypatch.setattr(rutas, "app", FastAPI())
    monkeypatch.setattr(rutas.navegacion, "INICIO_HABILITADO", True)
    rutas.registrar_rutas()
    return paginas


def capturar_instancia(monkeypatch, herramienta: str) -> list:
    """Envuelve el constructor real para inspeccionar la instancia creada por la ruta."""
    modulo, nombre = VISTAS_RUTAS[herramienta]
    importado = importlib.import_module(f"src.frontend.vistas.{modulo}")
    constructor = getattr(importado, nombre)
    instancias = []

    def construir(*argumentos, **opciones):
        """Procesa construir con los datos recibidos."""
        instancia = constructor(*argumentos, **opciones)
        instancias.append(instancia)
        return instancia

    monkeypatch.setattr(importado, nombre, construir)
    return instancias


def preparar_transporte(monkeypatch, cliente: Client) -> list[str]:
    """Aísla navegador y trabajador, conservando elementos, manejadores y matemáticas reales."""
    llamadas = []

    def ejecutar(codigo, **opciones):
        """Procesa ejecutar con los datos recibidos."""
        llamadas.append(codigo)
        return RespuestaCliente()

    monkeypatch.setattr(ui, "run_javascript", ejecutar)
    monkeypatch.setattr(cliente, "run_javascript", ejecutar)
    monkeypatch.setattr(cliente, "connected", AsyncMock())
    monkeypatch.setattr(run, "io_bound", ejecutar_trabajador_simulado)
    monkeypatch.setattr(core, "loop", asyncio.get_running_loop())
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("SCALARIS_DOCK", "1")
    return llamadas


async def construir_pagina(monkeypatch, herramienta: str, comprobar, parametros=None):
    """Construye la ruta vacía y ejecuta la comprobación dentro del cliente real."""
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba_integridad"))
    preparar_transporte(monkeypatch, cliente)
    paginas = registrar_paginas(monkeypatch)
    ruta = "/" if herramienta == "inicio" else ruta_de(herramienta)
    instancias = capturar_instancia(monkeypatch, herramienta)
    try:
        with cliente:
            argumentos = dict(parametros or {})
            if herramienta == "inicio": argumentos["client"] = cliente
            resultado = paginas[ruta](**argumentos)
            if inspect.isawaitable(resultado): await resultado
            assert len(instancias) == 1
            assert len(cliente.elements) > 10
            await comprobar(instancias[0], cliente)
    finally:
        await cerrar_cliente(cliente, instancias)


async def cerrar_cliente(cliente: Client, instancias: list) -> None:
    """Detiene reproducciones y tareas del escenario antes de destruir su cliente."""
    for instancia in instancias:
        reproductor = getattr(instancia, "reproductor_pasos", None) or getattr(instancia, "reproductor", None)
        if reproductor: reproductor.detener()
    cliente.delete()
    pendientes = [tarea for tarea in asyncio.all_tasks() if tarea is not asyncio.current_task()]
    for tarea in pendientes: tarea.cancel()
    await asyncio.gather(*pendientes, return_exceptions=True)
