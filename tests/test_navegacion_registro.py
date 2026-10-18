"""Taxonomía, rutas y referencias del registro de navegación."""
from src.frontend.componentes.iconos import icono_svg
from src.frontend.navegacion import (
    ORDEN_NAVEGACION_PLANA, PILARES, HERRAMIENTAS, ruta_navegacion, redirecciones_heredadas, pilar_de,
    herramienta_por_identificador, herramienta_por_ruta, herramientas_visibles,
)


def test_identificadores_y_rutas_unicos():
    """Pilares, herramientas y redirecciones tienen identificadores únicos."""
    identificadores_pilares = [pilar.identificador for pilar in PILARES]
    assert len(identificadores_pilares) == len(set(identificadores_pilares)), "Identificadores de pilares duplicados"
    identificadores_herramientas = [herramienta.identificador for herramienta in HERRAMIENTAS]
    assert len(identificadores_herramientas) == len(set(identificadores_herramientas)), "Identificadores de herramientas duplicados"
    rutas_herramientas = [herramienta.ruta for herramienta in HERRAMIENTAS]
    assert len(rutas_herramientas) == len(set(rutas_herramientas)), "Rutas canónicas duplicadas"
    rutas_anteriores = [redireccion.ruta for redireccion in redirecciones_heredadas()]
    assert len(rutas_anteriores) == len(set(rutas_anteriores)), "Rutas de redirección duplicadas"


def test_formato_de_rutas():
    """Las rutas son absolutas y carecen de barra final salvo la raíz."""
    for herramienta in HERRAMIENTAS:
        assert herramienta.ruta.startswith("/"), f"La ruta {herramienta.ruta} debe empezar con '/'"
        if herramienta.ruta != "/":
            assert not herramienta.ruta.endswith("/"), f"La ruta {herramienta.ruta} no debe terminar con '/'"
    for redireccion in redirecciones_heredadas():
        assert redireccion.ruta.startswith("/"), f"La ruta anterior {redireccion.ruta} debe empezar con '/'"
        if redireccion.ruta != "/":
            assert not redireccion.ruta.endswith("/"), f"La ruta anterior {redireccion.ruta} no debe terminar con '/'"
        assert redireccion.ruta_destino.startswith("/"), f"El destino {redireccion.ruta_destino} debe empezar con '/'"
        if redireccion.ruta_destino != "/":
            assert not redireccion.ruta_destino.endswith("/"), f"El destino {redireccion.ruta_destino} no debe terminar con '/'"


def test_redirecciones_sin_colision_con_rutas_actuales():
    """Las rutas anteriores no sustituyen ninguna ruta canónica actual."""
    rutas_actuales = {herramienta.ruta for herramienta in HERRAMIENTAS}
    rutas_anteriores = {redireccion.ruta for redireccion in redirecciones_heredadas()}
    coincidencias = rutas_actuales.intersection(rutas_anteriores)
    assert not coincidencias, f"Colisión entre rutas canónicas y anteriores: {coincidencias}"


def test_pilares_referenciados_existen():
    """Cada herramienta referencia un pilar registrado y resoluble."""
    pilares_por_identificador = {pilar.identificador: pilar for pilar in PILARES}
    for herramienta in HERRAMIENTAS:
        assert herramienta.identificador_pilar in pilares_por_identificador, f"La herramienta '{herramienta.identificador}' referencia un pilar inexistente '{herramienta.identificador_pilar}'"
        pilar_resuelto = pilar_de(herramienta.identificador)
        assert pilar_resuelto.identificador == herramienta.identificador_pilar


def test_herramientas_habilitadas_con_iconos():
    """Cada herramienta visible tiene un icono SVG no vacío."""
    for herramienta in herramientas_visibles():
        svg = icono_svg(herramienta.icono)
        assert isinstance(svg, str) and svg.strip().startswith("<svg"), (
            f"La herramienta '{herramienta.identificador}' con icono '{herramienta.icono}' no genera un SVG válido"
        )


def test_titulos_con_sufijo_oficial():
    """Los títulos de todas las páginas incluyen la marca oficial."""
    for herramienta in HERRAMIENTAS:
        assert herramienta.titulo_pagina.endswith("| Scalaris"), (
            f"El título de '{herramienta.identificador}' ('{herramienta.titulo_pagina}') carece de '| Scalaris'"
        )


def test_busqueda_por_ruta_normaliza_consulta_y_barra():
    """La búsqueda ignora consultas y barras finales, y rechaza rutas ajenas."""
    sistemas = herramienta_por_ruta("/algebra-lineal/sistemas/?method=gauss-jordan&x=1")
    assert sistemas is not None and sistemas.identificador == "sistemas"
    inversa = herramienta_por_ruta("/algebra-lineal/inversa/")
    assert inversa is not None and inversa.identificador == "inversa"
    assert herramienta_por_ruta("/ruta-completamente-inexistente") is None
    assert herramienta_por_ruta("/algebra-lineal/inexistente") is None


def test_visualizador_habilitado_y_visible():
    """El visualizador geométrico está habilitado y aparece entre herramientas."""
    visualizador = herramienta_por_identificador("visualizador")
    assert visualizador.habilitada, "El visualizador debe estar habilitado"
    identificadores_visibles = {herramienta.identificador for herramienta in herramientas_visibles()}
    assert "visualizador" in identificadores_visibles, "El visualizador debe figurar entre herramientas visibles"


def test_orden_cubre_todas_las_herramientas_visibles():
    """El orden plano contiene exactamente las herramientas habilitadas."""
    identificadores_visibles = {herramienta.identificador for herramienta in herramientas_visibles()}
    assert set(ORDEN_NAVEGACION_PLANA) == identificadores_visibles, (
        f"El orden {set(ORDEN_NAVEGACION_PLANA)} difiere de las herramientas visibles {identificadores_visibles}"
    )


def test_migas_de_pan_por_ruta():
    """Las rutas conocidas generan migas y las inexistentes devuelven vacío."""
    migas = ruta_navegacion("/algebra-lineal/inversa")
    assert migas == (("Álgebra lineal", None), ("Matriz inversa", "/algebra-lineal/inversa"))
    migas_consulta = ruta_navegacion("/algebra-lineal/sistemas?method=gauss")
    assert migas_consulta == (("Álgebra lineal", None), ("Sistemas de ecuaciones", "/algebra-lineal/sistemas"))
    migas_inexistentes = ruta_navegacion("/ruta/falsa/123")
    assert migas_inexistentes == ()
