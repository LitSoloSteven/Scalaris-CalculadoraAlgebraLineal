"""Contenedores adaptables y raíces de las vistas de interfaz."""
from pathlib import Path
from tests.comun import leer_css_completo


def test_estilos_consultas_por_contenedor():
    """Las raíces y disposiciones conservan sus reglas de contenedor."""
    contenido = leer_css_completo()
    assert ".view-root { container-type: inline-size; }" in contenido or ".view-root { container-type: inline-size" in contenido
    assert ".hub-root { container-type: inline-size; }" in contenido or ".hub-root { container-type: inline-size" in contenido
    cantidad = contenido.count("container-type: inline-size")
    assert cantidad == 3, f"Se esperaban tres declaraciones de contenedor, se encontraron {cantidad}"
    assert "@container" in contenido
    assert ".layout-split" in contenido
    assert ".layout-grid-2" in contenido
    cantidad_reservas = contenido.count("--fab-reserve:")
    assert cantidad_reservas >= 4, f"Se esperaban al menos cuatro reservas, se encontraron {cantidad_reservas}"
    assert "100vh" not in contenido, "Unidad de altura fija encontrada en los estilos"


def test_vistas_utilizan_disposicion_por_contenedor():
    """Las vistas usan raíz semántica y carecen de clases de puntos de corte retiradas."""
    vistas = [
        "src/frontend/vistas/linear_systems/view_linear_systems.py",
        "src/frontend/vistas/operaciones_vectores/vista_operaciones_vectores.py",
        "src/frontend/vistas/matrix_ops/view_matrix_ops.py",
        "src/frontend/vistas/inverse_ops/view_inverse_ops.py",
        "src/frontend/vistas/numeric_systems/view_numeric_systems.py",
        "src/frontend/vistas/numeric_systems/view_roman_calculator.py",
    ]
    for vista in vistas:
        ruta_vista = Path(vista)
        assert ruta_vista.exists()
        contenido = ruta_vista.read_text(encoding="utf-8")
        assert "lg:flex-row" not in contenido
        assert "lg:w-1/2" not in contenido
        assert "lg:flex-1" not in contenido
        assert "md:grid-cols-2" not in contenido
        assert "view-root" in contenido, f"Raíz de vista ausente en {vista}"


def test_hub_contiene_raiz_de_vista():
    """La vista del Hub conserva su raíz de contenedor."""
    ruta_hub = Path("src/frontend/vistas/hub/view_hub.py")
    assert ruta_hub.exists()
    contenido = ruta_hub.read_text(encoding="utf-8")
    assert "view-root" in contenido
