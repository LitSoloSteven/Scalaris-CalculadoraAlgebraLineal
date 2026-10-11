"""Barridos estáticos de estilos, fórmulas y accesibilidad de controles."""
import os
import re
import ast
import pytest

FRONTEND_DIR = 'src/frontend'
THEME_CSS_PATH = 'src/frontend/assets/css/theme.css'


def test_interfaz_sin_altura_estatica_pantalla():
    """Ningún archivo de la interfaz contiene altura estática de pantalla."""
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.css')):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for i, line in enumerate(fp, 1):
                    if '100vh' in line:
                        violations.append(f"{path}:{i} -> {line.strip()}")
    assert not violations, f"Se encontraron referencias a 100vh:\n" + "\n".join(violations)


def test_interfaz_sin_filtros_de_desenfoque():
    """La interfaz evita filtros de desenfoque fuera del splash."""
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f == 'splash.js':
                continue
            if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.css')):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for i, line in enumerate(fp, 1):
                    if 'backdrop-filter' in line or 'blur(' in line:
                        violations.append(f"{path}:{i} -> {line.strip()}")
    assert not violations, f"Se encontraron 'backdrop-filter' o 'blur(' fuera de splash.js:\n" + "\n".join(violations)


def test_css_sin_colores_literales_fuera_de_tokens():
    """Las hojas de estilos usan tokens para sus colores."""
    from tests.comun import ARCHIVOS_CSS
    color_re = re.compile(r'(#[0-9a-fA-F]{3,8}\b|rgba?\([^)]+\))')
    violations = []
    for archivo in ARCHIVOS_CSS:
        if archivo.name == "tokens.css":
            continue
        lineas = archivo.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lineas, 1):
            clean = line.split('/*')[0].strip()
            m = color_re.findall(clean)
            if m:
                violations.append(f"{archivo.name}:{i} -> {clean} (colores: {m})")

    assert not violations, f"Colores literales encontrados fuera de tokens.css:\n" + "\n".join(violations)


def test_interfaz_sin_capas_numericas_elevadas():
    """Las capas locales no superan diez y la capa modal usa su token."""
    violations = []
    z_re = re.compile(r'z-index\s*:\s*([0-9]+)', re.IGNORECASE)
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f == 'splash.js':
                continue
            if not (f.endswith('.py') or f.endswith('.js') or f.endswith('.css')):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                for i, line in enumerate(fp, 1):
                    m = z_re.search(line)
                    if m:
                        val = int(m.group(1))
                        # Las capas pequeñas corresponden a contextos locales de apilamiento.
                        if val > 10:
                            violations.append(f"{path}:{i} -> z-index: {val}")

    app_js_path = os.path.join(FRONTEND_DIR, 'assets', 'js', 'app.js')
    with open(app_js_path, 'r', encoding='utf-8') as fp:
        app_js = fp.read()
    assert "9999" not in app_js, "app.js aún contiene z-index 9999"
    assert "var(--z-modal)" in app_js, "app.js debe usar var(--z-modal)"

    assert not violations, f"z-index numéricos elevados no permitidos:\n" + "\n".join(violations)


def test_formulas_tienen_contenedor_desplazable():
    """Las fórmulas de vistas y componentes disponen de su contenedor."""
    target = chr(36) + chr(36)
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        if 'vistas' not in root and 'componentes' not in root:
            continue
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                content = fp.read()
            if target not in content:
                continue

            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if target in line:
                    window = '\n'.join(lines[max(0, i - 10):min(len(lines), i + 10)])
                    if 'math-scroll-container' not in window:
                        violations.append(f"{path}:{i} -> {line.strip()}")

    assert not violations, f"Fórmulas $$ fuera de math-scroll-container:\n" + "\n".join(violations)


def test_botones_icono_tienen_nombre_accesible():
    """Todo botón con icono y sin texto accesible tiene aria-label."""
    violations = []
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if not f.endswith('.py'):
                continue
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fp:
                src = fp.read()
            try:
                tree = ast.parse(src, filename=path)
            except Exception:
                continue

            lines = src.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    is_btn = False
                    if isinstance(node.func, ast.Attribute) and node.func.attr == 'button':
                        is_btn = True
                    if is_btn:
                        has_text = False
                        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str) and node.args[0].value.strip() != '':
                            has_text = True
                        has_icon = any(k.arg == 'icon' for k in node.keywords)
                        if not has_text and has_icon:
                            chunk = '\n'.join(lines[node.lineno - 1:node.end_lineno + 3])
                            if 'aria-label' not in chunk:
                                violations.append(f"{path}:{node.lineno} -> {chunk[:100]}")

    assert not violations, f"Botones de solo icono sin aria-label:\n" + "\n".join(violations)
