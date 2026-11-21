"""Auditoría de las responsabilidades y límites del dominio y la integración ampliada."""
import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as reglas


@pytest.mark.parametrize("comprobar", [reglas.test_limites_tamanio_y_complejidad, reglas.test_docstrings_publicos,
    reglas.test_identificadores_idioma_y_ascii, reglas.test_comentarios_y_textos_limpios, reglas.test_reglas_python_frontend])
def test_modulos_ampliados_cumplen_reglas(monkeypatch, comprobar):
    """Audita todos los módulos ampliados con las reglas comunes sin cambiar sus manifiestos."""
    rutas = list((RAIZ / "src/backend/resolutores/raices").rglob("*regla_falsa*.py"))
    rutas.extend(RAIZ / ruta for ruta in (
        "src/frontend/controladores/regla_falsa/__init__.py",
        "src/frontend/controladores/raices/regla_falsa/captura/captura.py",
        "src/frontend/controladores/raices/regla_falsa/captura/configuracion_ampliada.py",
        "src/frontend/controladores/regla_falsa/contexto_regla_falsa.py",
        "src/frontend/controladores/raices/regla_falsa/captura/continuidad_intervalo.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/controlador.py",
        "src/frontend/controladores/regla_falsa/diagnostico.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/ejecucion_ampliada.py",
        "src/frontend/controladores/regla_falsa/formulas_procedimiento.py",
        "src/frontend/controladores/regla_falsa/pasos.py",
        "src/frontend/controladores/regla_falsa/pasos_ampliados.py",
        "src/frontend/controladores/regla_falsa/presentacion.py",
        "src/frontend/controladores/regla_falsa/presentacion_ampliada.py",
        "src/frontend/controladores/regla_falsa/presentacion_examen.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/presentacion_grafica.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/resolucion_multiple.py",
        "src/frontend/controladores/regla_falsa/salidas_regla_falsa.py",
        "src/frontend/controladores/raices/regla_falsa/captura/serializacion.py",
        "src/frontend/controladores/regla_falsa/tabla.py",
        "src/frontend/controladores/raices/regla_falsa/captura/validacion_contextual.py",
    ))
    rutas.extend((RAIZ / "src/frontend/vistas/regla_falsa").glob("*.py"))
    rutas.append(RAIZ / "src/backend/resolutores/raices/continuidad/analisis/sugerencias_dominio.py")
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", tuple(rutas))
    comprobar()
