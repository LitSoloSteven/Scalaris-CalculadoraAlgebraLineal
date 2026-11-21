"""Recientes por método y preferencias visuales en la captura compartida."""
import asyncio

from nicegui import Client, core, ui

from src.frontend.componentes.resultados.acciones.copia_resultado import texto_resultado_copiable
from src.frontend.controladores.raices.biseccion.captura.catalogo_criterios import DECIMALES_PRESENTACION_DEFECTO
from src.frontend.controladores.raices.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA, resolver_presentacion
from src.frontend.vistas.raices.biseccion.resultados import resumen_criterio
from src.frontend.vistas.metodos_cerrados.acciones import AccionesMetodosCerrados
from src.frontend.vistas.regla_falsa import resultado
from tests.comun_construccion_vistas import cerrar_cliente
from tests.test_metodos_cerrados_calculo import captura_ejercicio, montar_vista


def test_recientes_conservan_cinco_capturas_por_metodo_y_restauran_sin_calcular(monkeypatch):
    """Activa el botón real y comprueba que entrega la captura independiente con su método."""
    async def _comprobar():
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/prueba-recientes-cerrados"))
        restauradas = []
        acciones = AccionesMetodosCerrados(restauradas.append)
        try:
            with cliente:
                acciones.construir()
                _llenar_historial(acciones)
                sin_cambio = {**_captura(BISECCION, 1), "expresion": "x^2 + 1"}
                acciones.registrar(sin_cambio, resolver_presentacion(sin_cambio)["resultado"])
                botones = [elemento for elemento in cliente.elements.values() if isinstance(elemento, ui.button)]
                assert len(botones) == 10
                assert all(not boton.text.startswith("x - 1 ·") for boton in botones)
                regla_falsa = botones[5]
                assert regla_falsa.text.startswith("x - 6 ·")
                evento = next(evento for evento in regla_falsa._event_listeners.values() if evento.type == "click")
                evento.handler(None)
                assert restauradas == [_captura(REGLA_FALSA, 6)]
        finally:
            await cerrar_cliente(cliente, [])
    asyncio.run(_comprobar())


def _llenar_historial(acciones):
    for metodo in (BISECCION, REGLA_FALSA):
        for indice in range(1, 7):
            captura = _captura(metodo, indice)
            datos = resolver_presentacion(captura)
            acciones.registrar(captura, datos["resultado"], datos.get("ampliado"))
            captura["criterio"]["parametro"] = "2"


def test_preferencias_visuales_tienen_valores_independientes_por_metodo_y_vista():
    """Un cambio de formato no altera otro método ni las preferencias de otro cliente."""
    acciones = AccionesMetodosCerrados(lambda captura: None)
    otra_vista = AccionesMetodosCerrados(lambda captura: None)
    acciones.fijar_precision(BISECCION, 3)
    acciones.fijar_examen(BISECCION, True)
    assert acciones.precision(BISECCION) == 3 and acciones.examen(BISECCION)
    assert acciones.precision(REGLA_FALSA) == DECIMALES_PRESENTACION_DEFECTO
    assert not acciones.examen(REGLA_FALSA)
    assert otra_vista.precision(BISECCION) == DECIMALES_PRESENTACION_DEFECTO
    assert not otra_vista.examen(BISECCION)


def test_reciente_cruzado_conserva_captura_examen_y_precision_sin_recalcular(monkeypatch):
    """Conecta los recientes y las preferencias con los resultados de ambos motores."""
    copias = []
    for modulo in (resumen_criterio, resultado):
        monkeypatch.setattr(modulo, "renderizar_copia_resultado", copias.append)

    async def _comprobar():
        async with montar_vista(monkeypatch) as (vista, cliente):
            capturas = {}
            for metodo, expresion in ((BISECCION, "x^2 - 2"), (REGLA_FALSA, "x^2 - 3")):
                vista.captura.metodo.set_value(metodo)
                vista.cargar_captura(captura_ejercicio(expresion, "1", "2", "radianes"))
                capturas[metodo] = vista.capturar()
                await vista.resolver()
                precision = 2 if metodo == BISECCION else 3
                _comprobar_copia(vista, copias, precision)
                assert vista.capturar() == capturas[metodo]

            boton = next(elemento for elemento in cliente.elements.values()
                         if isinstance(elemento, ui.button) and elemento.text.startswith("x^2 - 2 ·"))
            evento = next(evento for evento in boton._event_listeners.values() if evento.type == "click")
            evento.handler(None)
            assert vista.capturar() == capturas[BISECCION] and vista.ultimo_resultado is None
            await vista.resolver()
            assert vista.formato.value == 2 and vista.interruptor_examen.value

    asyncio.run(_comprobar())


def _comprobar_copia(vista, copias, precision):
    respuesta = vista.ultimo_resultado
    vista.salida.reproductor.ir_a(1)
    assert not vista.interruptor_examen.value
    vista.interruptor_examen.set_value(True)
    vista.formato.set_value(precision)
    copia = texto_resultado_copiable(copias[-1]())
    assert f"{respuesta['aproximacion']:.{precision}f}" in copia and "Modo examen" in copia
    assert vista.ultimo_resultado is respuesta and vista.salida.reproductor.indice_actual == 1


def _captura(metodo: str, indice: int) -> dict:
    criterio = {"tipo": "iteraciones", "parametro": "3"}
    return {"metodo": metodo, "expresion": f"x - {indice}", "unidad_angular": "grados",
            "extremo_izquierdo": str(indice), "extremo_derecho": str(indice + 1),
            "limite_iteraciones": "33", "criterio": criterio, "cero_preferido": indice}
