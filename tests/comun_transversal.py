"""Ejecución del análisis transversal del cliente con el parser existente."""
import json
import subprocess

from tests.comun import RAIZ


def analizar_fuentes_cliente(fuentes):
    """Devuelve nombres, comentarios y duplicados AST; propaga fallos del parser o proceso."""
    proceso = subprocess.run(
        ['node', '--expose-internals', str(RAIZ / 'tests/comun_transversal_javascript.js')],
        input=json.dumps(fuentes), text=True, encoding='utf-8', capture_output=True,
        check=True, timeout=30,
    )
    return json.loads(proceso.stdout)
