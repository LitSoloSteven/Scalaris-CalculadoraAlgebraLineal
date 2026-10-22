"""Integración de las pruebas nativas del cliente en la suite del proyecto."""
import shutil
import subprocess

from tests.comun import RAIZ


def test_suite_javascript_completa():
    """Ejecuta todos los archivos de prueba JavaScript y comprueba su resultado."""
    ejecutable = shutil.which("node")
    assert ejecutable, "Se necesita el runtime Node existente para comprobar el cliente."
    pruebas = sorted((RAIZ / "tests").glob("test_*.js"))
    assert pruebas, "No se encontraron pruebas JavaScript del cliente."
    resultado = subprocess.run(
        [ejecutable, "--expose-internals", "--test", *map(str, pruebas)],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
