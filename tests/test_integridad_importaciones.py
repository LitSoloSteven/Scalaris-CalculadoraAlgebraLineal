"""Contrato de resolución de importaciones internas de producción y consumidores."""
from tests.comun import RAIZ
from tests.comun_integridad_importaciones import (
    errores_importaciones, referencias_importadas, resolver_referencia,
)


def test_todas_las_importaciones_internas_resuelven():
    """Detecta módulos o símbolos rotos, también dentro de funciones y métodos."""
    rutas = sorted((RAIZ / "src").rglob("*.py")) + sorted((RAIZ / "tests").rglob("*.py"))
    errores = errores_importaciones(rutas)
    assert not errores, "\n".join(errores)


def test_importacion_diferida_inexistente_no_se_omite():
    """Una referencia diferida incorrecta se identifica sin ejecutar su función."""
    ruta = RAIZ / "src/frontend/rutas.py"
    referencias = referencias_importadas(ruta, "def construir():\n    from src.frontend import simbolo_inexistente\n")
    assert referencias == [(2, "src.frontend", "simbolo_inexistente")]
    assert resolver_referencia(*referencias[0][1:]) is not None


def test_importacion_relativa_y_submodulo_resuelven():
    """El arnés sigue paquetes relativos y la semántica de from paquete import módulo."""
    ruta = RAIZ / "src/frontend/vistas/operaciones_vectores/controles.py"
    referencias = referencias_importadas(ruta, "from . import contexto\nimport src.backend.modelos.matriz\n")
    assert referencias == [(1, "src.frontend.vistas.operaciones_vectores", "contexto"),
                           (2, "src.backend.modelos.matriz", None)]
    assert all(resolver_referencia(modulo, simbolo) is None for _, modulo, simbolo in referencias)
