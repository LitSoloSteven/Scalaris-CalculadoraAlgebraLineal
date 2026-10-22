"""Auditoría de nombres accesibles en botones e interruptores de NiceGUI."""
from __future__ import annotations

import ast
from pathlib import Path
from tests.comun_recorrido_codigo import cadena_estatica, pares_padre_hijo


def _extraer_cadenas_propiedades(llamada: ast.Call) -> list[str]:
    """Extrae literales y partes estáticas de los argumentos de propiedades."""
    cadenas = []
    for argumento in llamada.args:
        contenido = cadena_estatica(argumento)
        if contenido is not None:
            cadenas.append(contenido)
    return cadenas


def _reunir_propiedades_encadenadas(nodo: ast.AST, padres: dict[ast.AST, ast.AST]) -> list[str]:
    """Recorre la cadena de llamadas y recoge las cadenas de propiedades."""
    actual = nodo
    propiedades = []
    while actual in padres:
        padre = padres[actual]
        if isinstance(padre, ast.Attribute) and padre.value == actual and padre.attr == "props":
            llamada = padres.get(padre)
            if isinstance(llamada, ast.Call):
                propiedades.extend(_extraer_cadenas_propiedades(llamada))
        actual = padre
    return propiedades


def buscar_infracciones_accesibilidad(arbol: ast.AST, ruta: str) -> list[tuple[str, str, int, str]]:
    """Encuentra controles de NiceGUI que carecen de nombre accesible."""
    padres = {hijo: padre for padre, hijo in pares_padre_hijo(arbol)}
    infracciones = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        infracciones.extend(_infracciones_boton(nodo, padres, ruta))
        infracciones.extend(_infracciones_interruptor(nodo, padres, ruta))
    return infracciones


def _es_control_ui(nodo, nombre):
    return (isinstance(nodo.func, ast.Attribute) and nodo.func.attr == nombre
            and isinstance(nodo.func.value, ast.Name) and nodo.func.value.id == "ui")


def _tiene_texto_posicional(nodo):
    return (len(nodo.args) > 0 and isinstance(nodo.args[0], ast.Constant)
            and isinstance(nodo.args[0].value, str))


def _infracciones_boton(nodo, padres, ruta):
    if _es_control_ui(nodo, "button"):
        tiene_icono = any(clave.arg == "icon" for clave in nodo.keywords)
        if tiene_icono and not _tiene_texto_posicional(nodo):
            propiedades = " ".join(_reunir_propiedades_encadenadas(nodo, padres))
            if "aria-label" not in propiedades:
                return [("BUTTON", ruta, nodo.lineno, propiedades)]
    return []


def _infracciones_interruptor(nodo, padres, ruta):
    if _es_control_ui(nodo, "switch"):
        tiene_nombre = any(clave.arg in ("aria_label", "aria-label") for clave in nodo.keywords)
        propiedades = " ".join(_reunir_propiedades_encadenadas(nodo, padres))
        if not _tiene_texto_posicional(nodo) and not tiene_nombre and "aria-label" not in propiedades:
            return [("SWITCH", ruta, nodo.lineno, propiedades)]
    return []


def test_botones_e_interruptores_con_nombre_accesible():
    """Audita todos los archivos en src/frontend para que no existan ui.button ni ui.switch sin accesibilidad."""
    carpeta_interfaz = Path(__file__).resolve().parent.parent / "src" / "frontend"
    infracciones = []
    for ruta in carpeta_interfaz.rglob("*.py"):
        codigo = ruta.read_text(encoding="utf-8")
        arbol = ast.parse(codigo, filename=str(ruta))
        infracciones.extend(buscar_infracciones_accesibilidad(arbol, ruta.as_posix()))
    if infracciones:
        lineas = [
            f"[{tipo}] {ruta}:{linea} (propiedades: '{propiedades}')"
            for tipo, ruta, linea, propiedades in infracciones
        ]
        informe = "\n".join(lineas)
        raise AssertionError(
            f"Se encontraron {len(infracciones)} elementos de interfaz sin aria-label ni texto:\n{informe}"
        )


def test_detector_identifica_controles_sin_nombre():
    """Verifica que el auditor detecte llamadas inválidas sintéticas."""
    codigo_invalido = '''
def build():
    btn = ui.button(icon="send").props("ripple=false")
    sw = ui.switch(value=True).props("dense size=sm")
'''
    arbol = ast.parse(codigo_invalido)
    infracciones = buscar_infracciones_accesibilidad(arbol, "synthetic.py")
    tipos = [infraccion[0] for infraccion in infracciones]
    assert "BUTTON" in tipos
    assert "SWITCH" in tipos
