"""Ejecución de invocaciones Python contra las animaciones reales del cliente."""
import json
import shutil
import subprocess

from tests.comun import RAIZ


def observar_invocaciones_cliente(codigos):
    """Devuelve selectores, duraciones y detección de ejecución ajena para cada invocación."""
    ejecutable = shutil.which("node")
    assert ejecutable, "Se necesita el runtime Node existente para comprobar el cliente."
    proceso = subprocess.run(
        [ejecutable, str(RAIZ / "tests/comun_invocaciones_cuadricula.js")],
        input=json.dumps(codigos), text=True, encoding="utf-8",
        capture_output=True, check=True, timeout=15,
    )
    return json.loads(proceso.stdout)
