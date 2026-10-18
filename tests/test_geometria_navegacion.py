"""Integración del visualizador en el registro de navegación."""
from src.frontend.navegacion import (
    grupos_navegacion,
    ruta_de,
    ruta_navegacion,
    herramienta_por_identificador,
    herramientas_visibles,
    HERRAMIENTAS,
    ORDEN_NAVEGACION_PLANA,
)
from src.frontend.controladores.inicio._recientes import normalizar_recientes


def test_visualizador_presente_en_grupos_navegacion():
    """El visualizador aparece entre los grupos de navegación."""
    identificadores_herramientas = set()
    for pilar, herramientas in grupos_navegacion():
        for herramienta in herramientas:
            identificadores_herramientas.add(herramienta.identificador)
    assert "visualizador" in identificadores_herramientas


def test_ruta_visualizador():
    """El registro devuelve la ruta del visualizador."""
    assert ruta_de("visualizador") == "/visualizador"


def test_visualizador_migas_navegacion():
    """La miga del visualizador conserva su nombre y área."""
    migas = ruta_navegacion("/visualizador")
    assert len(migas) == 2
    assert migas[0][0] == "Visualizador geométrico"
    assert migas[1][0] == "Rectas, planos y vectores"
    assert migas[1][1] == "/visualizador"


def test_historial_reciente_admite_visualizador():
    """El normalizador acepta el identificador del visualizador."""
    resultado = normalizar_recientes(["visualizador", "sistemas", "bases"])
    identificadores_herramientas = [t.identificador for t in resultado]
    assert "visualizador" in identificadores_herramientas


def test_registro_conserva_rutas_unicas():
    """Las rutas del registro no se repiten."""
    rutas = [t.ruta for t in HERRAMIENTAS]
    assert len(rutas) == len(set(rutas))


def test_registro_conserva_identificadores_unicos():
    """Los identificadores del registro no se repiten."""
    identificadores = [t.identificador for t in HERRAMIENTAS]
    assert len(identificadores) == len(set(identificadores))


def test_orden_navegacion_incluye_visualizador():
    """El orden de navegación incluye el visualizador."""
    assert "visualizador" in ORDEN_NAVEGACION_PLANA


def test_visualizador_habilitado():
    """La herramienta de visualización está habilitada."""
    vis = herramienta_por_identificador("visualizador")
    assert vis.habilitada
