"""Auditoría explícita de la integración sin alterar manifiestos existentes."""
import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as reglas

_RUTAS = (
    "componentes/modos_captura_raices.py", "controladores/captura_exploratoria_raices.py",
    "vistas/biseccion/modos_captura.py",
    "componentes/paso_exploracion_raices.py", "componentes/exploracion_raices.py",
    "vistas/biseccion/exploracion.py", "vistas/regla_falsa/modos_captura.py",
    "vistas/regla_falsa/seleccion_candidato.py", "vistas/regla_falsa/exploracion.py",
    "vistas/regla_falsa/captura.py", "vistas/regla_falsa/composicion.py",
    "vistas/regla_falsa/vista_regla_falsa.py",
)


@pytest.mark.parametrize("comprobar", [
    reglas.test_limites_tamanio_y_complejidad, reglas.test_docstrings_publicos,
    reglas.test_identificadores_idioma_y_ascii, reglas.test_comentarios_y_textos_limpios,
    reglas.test_reglas_python_frontend,
])
def test_integracion_de_exploracion_cumple_reglas(monkeypatch, comprobar):
    """Aplica tamaños, responsabilidades, idioma y documentación a todos los módulos afectados."""
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", tuple(RAIZ / "src/frontend" / ruta for ruta in _RUTAS))
    comprobar()
