"""Regresiones de las tareas, la captura común y el contexto angular."""
from unittest.mock import AsyncMock

import pytest

from src.backend.resolutores.raices.contrato_biseccion import LIMITE_ITERACIONES_DEFECTO
from src.backend.resolutores.raices.unidades_angulares import funcion_sensible_a_unidad
from src.frontend.controladores.biseccion.exploracion import PASO_EXPLORACION_DEFECTO
from src.frontend.controladores.biseccion.vista_previa import RANGO_GRAFICA_DEFECTO
from src.frontend.vistas.biseccion.ejemplos import EJEMPLOS
from src.frontend.vistas.biseccion.modos_captura import MODO_BUSQUEDA, MODO_INTERVALO
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("nombre,sensible", [
    ("sin", True), ("tan", True), ("acos", True), ("atan", True),
    ("tanh", False), ("sqrt", False), ("desconocida", False),
])
def test_metadato_angular(nombre, sensible):
    """Distingue llamadas angulares de otras funciones y rechaza nombres sin texto."""
    assert funcion_sensible_a_unidad(nombre) is sensible
    with pytest.raises(ValueError, match="texto"):
        funcion_sensible_a_unidad(None)


def test_orientacion_de_entrada_y_unidad(monkeypatch):
    """La captura empieza vacía y conserva la unidad cuando deja de mostrarla."""
    async def comprobar(vista):
        """Recorre una expresión incompleta, una inversa y una hiperbólica."""
        assert vista.inferior.value == vista.superior.value == ""
        assert not vista.inferior._props.get("placeholder")
        assert vista.estado_expresion.text == "Escribe una función de x."
        assert "Completa ambos extremos" in vista.estado_continuidad.text
        assert not vista.estimacion.text
        vista.expresion.set_value("acos(")
        assert "Completa la función" in vista.estado_expresion.text
        salida = next(evento for evento in vista.expresion._event_listeners.values() if evento.type == "blur")
        salida.handler()
        assert "Sintaxis inválida" in vista.estado_expresion.text
        vista.expresion.set_value("acos(tanh(x))")
        assert vista.unidad_angular.visible
        vista.unidad_angular.set_value("grados")
        vista.expresion.set_value("tanh(x)")
        assert not vista.unidad_angular.visible
        vista.expresion.set_value("cos(x)")
        assert vista.unidad_angular.visible and vista.unidad_angular.value == "grados"
        vista.inferior.set_value("0")
        vista.superior.set_value("1")
        assert vista.estado_continuidad.text == "Continuidad no verificada."
    ejecutar_escenario(monkeypatch, comprobar)


def test_conmutar_tarea_conserva_datos_y_envia_solo_la_activa(monkeypatch):
    """Verifica el grupo de opciones y el envío contextual de la función común."""
    async def comprobar(vista):
        """Intercambia regiones con un resultado individual vigente."""
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        resultado, huella = vista.ultimo_resultado, vista._huella_resultado
        resolver, buscar = AsyncMock(), AsyncMock()
        monkeypatch.setattr(vista, "resolver", resolver)
        monkeypatch.setattr(vista.exploracion, "explorar", buscar)
        vista.modos.set_value(MODO_BUSQUEDA)
        assert vista.region_busqueda.visible and not vista.region_intervalo.visible
        assert vista.modos.botones[MODO_BUSQUEDA]._props["tabindex"] == "0"
        assert vista.modos.botones[MODO_INTERVALO]._props["tabindex"] == "-1"
        await vista.enviar_calculo()
        await vista._enviar_funcion()
        resolver.assert_not_awaited()
        buscar.assert_awaited_once()
        vista.modos.set_value(MODO_INTERVALO)
        assert vista.region_intervalo.visible and not vista.region_busqueda.visible
        assert vista.ultimo_resultado is resultado and vista._huella_resultado == huella
        await vista.exploracion.enviar_busqueda()
        await vista._enviar_funcion()
        resolver.assert_awaited_once()
        buscar.assert_awaited_once()
    ejecutar_escenario(monkeypatch, comprobar)


def test_ejemplos_y_limpieza_aplican_preferencias_explicitamente(monkeypatch):
    """El ejemplo reemplaza su configuración y el vaciado conserva preferencias."""
    async def comprobar(vista):
        """Carga un ejemplo y vacía el ejercicio desde la tarea de búsqueda."""
        vista.cargar_captura(captura_criterio("ancho", ".001") | {"unidad_angular": "grados"})
        vista.modos.set_value(MODO_BUSQUEDA)
        vista.cargar_captura(dict(EJEMPLOS["Básicos"])["Raíz de 2"])
        assert vista.modos.value == MODO_INTERVALO
        assert vista.criterio.value == "decimales" and vista.unidad_angular.value == "radianes"
        assert vista.limite.value == LIMITE_ITERACIONES_DEFECTO and not vista.historial
        vista.cargar_captura(captura_criterio("ancho", ".02"))
        vista.exploracion.minimo.set_value("-4")
        vista.exploracion.paso.set_value(".25")
        vista.vista_previa.maximo.set_value("20")
        vista.modos.set_value(MODO_BUSQUEDA)
        vista.modo_examen = True
        vista.limpiar_todo()
        assert vista.modos.value == MODO_BUSQUEDA and vista.modo_examen
        assert vista.esta_completamente_vacio()
        assert vista.criterio.value == "ancho" and vista.parametros_criterio["ancho"].value == ".02"
        assert vista.exploracion.minimo.value == ""
        assert vista.exploracion.paso.value == PASO_EXPLORACION_DEFECTO
        assert vista.vista_previa.maximo.value == str(RANGO_GRAFICA_DEFECTO[1])
        assert vista.vista_previa.tarea is None and vista.exploracion.respuesta is None
    ejecutar_escenario(monkeypatch, comprobar)
