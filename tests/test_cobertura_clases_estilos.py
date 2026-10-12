"""Cobertura de clases semánticas usadas por componentes y vistas."""
from pathlib import Path
import re
from tests.comun import leer_css_completo
from tests.comun_estilos import extraer_clases_semanticas


def reunir_clases_semanticas_usadas() -> set[str]:
    """Recoge clases de navegación, Hub y Glosa de llamadas y fragmentos HTML."""
    clases_usadas = set()
    directorios = [Path("src/frontend/componentes"), Path("src/frontend/vistas")]
    patrones = [r'''(?:classes\(|class=)[fF]?['"]([^'"]+)['"]''',
                r'''class=['"]([^'"]+)['"]''']
    for directorio in directorios:
        for ruta in directorio.rglob("*.py"):
            contenido = ruta.read_text(encoding="utf-8")
            for patron in patrones:
                clases_usadas.update(extraer_clases_semanticas(contenido, patron))
    return clases_usadas


def reunir_clases_estilos_definidas() -> set[str]:
    """Recoge las clases declaradas en el conjunto completo de estilos."""
    contenido = leer_css_completo()
    return set(re.findall(r'\.([a-zA-Z0-9_-]+)', contenido))


def test_clases_semanticas_usadas_tienen_reglas():
    """Cada clase semántica usada en Python tiene una regla de estilo."""
    clases_usadas = reunir_clases_semanticas_usadas()
    assert len(clases_usadas) > 0, "No se encontraron clases semánticas usadas"
    clases_definidas = reunir_clases_estilos_definidas()
    huerfanas = sorted([clase for clase in clases_usadas if clase not in clases_definidas])
    assert huerfanas == [], f"Clases semánticas sin regla de estilo: {huerfanas}"
