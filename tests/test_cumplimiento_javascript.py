"""Límites estructurales de JavaScript medidos con el parser incluido en Node."""
import json
import shutil
import subprocess

from tests.comun import RAIZ
from tests.rutas_auditadas import RUTAS_AUDITADAS


def _analizar_archivos_javascript():
    ejecutable = shutil.which("node")
    if ejecutable is None:
        raise RuntimeError("Node no está disponible para ejecutar la auditoría JavaScript")
    archivos = [{"ruta": str(ruta.relative_to(RAIZ)), "contenido": ruta.read_text(encoding="utf-8")}
                for ruta in RUTAS_AUDITADAS if ruta.suffix == ".js"]
    proceso = subprocess.run(
        [ejecutable, "--expose-internals", str(RAIZ / "tests" / "comun_auditoria_javascript.js")],
        input=json.dumps(archivos), text=True, encoding="utf-8",
        capture_output=True, check=True, timeout=15,
    )
    return json.loads(proceso.stdout)


def test_limites_funciones_y_clases_javascript():
    """Cada función, callback y clase del manifiesto cumple los límites duros."""
    for archivo in _analizar_archivos_javascript():
        for clase in archivo["clases"]:
            assert clase["lineas"] <= 200, f"{archivo['ruta']}:{clase['nombre']} supera 200 líneas"
        for funcion in archivo["funciones"]:
            ubicacion = f"{archivo['ruta']}:{funcion['nombre']}:{funcion['linea']}"
            assert funcion["lineas"] <= 40, f"{ubicacion} tiene {funcion['lineas']} líneas"
            assert funcion["parametros"] <= 5, f"{ubicacion} tiene {funcion['parametros']} parámetros"
            assert funcion["anidamiento"] <= 3, f"{ubicacion} anidamiento {funcion['anidamiento']}"
            assert funcion["complejidad"] <= 10, f"{ubicacion} complejidad {funcion['complejidad']}"
