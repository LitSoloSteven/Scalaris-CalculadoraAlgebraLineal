"""Diagnóstico reproducible de límites del árbol completo de código auditado."""
import ast
import json

from tests.comun import RAIZ, analizar_fuentes_javascript
from tests.comun_auditoria import calcular_anidamiento_y_complejidad, nombres_parametros
from tests.rutas_auditadas import RUTAS_AUDITADAS
from tests.comun_javascript_embebido import fuentes_javascript

LIMITES_CODIGO = {"archivo": 300, "clase": 200, "lineas": 40,
                  "parametros": 5, "anidamiento": 3, "complejidad": 10}


def medir_limites():
    """Devuelve todas las infracciones ordenadas por exceso relativo al límite."""
    hallazgos = []
    for ruta in RUTAS_AUDITADAS:
        contenido = ruta.read_text(encoding="utf-8")
        ubicacion = (ruta.relative_to(RAIZ).as_posix(), ruta.name, 1)
        _registrar(hallazgos, ubicacion, "archivo", len(contenido.splitlines()))
        if ruta.suffix == ".py":
            _medir_python(contenido, ubicacion[0], hallazgos)
    medidas_javascript = analizar_fuentes_javascript(fuentes_javascript(RUTAS_AUDITADAS))
    for medida in medidas_javascript:
        _medir_javascript(medida, hallazgos)
    hallazgos.sort(key=lambda dato: (-dato["gravedad"], dato["ruta"], dato["linea"], dato["tipo"]))
    return hallazgos, medidas_javascript


def _medir_python(contenido, ruta, hallazgos):
    for nodo in ast.walk(ast.parse(contenido, filename=ruta)):
        if isinstance(nodo, ast.ClassDef):
            _registrar(hallazgos, (ruta, nodo.name, nodo.lineno),
                       "clase", nodo.end_lineno - nodo.lineno + 1)
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _medir_funcion_python(nodo, ruta, hallazgos)


def _medir_funcion_python(nodo, ruta, hallazgos):
    anidamiento, complejidad = calcular_anidamiento_y_complejidad(nodo)
    medidas = (("lineas", nodo.end_lineno - nodo.lineno + 1),
               ("parametros", len(nombres_parametros(nodo))),
               ("anidamiento", anidamiento), ("complejidad", complejidad))
    for tipo, valor in medidas:
        _registrar(hallazgos, (ruta, nodo.name, nodo.lineno), tipo, valor)


def _medir_javascript(medida, hallazgos):
    for clase in medida["clases"]:
        ubicacion = (medida["ruta"], clase["nombre"], medida["linea"] + clase["linea"] - 1)
        _registrar(hallazgos, ubicacion, "clase", clase["lineas"])
    for funcion in medida["funciones"]:
        ubicacion = (medida["ruta"], funcion["nombre"], medida["linea"] + funcion["linea"] - 1)
        for tipo in ("lineas", "parametros", "anidamiento", "complejidad"):
            _registrar(hallazgos, ubicacion, tipo, funcion[tipo])


def _registrar(hallazgos, ubicacion, tipo, valor):
    limite = LIMITES_CODIGO[tipo]
    if valor <= limite:
        return
    ruta, nombre, linea = ubicacion
    hallazgos.append({"ruta": ruta, "nombre": nombre, "linea": linea, "tipo": tipo,
                      "valor": valor, "limite": limite, "gravedad": round(valor / limite, 3)})


def guardar_diagnostico():
    """Regenera los dos JSON de diagnóstico en scratch sin modificar código."""
    hallazgos, medidas = medir_limites()
    for nombre, contenido in (("limites_pendientes.json", hallazgos), ("medidas_javascript.json", medidas)):
        ruta = RAIZ / "scratch" / nombre
        ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(hallazgos)


if __name__ == "__main__":
    guardar_diagnostico()
