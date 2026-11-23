"""Contratos de último acceso, escenas de portada y registro en barras."""
import asyncio
from dataclasses import replace
from unittest.mock import Mock

from nicegui import Client, core, ui
import pytest

from src.frontend.componentes.aplicacion.controles.barra_navegacion import crear_barra_navegacion
from src.frontend.controladores.inicio import _recientes
from src.frontend.controladores.inicio._modelo import estado_portada
from src.frontend.controladores.inicio._recientes import (
    elegir_acceso_destacado,
    normalizar_accesos_recientes,
)
from src.frontend.navegacion import consultas, enlace_elemento_navegacion, ruta_de
from src.frontend.navegacion.secciones_inicio import secciones_inicio
from src.frontend.vistas.inicio._catalogo_ejemplos import CLAVES_EJEMPLOS, obtener_ejemplo
from src.frontend.vistas.inicio.panel_ejemplo import construir_html_ejemplo, renderizar_panel_ejemplo
from tests.comun_construccion_vistas import construir_pagina

_CLAVES_ESPERADAS = {
    acceso.clave
    for seccion in secciones_inicio()
    for grupo in seccion.grupos
    for acceso in grupo.accesos
}


def test_catalogo_ejemplos_cubre_exactamente_los_quince_accesos():
    """Todos los accesos del directorio tienen plantilla y metadatos propios."""
    assert CLAVES_EJEMPLOS == _CLAVES_ESPERADAS
    assert len(CLAVES_EJEMPLOS) == 17
    assert obtener_ejemplo("desconocida").clave == "sistemas"


@pytest.mark.parametrize(
    "acceso",
    [acceso for seccion in secciones_inicio() for grupo in seccion.grupos for acceso in grupo.accesos],
    ids=lambda acceso: acceso.clave,
)
def test_cada_acceso_sincroniza_titulo_enlace_y_ejemplo_unico(acceso):
    """Portada, enlace destacado y ejemplo coinciden e incluyen solo el caso activo."""
    estado = estado_portada([acceso.clave])
    assert estado.hay_historial is True
    assert estado.clave == acceso.clave
    assert estado.enlace == enlace_elemento_navegacion(acceso)
    assert estado.texto_destacado == f"Retomar {estado.titulo}"
    if acceso.clave == "vis:vectores":
        assert estado.titulo == "Vectores del Visualizador"
    fragmento = construir_html_ejemplo(estado)
    assert f'data-ejemplo-clave="{acceso.clave}"' in fragmento
    assert f'href="{estado.enlace}"' in fragmento
    assert estado.titulo in fragmento
    assert fragmento.count('class="inicio-ejemplo-etapa"') == 2
    assert "<template" not in fragmento
    assert "Ejemplo" in fragmento and "Reproducir" in fragmento and "Ver módulo" in fragmento


def test_normalizacion_resuelve_visualizador_heredado_alias_y_limite():
    """Visualizador heredado pasa a rectas-planos, consolida alias y respeta tope 4."""
    recientes = normalizar_accesos_recientes([
        "visualizador", "vis:rectas-planos", "biseccion", "regla_falsa", "bases", "romanos", "leontief",
    ])
    assert [acceso.clave for acceso in recientes] == [
        "vis:rectas-planos", "metodos_cerrados", "bases", "romanos",
    ]


@pytest.mark.parametrize(
    "historial",
    [None, "sistemas", 42, [], ["", "   ", "vis:inexistente", "desconocido", None, 99]],
)
def test_historial_vacio_o_corrupto_respalda_con_sistemas(historial):
    """La portada muestra Sistemas con acción inicial si faltan visitas válidas."""
    estado = estado_portada(historial)
    assert estado.clave == "sistemas"
    assert estado.enlace == "/algebra-lineal/sistemas"
    assert estado.texto_destacado == "Resolver un sistema"
    assert estado.hay_historial is False


def test_deshabilitar_visualizador_o_herramienta_omite_visitas_cerradas(monkeypatch):
    """Las entradas deshabilitadas en el catálogo o en el controlador se omiten."""
    catalogo = tuple(
        replace(herramienta, habilitada=False) if herramienta.identificador in {"visualizador", "sistemas"} else herramienta
        for herramienta in consultas.HERRAMIENTAS
    )
    monkeypatch.setattr(consultas, "HERRAMIENTAS", catalogo)
    acceso, hay_historial = elegir_acceso_destacado(["vis:vectores", "visualizador", "bases"])
    assert acceso.clave == "bases"
    assert hay_historial is True
    respaldo = estado_portada([])
    assert respaldo.clave == "leontief"
    assert respaldo.texto_destacado == "Abrir Modelo de Leontief"


