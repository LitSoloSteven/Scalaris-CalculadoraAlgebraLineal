"""Contrato de referencias cliente frente al espacio real publicado por los recursos."""
import pytest

from tests.comun import RAIZ
from tests.comun_integridad_cliente import errores_referencias, fragmentos_python


def test_referencias_python_existen_en_espacio_nombres_cliente():
    """Detecta nombres inexistentes aun cuando una guarda opcional evita la excepción."""
    fragmentos = fragmentos_python(sorted((RAIZ / "src").rglob("*.py")))
    recursos = [ruta.read_text(encoding="utf-8") for ruta in sorted((RAIZ / "src/frontend/recursos/js").glob("*.js"))]
    assert fragmentos
    errores = errores_referencias(fragmentos, recursos)
    assert not errores, "\n".join(errores)


def test_funcion_privada_no_se_confunde_con_global_exportada():
    """Una función dentro de IIFE no satisface un consumidor global inexistente."""
    fragmentos = [("ejemplo.py", 1, "window.scalaris.ausente(); funcionPrivada();")]
    recursos = ["(function(){ function funcionPrivada(){} window.scalaris = {}; })();"]
    errores = errores_referencias(fragmentos, recursos)
    assert any("window.scalaris.ausente" in error for error in errores)
    assert any("funcionPrivada" in error for error in errores)


def test_propiedad_opcional_y_objeto_publicado_se_resuelven():
    """Objetos anidados reales satisfacen rutas completas con optional chaining."""
    fragmentos = [("ejemplo.py", 1, "window.scalaris?.geometria?.registrar?.();")]
    recursos = ["window.scalaris = { geometria: { registrar: function(){} } };"]
    assert errores_referencias(fragmentos, recursos) == []


def test_llamada_global_ausente_sin_prefijos_es_detectada(tmp_path):
    """El descubrimiento usa emisores reales, sin depender de nombres defectuosos conocidos."""
    ruta = tmp_path / "ejemplo.py"
    ruta.write_text('def ejecutar():\n    ui.run_javascript("funcionAusente();")\n', encoding="utf-8")
    fragmentos = fragmentos_python([ruta])
    assert len(fragmentos) == 1
    assert any("funcionAusente" in error for error in errores_referencias(fragmentos, []))


def test_cadena_concatenada_y_referencia_interpolada_no_se_omiten(tmp_path):
    """Las cadenas completas y las alternativas literales conservan todas sus referencias."""
    ruta = tmp_path / "ejemplo.py"
    ruta.write_text('def ejecutar():\n    nombre = "ausente"\n    codigo = f"window.scalaris.{nombre}();"\n'
                    '    ui.run_javascript(codigo)\n    ui.run_javascript("funcionAusente(" + json.dumps("dato") + ");")\n', encoding="utf-8")
    fragmentos = fragmentos_python([ruta])
    errores = errores_referencias(fragmentos, ["window.scalaris = {};"])
    assert any("window.scalaris.ausente" in error for error in errores)
    assert any("funcionAusente" in error for error in errores)


@pytest.mark.parametrize("fragmento", [
    "function privada(){const funcionAusente=()=>{};} funcionAusente();",
    "(function(){function funcionAusente(){}})(); funcionAusente();",
    "{let funcionAusente=()=>{};} funcionAusente();",
    "function privada(funcionAusente){funcionAusente();} funcionAusente();",
])
def test_declaracion_en_otro_ambito_no_oculta_global_ausente(fragmento):
    """Una declaración privada no valida usos en el ámbito exterior."""
    errores = errores_referencias([("ejemplo.py", 1, fragmento)], [])
    assert any("funcionAusente" in error for error in errores)


@pytest.mark.parametrize("fragmento", [
    "function privada(){local(); var local=()=>{};} privada();",
    "function privada({local}){local();} privada({local:()=>{}});",
])
def test_parametros_y_declaraciones_elevadas_se_resuelven(fragmento):
    """Los enlaces reales del ámbito de la función satisfacen sus usos internos."""
    assert errores_referencias([("ejemplo.py", 1, fragmento)], []) == []
