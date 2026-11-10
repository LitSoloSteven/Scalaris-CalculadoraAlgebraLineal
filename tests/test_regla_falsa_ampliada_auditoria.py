"""Auditoría de las responsabilidades y límites del dominio y la integración ampliada."""
import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as reglas


@pytest.mark.parametrize("comprobar", [reglas.test_limites_tamanio_y_complejidad, reglas.test_docstrings_publicos,
    reglas.test_identificadores_idioma_y_ascii, reglas.test_comentarios_y_textos_limpios, reglas.test_reglas_python_frontend])
def test_modulos_ampliados_cumplen_reglas(monkeypatch, comprobar):
    rutas = list((RAIZ / "src/backend/resolutores/raices").glob("*regla_falsa*.py"))
    rutas.extend((RAIZ / "src/frontend/controladores/regla_falsa").glob("*.py"))
    rutas.extend((RAIZ / "src/frontend/vistas/regla_falsa").glob("*.py"))
    rutas.append(RAIZ / "src/backend/resolutores/raices/sugerencias_dominio.py")
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", tuple(rutas))
    comprobar()