def test_deshabilitar_por_controlador_omite_herramienta_reciente(monkeypatch):
    """Respeta la desactivación dinámica de herramienta_por_identificador."""
    real = _recientes.herramienta_por_identificador
    monkeypatch.setattr(
        _recientes,
        "herramienta_por_identificador",
        lambda identificador: replace(real(identificador), habilitada=False)
        if identificador == "inversa" else real(identificador),
    )
    acceso, hay_historial = elegir_acceso_destacado(["inversa", "romanos"])
    assert acceso.clave == "romanos"
    assert hay_historial is True


@pytest.mark.parametrize("contextual", ["0", "1"])
@pytest.mark.parametrize(
    "ruta,clave_activa,esperado",
    [
        ("/algebra-lineal/leontief", None, "leontief"),
        ("/utilidades/biseccion", None, "metodos_cerrados"),
        ("/visualizador", "vis:rectas-planos", "vis:rectas-planos"),
        ("/visualizador", "vis:vectores", "vis:vectores"),
        ("/visualizador", "vis:combinacion", "vis:combinacion"),
        ("/visualizador", "vis:invalida", "vis:rectas-planos"),
    ],
)
def test_barra_registra_herramientas_y_escenas_en_ambos_modos(
    monkeypatch, contextual, ruta, clave_activa, esperado
):
    """Tanto la barra plana como la contextual registran la clave validada al conectar."""
    monkeypatch.setenv("SCALARIS_NAV", contextual)
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-registro-reciente"))
    enviar = Mock()
    monkeypatch.setattr(cliente, "run_javascript", enviar)
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa=ruta, clave_activa=clave_activa)
        cliente.connect_handlers[0]()
        llamadas = [llamada.args[0] for llamada in enviar.call_args_list]
        assert any(f'registrar?.("{esperado}")' in codigo for codigo in llamadas)
        assert any("centrarActivo" in codigo for codigo in llamadas) == (contextual == "1")
    finally:
        cliente.delete()


def test_barra_no_registra_rutas_desconocidas(monkeypatch):
    """Una ruta fuera del catálogo no inserta registros falsos en el historial."""
    monkeypatch.setenv("SCALARIS_NAV", "0")
    monkeypatch.setattr(core, "script_mode", False)
    cliente = Client(ui.page("/prueba-registro-desconocida"))
    enviar = Mock()
    monkeypatch.setattr(cliente, "run_javascript", enviar)
    try:
        with cliente:
            crear_barra_navegacion(ruta_activa="/ruta-inexistente", clave_activa="sistemas")
        assert not cliente.connect_handlers
        enviar.assert_not_called()
    finally:
        cliente.delete()


@pytest.mark.parametrize(
    "clave,titulo_esperado,enlace_esperado",
    [
        ("vis:rectas-planos", "Rectas y planos", "/visualizador?escena=rectas-planos"),
        ("vis:vectores", "Vectores del Visualizador", "/visualizador?escena=vectores"),
        ("vis:combinacion", "Combinación lineal", "/visualizador?escena=combinacion"),
        ("sistemas", "Sistemas de ecuaciones", "/algebra-lineal/sistemas"),
    ],
)
def test_portada_actualiza_acceso_y_ejemplo_conservando_directorio(
    monkeypatch, clave, titulo_esperado, enlace_esperado
):
    """La portada actualiza destacado y ejemplo tras conectar sin reconstruir el menú."""
    emitidos = []

    async def comprobar(vista, cliente):
        """Comprueba que el vínculo, el panel y el directorio sigan consistentes."""
        destacado = vista._enlace_destacado
        assert destacado._props["href"] == enlace_esperado
        assert destacado._props["data-acceso-reciente"] == clave
        assert vista._texto_destacado.content == f"Retomar {titulo_esperado}"
        assert f'data-ejemplo-clave="{clave}"' in vista._panel_ejemplo.content
        assert f'href="{enlace_esperado}"' in vista._panel_ejemplo.content
        assert (clave == "sistemas") != any("ejemplosInicio?.preparar" in codigo for codigo in emitidos)
        directorio = next(elemento for elemento in cliente.elements.values() if "inicio-directorio" in elemento.classes)
        assert "data-directorio-listo" in directorio._props
        assert len([elemento for elemento in directorio.descendants() if "inicio-enlace" in elemento.classes]) == 17

    def _responder(codigo):
        emitidos.append(codigo)
        if "recientes?.leer" in codigo:
            return _RespuestaJS(valor={"valido": True, "identificadores": [clave]})
        return _RespuestaJS()

    _instalar_respuesta_js(monkeypatch, _responder)
    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


