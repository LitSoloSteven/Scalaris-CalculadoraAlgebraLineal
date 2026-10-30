"""Modelo del inicio, selección por historial y contrato del cliente."""
from pathlib import Path
from src.backend.utilidades.estado_captura import celdas_matriz
import pytest

from src.frontend.controladores.inicio._modelo import (
    SeleccionInicial,
    ModeloPilar,
    ModeloTarjeta,
    pilares_inicio,
    seleccion_inicial,
)


def test_estructura_areas_inicio():
    """Verifica que pilares_inicio devuelva 3 pilares con 5, 3 y 2 tarjetas respectivamente."""
    pilares = pilares_inicio()
    assert len(pilares) == 3
    assert all(isinstance(p, ModeloPilar) for p in pilares)

    p_algebra, p_vis, p_util = pilares

    assert p_algebra.identificador == "algebra"
    assert p_algebra.nombre_corto == "Álgebra lineal"
    assert len(p_algebra.tarjetas) == 6
    assert [t.clave for t in p_algebra.tarjetas] == ["sistemas", "vectores", "matrices", "inversa", "determinantes", "factorizacion_lu"]
    assert all(isinstance(t, ModeloTarjeta) for t in p_algebra.tarjetas)

    assert p_vis.identificador == "visualizador"
    assert p_vis.nombre_corto == "Visualizador"
    assert len(p_vis.tarjetas) == 3
    assert [t.clave for t in p_vis.tarjetas] == ["vis:rectas-planos", "vis:vectores", "vis:combinacion"]

    assert p_util.identificador == "utilidades"
    assert p_util.nombre_corto == "Utilidades"
    assert len(p_util.tarjetas) == 2
    assert [t.clave for t in p_util.tarjetas] == ["bases", "romanos"]


def test_celdas_identidad_segun_dimension():
    """Verifica que matrix_cells genere la matriz identidad n x n."""
    assert celdas_matriz(3) == (
        ("1", "0", "0"),
        ("0", "1", "0"),
        ("0", "0", "1"),
    )
    assert celdas_matriz(1) == (("1",),)
    assert celdas_matriz(2) == (
        ("1", "0"),
        ("0", "1"),
    )


def test_celdas_rechazan_dimension_invalida():
    """Verifica que matrix_cells rechace dimensiones menores a 1."""
    with pytest.raises(ValueError):
        celdas_matriz(0)
    with pytest.raises(ValueError):
        celdas_matriz(-1)


def test_seleccion_inicial_historial_vacio():
    """Verifica degradacion al estado vacio orientativo (Sistemas de ecuaciones)."""
    seleccion = seleccion_inicial([])
    assert isinstance(seleccion, SeleccionInicial)
    assert seleccion.identificador_pilar == "algebra"
    assert seleccion.clave_tarjeta == "sistemas"
    assert seleccion.hay_historial is False


def test_seleccion_inicial_historial_valido():
    """Verifica seleccion focal en base al primer elemento valido del historial."""
    seleccion = seleccion_inicial(["romanos", "inversa"])
    assert seleccion.identificador_pilar == "utilidades"
    assert seleccion.clave_tarjeta == "romanos"
    assert seleccion.hay_historial is True


def test_seleccion_inicial_visualizador():
    """Verifica que una herramienta de visualizador active el pilar y la escena predeterminada."""
    seleccion = seleccion_inicial(["visualizador"])
    assert seleccion.identificador_pilar == "visualizador"
    assert seleccion.clave_tarjeta == "vis:rectas-planos"
    assert seleccion.hay_historial is True


@pytest.mark.parametrize(
    'historial, pilar_esperado, tarjeta_esperada',
    [
        (["romanos", "inversa"], "utilidades", "romanos"),
        (["inversa", "sistemas"], "algebra", "inversa"),
        (["vectores"], "algebra", "vectores"),
        (["matrices"], "algebra", "matrices"),
        (["determinantes"], "algebra", "determinantes"),
        (["bases"], "utilidades", "bases"),
        (["visualizador"], "visualizador", "vis:rectas-planos"),
        (["visualizador", "romanos"], "visualizador", "vis:rectas-planos"),
        # Duplicados
        (["romanos", "romanos"], "utilidades", "romanos"),
        (["inversa", "inversa", "sistemas"], "algebra", "inversa"),
        # Mezcla de validos e invalidos (el primer valido manda)
        (["zzz", "romanos"], "utilidades", "romanos"),
        ([None, 123, "zzz", "visualizador"], "visualizador", "vis:rectas-planos"),
        (["desconocido", None, "matrices", "inversa"], "algebra", "matrices"),
    ],
)
def test_seleccion_inicial_historiales_validos(historial, pilar_esperado, tarjeta_esperada):
    """Verifica seleccion correcta con historiales validos, duplicados y mezclas con invalidos."""
    seleccion = seleccion_inicial(historial)
    assert seleccion.identificador_pilar == pilar_esperado
    assert seleccion.clave_tarjeta == tarjeta_esperada
    assert seleccion.hay_historial is True


@pytest.mark.parametrize(
    'corrupto',
    [
        [],
        None,
        "x",
        "sistemas",
        42,
        {"a": 1},
        ["zzz"],
        ["inexistente_xyz"],
        [None],
        [None, 42, False],
        [{"a": 1}, ["x"]],
        ["invalido_1", "zzz"],
    ],
)
def test_seleccion_inicial_datos_corruptos(corrupto):
    """Verifica degradacion silenciosa ante datos corruptos, no lista, vacio o solo identificadores desconocidos."""
    seleccion = seleccion_inicial(corrupto)
    assert seleccion.identificador_pilar == "algebra"
    assert seleccion.clave_tarjeta == "sistemas"
    assert seleccion.hay_historial is False


def test_contrato_estatico_cliente_inicio():
    """Verifica el contrato de eventos delegados de la matriz y sus diálogos."""
    ruta_javascript = Path("src/frontend/recursos/js/inicio.js")
    assert ruta_javascript.exists()
    contenido = ruta_javascript.read_text(encoding="utf-8")

    assert "addEventListener('scroll'" not in contenido
    assert 'addEventListener("scroll"' not in contenido
    contenido_recientes = Path("src/frontend/recursos/js/inicio_recientes.js").read_text(encoding="utf-8")
    assert "window.scalaris.recientes =" in contenido_recientes
    assert "leer: leerRecientes" in contenido_recientes
    assert "registrar: registrarVisita" in contenido_recientes
    assert "window.scalarisHubSelect" not in contenido
    assert "function abrir(" in contenido
    assert "function cerrar(" in contenido
    assert "dialogo.showModal()" in contenido
    assert "evento.detail === 0" in contenido
    entrada = Path("src/frontend/recursos/js/inicio_entrada.js").read_text(encoding="utf-8")
    assert "data-inicio-pendiente" in entrada
    assert "presentacion.terminada.then(esperarContenido)" in entrada
    assert "hub-carousel" not in contenido
    assert "ResizeObserver" not in contenido
    assert "onPointerDown" not in contenido

    llamadas_foco = [llamada.split(")", 1)[0] for llamada in contenido.split(".focus(")[1:]]
    assert llamadas_foco
    assert all("preventScroll" in argumentos and "true" in argumentos for argumentos in llamadas_foco)
