"""Auditoría explícita de los contratos, servicio y pruebas del lote de falsa posición."""
import pytest

from tests import test_cumplimiento_reglas as reglas
from tests.comun import RAIZ


@pytest.mark.parametrize("comprobar", [reglas.test_limites_tamanio_y_complejidad,
    reglas.test_docstrings_publicos, reglas.test_identificadores_idioma_y_ascii,
    reglas.test_comentarios_y_textos_limpios])
def test_contrato_y_lote_cumplen_reglas_compartidas(monkeypatch, comprobar):
    """Incluye archivos nuevos en las auditorías sin modificar los manifiestos existentes."""
    nombres = ("contrato_lote_regla_falsa.py", "resolucion_multiple_regla_falsa.py",
               "contrato_resolucion_multiple.py")
    rutas = [RAIZ / "src/backend/resolutores/raices" / nombre for nombre in nombres]
    rutas.extend((RAIZ / "tests").glob("test_regla_falsa_lote_*.py"))
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", tuple(rutas))
    comprobar()