def test_portada_degrada_a_sistemas_ante_error_de_conexion_o_almacenamiento(monkeypatch):
    """Si falla la lectura o el cliente se cierra antes, permanece Sistemas sin errores."""
    _instalar_respuesta_js(
        monkeypatch,
        lambda codigo: _RespuestaJS(fallo=TimeoutError("Sin respuesta"))
        if "recientes?.leer" in codigo else _RespuestaJS(),
    )

    async def comprobar(vista, cliente):
        """Confirma que la portada conserva el respaldo de Sistemas."""
        assert vista._enlace_destacado._props["href"] == ruta_de("sistemas")
        assert vista._texto_destacado.content == "Resolver un sistema"
        assert 'data-ejemplo-clave="sistemas"' in vista._panel_ejemplo.content

    asyncio.run(construir_pagina(monkeypatch, "inicio", comprobar))


class _RespuestaJS:
    """Permite esperar respuestas síncronas simuladas sin dejar corrutinas pendientes."""

    def __init__(self, valor=None, fallo=None):
        self._valor = valor
        self._fallo = fallo

    def __await__(self):
        async def _responder():
            if self._fallo is not None:
                raise self._fallo
            return self._valor

        return _responder().__await__()


def test_normalizacion_acota_tamano_de_lista_y_longitud_clave():
    """El servidor rechaza claves mayores a 64 caracteres y descarta más allá de 16."""
    assert [acceso.clave for acceso in normalizar_accesos_recientes(["x" * 65, "leontief"])] == ["leontief"]
    assert normalizar_accesos_recientes(["desconocida"] * 16 + ["romanos"]) == ()
    with pytest.raises(ValueError, match="ruta interna"):
        renderizar_panel_ejemplo("https://externo.invalid", estado_portada(["leontief"]))


def test_portada_omite_cliente_eliminado_y_respuestas_no_estrictas(monkeypatch):
    """Cliente desconectado al conectar o respuesta no estricta conservan Sistemas."""
    llamadas = []

    async def _comprobar_no_estricto(vista, _cliente):
        assert vista._texto_destacado.content == "Resolver un sistema"
        assert not any("ejemplosInicio?.preparar" in codigo for codigo in llamadas)

    _instalar_respuesta_js(
        monkeypatch,
        lambda codigo: _RespuestaJS(valor={"valido": 1, "identificadores": ["romanos"]})
        if "recientes?.leer" in codigo else _RespuestaJS(),
    )
    asyncio.run(construir_pagina(monkeypatch, "inicio", _comprobar_no_estricto))

    async def _ejecutar_cliente_eliminado():
        from src.frontend.vistas.inicio.vista_inicio import VistaInicio
        import tests.comun_construccion_vistas as modulo_vistas

        cliente = Client(ui.page("/prueba-cliente-eliminado"))
        modulo_vistas.preparar_transporte(monkeypatch, cliente)

        async def _conectar(**opciones):
            cliente.delete()

        monkeypatch.setattr(cliente, "connected", _conectar)
        monkeypatch.setattr(cliente, "run_javascript", lambda codigo, **opciones: llamadas.append(codigo) or _RespuestaJS())
        vista = VistaInicio()
        try:
            with cliente:
                await vista.construir(cliente)
            assert vista._texto_destacado.content == "Resolver un sistema"
            assert not any("recientes?.leer" in codigo for codigo in llamadas)
        finally:
            if cliente.id in Client.instances:
                cliente.delete()

    asyncio.run(_ejecutar_cliente_eliminado())


def _instalar_respuesta_js(monkeypatch, resolver):
    """Sustituye el transporte del cliente por respuestas JS deterministas."""
    import tests.comun_construccion_vistas as modulo_vistas
    original = modulo_vistas.preparar_transporte

    def _preparar(parche, cliente):
        llamadas = original(parche, cliente)

        def _ejecutar(codigo, **opciones):
            llamadas.append(codigo)
            return resolver(codigo)

        parche.setattr(cliente, "run_javascript", _ejecutar)
        return llamadas

    monkeypatch.setattr(modulo_vistas, "preparar_transporte", _preparar)
