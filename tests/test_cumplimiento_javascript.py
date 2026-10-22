"""Límites estructurales de JavaScript medidos con el parser incluido en Node."""
from tests.comun import analizar_fuentes_javascript
from tests.rutas_auditadas import RUTAS_AUDITADAS
from tests.comun_javascript_embebido import fuentes_javascript


def _analizar_archivos_javascript():
    return analizar_fuentes_javascript(fuentes_javascript(RUTAS_AUDITADAS))


def test_limites_funciones_y_clases_javascript():
    """Cada función, manejador y clase del manifiesto cumple los límites duros."""
    for archivo in _analizar_archivos_javascript():
        for clase in archivo["clases"]:
            assert clase["lineas"] <= 200, f"{archivo['ruta']}:{clase['nombre']} supera 200 líneas"
        for funcion in archivo["funciones"]:
            linea = archivo["linea"] + funcion["linea"] - 1
            ubicacion = f"{archivo['ruta']}:{funcion['nombre']}:{linea}"
            assert funcion["lineas"] <= 40, f"{ubicacion} tiene {funcion['lineas']} líneas"
            assert funcion["parametros"] <= 5, f"{ubicacion} tiene {funcion['parametros']} parámetros"
            assert funcion["anidamiento"] <= 3, f"{ubicacion} anidamiento {funcion['anidamiento']}"
            assert funcion["complejidad"] <= 10, f"{ubicacion} complejidad {funcion['complejidad']}"
