"""Auditoría explícita de la integración sin alterar manifiestos existentes."""
import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as reglas

_RUTAS = (
    "componentes/raices/captura/modos_captura_raices.py", "controladores/raices/compartido/exploracion/captura_exploratoria_raices.py",
    "vistas/raices/biseccion/base/modos_captura.py",
    "componentes/raices/exploracion/paso_exploracion_raices.py", "componentes/raices/exploracion/exploracion_raices.py",
    "vistas/raices/biseccion/exploracion/exploracion.py", "vistas/raices/regla_falsa/base/modos_captura.py",
    "vistas/raices/regla_falsa/exploracion/seleccion_candidato.py", "vistas/raices/regla_falsa/exploracion/exploracion.py",
    "vistas/raices/regla_falsa/captura/captura.py", "vistas/regla_falsa/composicion.py",
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
