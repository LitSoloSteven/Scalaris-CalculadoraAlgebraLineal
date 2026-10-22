"""Comprueba que Sistemas conserva el traspaso al Visualizador sin gráficos propios."""

from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
VISTAS_SISTEMAS = RAIZ / "src/frontend/vistas/sistemas_lineales"
EXTENSIONES_FUENTE = {".py", ".js", ".css", ".html"}


def test_no_existe_el_mixin_de_graficas():
    """Confirma que el módulo de gráficos redundante fue retirado."""
    assert not (VISTAS_SISTEMAS / "graphics_mixin.py").exists()


def test_frontend_no_contiene_la_grafica_de_sistemas():
    """Busca referencias al gráfico retirado en todos los archivos de la interfaz."""
    terminos = ("render_graphics", "Visualización Gráfica")
    for archivo in (RAIZ / "src/frontend").rglob("*"):
        if not archivo.is_file() or archivo.suffix not in EXTENSIONES_FUENTE:
            continue
        contenido = archivo.read_text(encoding="utf-8", errors="ignore")
        assert all(termino not in contenido for termino in terminos), str(archivo)


def test_resultados_conservan_el_boton_y_su_transferencia():
    """Verifica el botón existente, su condición, su tooltip y el traspaso de datos."""
    contenido = (VISTAS_SISTEMAS / "mixin_resolucion.py").read_text(encoding="utf-8")
    contenido += (RAIZ / 'src/backend/utilidades/estado_captura.py').read_text(encoding='utf-8')
    assert "if numero_variables in (2, 3):" in contenido
    assert "Ver en el Visualizador" in contenido
    assert "guardar_sistema('sistemas', coeficientes, independientes)" in contenido
    assert ".tooltip('Visualiza el sistema en R² o R³')" in contenido
