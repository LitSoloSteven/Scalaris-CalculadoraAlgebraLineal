"""Auditoría de las responsabilidades y límites del dominio y la integración ampliada."""
import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as reglas


_VISTAS_REGLA_FALSA = (
    "src/frontend/vistas/regla_falsa/__init__.py",
    "src/frontend/vistas/raices/regla_falsa/captura/acciones_captura.py",
    "src/frontend/vistas/raices/regla_falsa/captura/captura.py",
    "src/frontend/vistas/raices/regla_falsa/resultados/composicion.py",
    "src/frontend/vistas/raices/regla_falsa/exploracion/continuidad_intervalo.py",
    "src/frontend/vistas/raices/regla_falsa/resultados/detalle_resultado.py",
    "src/frontend/vistas/raices/regla_falsa/captura/ejemplos.py",
    "src/frontend/vistas/raices/regla_falsa/captura/estado_captura.py",
    "src/frontend/vistas/raices/regla_falsa/captura/estados_entrada.py",
    "src/frontend/vistas/raices/regla_falsa/exploracion/exploracion.py",
    "src/frontend/vistas/raices/regla_falsa/grafica/figura.py",
    "src/frontend/vistas/raices/regla_falsa/procedimiento/modo_examen.py",
    "src/frontend/vistas/raices/regla_falsa/base/modos_captura.py",
    "src/frontend/vistas/regla_falsa/pagina.py",
    "src/frontend/vistas/raices/regla_falsa/procedimiento/procedimiento.py",
    "src/frontend/vistas/raices/regla_falsa/grafica/rango_previo.py",
    "src/frontend/vistas/raices/regla_falsa/resultados/resolucion_multiple.py",
    "src/frontend/vistas/raices/regla_falsa/procedimiento/resultado.py",
    "src/frontend/vistas/raices/regla_falsa/resultados/resultados_multiples.py",
    "src/frontend/vistas/raices/regla_falsa/exploracion/seleccion_candidato.py",
    "src/frontend/vistas/raices/regla_falsa/grafica/seleccion_grafico.py",
    "src/frontend/vistas/raices/regla_falsa/base/selector_criterio.py",
    "src/frontend/vistas/raices/regla_falsa/base/sugerencias.py",
    "src/frontend/vistas/raices/regla_falsa/procedimiento/tabla_iteraciones.py",
    "src/frontend/vistas/raices/regla_falsa/base/vigencia_solicitud.py",
    "src/frontend/vistas/raices/regla_falsa/grafica/vista_previa.py",
    "src/frontend/vistas/regla_falsa/vista_regla_falsa.py",
)

@pytest.mark.parametrize("comprobar", [reglas.test_limites_tamanio_y_complejidad, reglas.test_docstrings_publicos,
    reglas.test_identificadores_idioma_y_ascii, reglas.test_comentarios_y_textos_limpios, reglas.test_reglas_python_frontend])
def test_modulos_ampliados_cumplen_reglas(monkeypatch, comprobar):
    """Audita todos los módulos ampliados con las reglas comunes sin cambiar sus manifiestos."""
    rutas = list((RAIZ / "src/backend/resolutores/raices").rglob("*regla_falsa*.py"))
    rutas.extend(RAIZ / ruta for ruta in (
        "src/frontend/controladores/raices/regla_falsa/__init__.py",
        "src/frontend/controladores/raices/regla_falsa/captura/captura.py",
        "src/frontend/controladores/raices/regla_falsa/captura/configuracion_ampliada.py",
        "src/frontend/controladores/raices/regla_falsa/procedimiento/contexto_regla_falsa.py",
        "src/frontend/controladores/raices/regla_falsa/captura/continuidad_intervalo.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/controlador.py",
        "src/frontend/controladores/raices/regla_falsa/presentacion/diagnostico.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/ejecucion_ampliada.py",
        "src/frontend/controladores/raices/regla_falsa/procedimiento/formulas_procedimiento.py",
        "src/frontend/controladores/raices/regla_falsa/procedimiento/pasos.py",
        "src/frontend/controladores/raices/regla_falsa/procedimiento/pasos_ampliados.py",
        "src/frontend/controladores/raices/regla_falsa/presentacion/presentacion.py",
        "src/frontend/controladores/raices/regla_falsa/presentacion/presentacion_ampliada.py",
        "src/frontend/controladores/raices/regla_falsa/presentacion/presentacion_examen.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/presentacion_grafica.py",
        "src/frontend/controladores/raices/regla_falsa/ejecucion/resolucion_multiple.py",
        "src/frontend/controladores/raices/regla_falsa/procedimiento/salidas_regla_falsa.py",
        "src/frontend/controladores/raices/regla_falsa/captura/serializacion.py",
        "src/frontend/controladores/raices/regla_falsa/presentacion/tabla.py",
        "src/frontend/controladores/raices/regla_falsa/captura/validacion_contextual.py",
    ))
    rutas.extend(RAIZ / ruta for ruta in _VISTAS_REGLA_FALSA)
    rutas.append(RAIZ / "src/backend/resolutores/raices/continuidad/analisis/sugerencias_dominio.py")
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", tuple(rutas))
    comprobar()
