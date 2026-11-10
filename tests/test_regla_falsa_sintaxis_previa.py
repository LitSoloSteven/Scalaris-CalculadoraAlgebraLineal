"""Sintaxis parcial segura y auditoría explícita de los módulos compartidos."""
import json

import pytest

from src.frontend.controladores.formato_funcion_real import formatear_expresion
from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from tests import test_cumplimiento_reglas as reglas
from tests.comun import RAIZ
from tests.comun_regla_falsa_vista import ejecutar_escenario

_MODULOS = (
    "controladores/muestreo_raices.py", "controladores/formato_funcion_real.py",
    "controladores/vista_previa_raices.py", "controladores/seleccion_muestra_raices.py",
    "controladores/biseccion/muestreo.py", "controladores/biseccion/formato_expresion.py",
    "controladores/biseccion/vista_previa.py", "controladores/regla_falsa/presentacion_grafica.py",
    "controladores/regla_falsa/formulas_procedimiento.py", "componentes/previa_expresion_raices.py",
    "componentes/borrador_intervalo_raices.py", "componentes/figura_funcion_real.py",
    "vistas/biseccion/previa_expresion.py", "vistas/biseccion/seleccion_grafico.py", "vistas/biseccion/figura.py",
    "vistas/regla_falsa/rango_previo.py", "vistas/regla_falsa/vista_previa.py",
    "vistas/regla_falsa/seleccion_grafico.py", "vistas/regla_falsa/composicion.py",
    "vistas/regla_falsa/exploracion.py", "vistas/regla_falsa/vista_regla_falsa.py",
    "vistas/regla_falsa/procedimiento.py",
)


@pytest.mark.parametrize("expresion", ["x+", "desconocida(x)", "<img src=x onerror=alert(1)>", "x" * 10000])
def test_sintaxis_parcial_o_html_solo_produce_orientacion(expresion):
    """El parser restringido devuelve mensajes serializables y rechaza la proyección TeX."""
    respuesta = preparar_vista_previa({"expresion": expresion, "x_min": "-2", "x_max": "2"})
    assert respuesta["estado"] == "ERROR" and "muestra" not in respuesta
    json.dumps(respuesta, allow_nan=False)
    with pytest.raises(ValueError):
        formatear_expresion(expresion)


def test_formula_cambia_y_no_publica_html_de_usuario(monkeypatch):
    """La fórmula válida desaparece al editar y una entrada parcial no se interpreta como HTML."""
    async def comprobar(vista):
        """Espera la previa validada y contrasta sus nodos tras una edición incompleta."""
        vista.expresion.set_value("sqrt(x)+1")
        await vista.previa_expresion._tarea
        assert list(vista.previa_expresion.region.descendants())
        vista.expresion.set_value("x+")
        assert not list(vista.previa_expresion.region.descendants())
        await vista.vista_previa.tarea
        assert vista.vista_previa.respuesta["estado"] == "ERROR"
        assert vista.vista_previa.estado.text and vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("comprobar", [
    reglas.test_limites_tamanio_y_complejidad, reglas.test_docstrings_publicos,
    reglas.test_identificadores_idioma_y_ascii, reglas.test_comentarios_y_textos_limpios,
    reglas.test_reglas_python_frontend,
])
def test_modulos_afectados_cumplen_reglas(monkeypatch, comprobar):
    """Audita todos los módulos de producción cambiados sin editar manifiestos existentes."""
    rutas = tuple(RAIZ / "src/frontend" / ruta for ruta in _MODULOS)
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", rutas)
    comprobar()
