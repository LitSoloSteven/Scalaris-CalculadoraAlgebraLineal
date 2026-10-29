"""Extracción estática de código cliente emitido por Python y publicado en recursos."""
import ast
import json
import re
import subprocess

from tests.comun import RAIZ
from tests.comun_cadenas_cliente import ResolutorCadenasCliente

RAICES_EXTERNAS = {
    "window", "document", "navigator", "history", "localStorage", "console",
    "location",
    "Math", "JSON", "Promise", "Array", "Object", "String", "Number",
    "setTimeout", "clearTimeout", "requestAnimationFrame", "cancelAnimationFrame",
    "getComputedStyle", "CustomEvent", "parseInt", "parseFloat", "encodeURIComponent",
    "URL", "URLSearchParams", "Date", "Blob", "Set", "Map", "fetch",
}


def fragmentos_python(rutas, solo_emisiones=False, emisores=("run_javascript", "_ejecutar_javascript")) -> list[tuple[str, int, str]]:
    """Recoge cadenas ejecutables completas, interpoladas y guardadas en variables."""
    fragmentos = []
    for ruta in rutas:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        padres = {hijo: nodo for nodo in ast.walk(arbol) for hijo in ast.iter_child_nodes(nodo)}
        resolutor = ResolutorCadenasCliente(arbol, padres)
        argumentos = _argumentos_cliente(arbol, emisores)
        fragmentos.extend(_fragmentos_arbol(arbol, resolutor, padres, (ruta, argumentos), solo_emisiones))
    return fragmentos


def _argumentos_cliente(arbol, emisores):
    argumentos = set()
    for nodo in ast.walk(arbol):
        argumento = _argumento_cliente(nodo, emisores)
        if argumento is not None: argumentos.add(argumento)
    return argumentos


def _argumento_cliente(nodo, emisores):
    if not isinstance(nodo, ast.Call) or not isinstance(nodo.func, ast.Attribute): return None
    if nodo.func.attr not in emisores: return None
    if nodo.args: return nodo.args[0]
    return next((opcion.value for opcion in nodo.keywords if opcion.arg in {"code", "content", "codigo"}), None)


def _fragmentos_arbol(arbol, resolutor, padres, contexto, solo_emisiones=False):
    ruta, argumentos = contexto
    nombre_archivo = ruta.relative_to(RAIZ).as_posix() if ruta.is_relative_to(RAIZ) else str(ruta)
    encontrados = []
    for nodo in ast.walk(arbol):
        if isinstance(padres.get(nodo), (ast.JoinedStr, ast.BinOp)): continue
        if isinstance(nodo, ast.Name) and nodo not in argumentos: continue
        encontrados.extend((nombre_archivo, nodo.lineno, _expresion_propiedad(cadena))
                           for cadena in resolutor.variantes(nodo)
                           if nodo in argumentos or (not solo_emisiones and "window." in cadena))
    return encontrados


def _expresion_propiedad(cadena):
    coincidencia = re.fullmatch(r':[^=]+="([^"]*)"', cadena)
    return coincidencia.group(1) if coincidencia else cadena


def analizar_cliente(fragmentos: list[str], recursos: list[str]) -> dict:
    """Analiza AST JavaScript con Acorn incluido en Node, sin dependencias nuevas."""
    proceso = subprocess.run(
        ["node", "--expose-internals", str(RAIZ / "tests/comun_integridad_cliente.js")],
        input=json.dumps({"recursos": recursos, "fragmentos": fragmentos}),
        text=True, encoding="utf-8", capture_output=True, check=True, timeout=15,
    )
    return json.loads(proceso.stdout)


def errores_referencias(fragmentos: list[tuple], recursos: list[str]) -> list[str]:
    """Compara cada referencia con publicaciones reales y APIs externas explícitas."""
    analisis = analizar_cliente([cadena for _, _, cadena in fragmentos], recursos)
    publicadas = set(analisis["publicadas"])
    errores = []
    for (ruta, linea, _), resultado in zip(fragmentos, analisis["resultados"]):
        if "error" in resultado:
            errores.append(f"{ruta}:{linea}: JavaScript no analizable: {resultado['error']}")
        else:
            errores.extend(f"{ruta}:{linea}: referencia ausente {nombre}" for nombre in resultado["referencias"]
                           if nombre not in publicadas and nombre not in RAICES_EXTERNAS)
    return errores
