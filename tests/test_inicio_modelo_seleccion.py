"""Proyección del directorio, preferencia destacada y contrato del cliente."""
from pathlib import Path
from src.backend.utilidades.estado_captura import celdas_matriz
import pytest

from src.frontend.controladores.inicio._modelo import acceso_destacado
from src.frontend.controladores.inicio._recientes import elegir_destacada
from src.frontend.navegacion import (
    ElementoNavegacion, Herramienta, pilar_de, predeterminado_elemento_clave, ruta_de,
)
from src.frontend.navegacion.secciones_inicio import SeccionInicio, secciones_inicio


def test_estructura_areas_inicio():
    """Las áreas del directorio conservan herramientas y escenas en orden de lectura."""
    secciones = secciones_inicio()
    assert len(secciones) == 5
    assert all(isinstance(seccion, SeccionInicio) for seccion in secciones)

    grupos = {
        seccion.identificador: tuple(acceso for grupo in seccion.grupos for acceso in grupo.accesos)
        for seccion in secciones
    }
    assert {identificador: [acceso.clave for acceso in accesos]
            for identificador, accesos in grupos.items()} == {
        "sistemas-lineales": ["sistemas", "leontief"],
        "matrices": ["matrices", "inversa", "determinantes", "factorizacion_lu"],
        "vectores-geometria": [
            "vectores", "transformaciones", "vis:rectas-planos", "vis:vectores", "vis:combinacion",
        ],
        "metodos-numericos": ["metodos_cerrados", "metodos_abiertos"],
        "sistemas-numeracion": ["bases", "romanos"],
    }
    assert all(isinstance(acceso, ElementoNavegacion) for accesos in grupos.values() for acceso in accesos)


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


def test_acceso_destacado_predeterminado():
    """Durante el montaje el acceso destacado ofrece Sistemas desde el catálogo."""
    acceso = acceso_destacado()
    assert isinstance(acceso, Herramienta)
    assert acceso.identificador == "sistemas"
    assert acceso.ruta == ruta_de("sistemas")
    herramienta, hay_historial = elegir_destacada([])
    assert herramienta == acceso
    assert hay_historial is False


def test_seleccion_inicial_historial_valido():
    """Verifica seleccion focal en base al primer elemento valido del historial."""
    herramienta, hay_historial = elegir_destacada(["romanos", "inversa"])
    assert pilar_de(herramienta.identificador).identificador == "utilidades"
    assert predeterminado_elemento_clave(herramienta.ruta) == "romanos"
    assert hay_historial is True


def test_seleccion_inicial_visualizador():
    """Verifica que una herramienta de visualizador active el pilar y la escena predeterminada."""
    herramienta, hay_historial = elegir_destacada(["visualizador"])
    assert pilar_de(herramienta.identificador).identificador == "visualizador"
    assert predeterminado_elemento_clave(herramienta.ruta) == "vis:rectas-planos"
    assert hay_historial is True


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
    herramienta, hay_historial = elegir_destacada(historial)
    assert pilar_de(herramienta.identificador).identificador == pilar_esperado
    assert predeterminado_elemento_clave(herramienta.ruta) == tarjeta_esperada
    assert hay_historial is True


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
    herramienta, hay_historial = elegir_destacada(corrupto)
    assert pilar_de(herramienta.identificador).identificador == "algebra"
    assert predeterminado_elemento_clave(herramienta.ruta) == "sistemas"
    assert hay_historial is False


def test_contrato_estatico_cliente_inicio():
    """El montaje conserva su API y el cliente delega el gesto sin apropiarse del foco."""
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
    assert "data-gesto-inicio" in contenido
    assert "showModal(" not in contenido
    assert ".focus(" not in contenido
    entrada = Path("src/frontend/recursos/js/inicio_entrada.js").read_text(encoding="utf-8")
    assert "data-inicio-pendiente" in entrada
    assert ".inicio-directorio[data-directorio-listo]" in entrada
    assert "presentacion.terminada.then(esperarContenido, esperarContenido)" in entrada
    assert "hub-carousel" not in contenido
    assert "ResizeObserver" not in contenido
    assert "onPointerDown" not in contenido
