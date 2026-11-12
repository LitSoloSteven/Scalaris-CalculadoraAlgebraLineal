"""Auditorías explícitas de los módulos compartidos y sus pruebas nuevas."""
import ast

import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as auditoria

_RUTAS = (
    "src/frontend/controladores/captura_real.py",
    "src/frontend/controladores/calculo_raices.py",
    "src/frontend/componentes/tabla_iteraciones.py",
    "src/frontend/controladores/biseccion/captura_criterio.py",
    "src/frontend/vistas/biseccion/calculo_individual.py",
    "src/frontend/vistas/biseccion/tabla_iteraciones.py",
    "tests/test_regla_falsa_reutilizacion_captura.py",
    "tests/test_regla_falsa_reutilizacion_calculo.py",
    "tests/test_regla_falsa_reutilizacion_tabla.py",
    "tests/test_regla_falsa_reutilizacion.py",
    "tests/test_regla_falsa_dependencia_interfaz.py",
)
_COMPROBACIONES = (
    auditoria.test_limites_tamanio_y_complejidad,
    auditoria.test_docstrings_publicos,
    auditoria.test_identificadores_idioma_y_ascii,
    auditoria.test_comentarios_y_textos_limpios,
    auditoria.test_reglas_python_frontend,
)


@pytest.mark.parametrize("ruta", _RUTAS)
@pytest.mark.parametrize("comprobar", _COMPROBACIONES, ids=lambda funcion: funcion.__name__)
def test_modulos_extraidos_cumplen_las_auditorias_existentes(monkeypatch, ruta, comprobar):
    """Incluye las fuentes nuevas sin ampliar ni debilitar los manifiestos existentes."""
    archivo = RAIZ / ruta
    assert archivo.is_file()
    monkeypatch.setattr(auditoria, "RUTAS_AUDITADAS", (archivo,))
    comprobar()


@pytest.mark.parametrize("ruta", _RUTAS[:3])
def test_componentes_compartidos_no_importan_un_metodo_concreto(ruta):
    """La reutilización no depende de clases ni contratos de bisección o regla falsa."""
    arbol = ast.parse((RAIZ / ruta).read_text(encoding="utf-8"))
    modulos = [nodo.module for nodo in ast.walk(arbol) if isinstance(nodo, ast.ImportFrom)]
    assert all("biseccion" not in (modulo or "") and "regla_falsa" not in (modulo or "")
               for modulo in modulos)
