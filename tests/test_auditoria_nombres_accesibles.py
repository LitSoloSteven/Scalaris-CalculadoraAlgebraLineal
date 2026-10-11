"""Auditoría estática AST de accesibilidad (a11y) para src/frontend.

Verifica:
1. ui.button con keyword `icon=` y sin texto posicional debe incluir 'aria-label' en sus .props(...).
2. ui.switch sin texto posicional debe incluir 'aria-label' (en props o keywords).
"""
from __future__ import annotations

import ast
from pathlib import Path


def _extraer_cadenas_propiedades(call_node: ast.Call) -> list[str]:
    """Extrae literales de cadena (estáticos o f-strings) de los argumentos de .props(...)."""
    res = []
    for a in call_node.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            res.append(a.value)
        elif isinstance(a, ast.JoinedStr):
            parts = []
            for val in a.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                else:
                    parts.append("")
            res.append("".join(parts))
    return res


def _reunir_propiedades_encadenadas(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> list[str]:
    """Sube por la cadena de llamadas (.classes(...).props(...).style(...)) recopilando strings de props."""
    curr = node
    props_str = []
    while curr in parent_map:
        parent = parent_map[curr]
        if isinstance(parent, ast.Attribute) and parent.value == curr and parent.attr == "props":
            call_parent = parent_map.get(parent)
            if isinstance(call_parent, ast.Call):
                props_str.extend(_extraer_cadenas_propiedades(call_parent))
        curr = parent
    return props_str


def buscar_infracciones_accesibilidad(tree: ast.AST, file_path_str: str) -> list[tuple[str, str, int, str]]:
    """Encuentra violaciones de accesibilidad en ui.button y ui.switch."""
    parent_map = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        violations.extend(_infracciones_boton(node, parent_map, file_path_str))
        violations.extend(_infracciones_interruptor(node, parent_map, file_path_str))

    return violations


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
    frontend_dir = Path(__file__).resolve().parent.parent / "src" / "frontend"
    all_violations = []

    for py_file in frontend_dir.rglob("*.py"):
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))
        violations = buscar_infracciones_accesibilidad(tree, py_file.as_posix())
        all_violations.extend(violations)

    if all_violations:
        lines = [
            f"[{kind}] {p}:{line} (props: '{props}')"
            for kind, p, line, props in all_violations
        ]
        report = "\n".join(lines)
        raise AssertionError(
            f"Se encontraron {len(all_violations)} elementos UI sin aria-label ni texto:\n{report}"
        )


def test_detector_identifica_controles_sin_nombre():
    """Verifica que el auditor detecte llamadas inválidas sintéticas."""
    bad_code = '''
def build():
    btn = ui.button(icon="send").props("ripple=false")
    sw = ui.switch(value=True).props("dense size=sm")
'''
    tree = ast.parse(bad_code)
    violations = buscar_infracciones_accesibilidad(tree, "synthetic.py")

    kinds = [v[0] for v in violations]
    assert "BUTTON" in kinds
    assert "SWITCH" in kinds
