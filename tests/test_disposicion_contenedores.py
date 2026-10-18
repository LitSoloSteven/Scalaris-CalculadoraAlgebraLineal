"""Contenedores adaptables y raíces de las vistas de interfaz."""
from pathlib import Path
from tests.comun import leer_css_completo


def test_estilos_consultas_por_contenedor():
    """Las raíces y disposiciones conservan sus reglas de contenedor."""
    contenido = leer_css_completo()
    assert ".vista-raiz { container-type: inline-size; }" in contenido or ".vista-raiz { container-type: inline-size" in contenido
    assert ".inicio-raiz { container-type: inline-size; }" in contenido or ".inicio-raiz { container-type: inline-size" in contenido
    cantidad = contenido.count("container-type: inline-size")
    assert cantidad == 3, f"Se esperaban tres declaraciones de contenedor, se encontraron {cantidad}"
    assert "@container" in contenido
    assert ".disposicion-dividida" in contenido
    assert ".disposicion-cuadricula-dos" in contenido
    cantidad_reservas = contenido.count("--fab-reserve:")
    assert cantidad_reservas >= 4, f"Se esperaban al menos cuatro reservas, se encontraron {cantidad_reservas}"
    assert "100vh" not in contenido, "Unidad de altura fija encontrada en los estilos"


def test_vistas_utilizan_disposicion_por_contenedor():
    """Las vistas usan raíz semántica y carecen de clases de puntos de corte retiradas."""
    vistas = [
        "src/frontend/vistas/sistemas_lineales/vista_sistemas_lineales.py",
        "src/frontend/vistas/operaciones_vectores/vista_operaciones_vectores.py",
        "src/frontend/vistas/operaciones_matrices/vista_operaciones_matrices.py",
        "src/frontend/vistas/operaciones_inversas/vista_operaciones_inversas.py",
        "src/frontend/vistas/sistemas_numericos/vista_sistemas_numericos.py",
        "src/frontend/vistas/sistemas_numericos/vista_calculadora_romana.py",
    ]
    for vista in vistas:
        ruta_vista = Path(vista)
        assert ruta_vista.exists()
        contenido = ruta_vista.read_text(encoding="utf-8")
        assert "lg:flex-row" not in contenido
        assert "lg:w-1/2" not in contenido
        assert "lg:flex-1" not in contenido
        assert "md:grid-cols-2" not in contenido
        assert "vista-raiz" in contenido, f"Raíz de vista ausente en {vista}"


def test_inicio_contiene_raiz_de_vista():
    """La vista del inicio conserva su raíz de contenedor."""
    ruta_inicio = Path("src/frontend/vistas/inicio/vista_inicio.py")
    assert ruta_inicio.exists()
    contenido = ruta_inicio.read_text(encoding="utf-8")
    assert "vista-raiz" in contenido
