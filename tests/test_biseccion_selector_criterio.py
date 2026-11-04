"""Selector contextual, vigencia de parámetros activos y formato independiente."""
import pytest
from nicegui import run

from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("tipo,parametro,filas", [
    ("decimales", 2, 8), ("ancho", ".01", 8), ("relativo", "1", 7),
    ("residuo", ".1", 4), ("iteraciones", 3, 3),
])
def test_cinco_criterios_desde_controles_reales(monkeypatch, tipo, parametro, filas):
    """Solo se muestra el parámetro activo y su resolución produce el número esperado de filas."""
    async def comprobar(vista):
        """Carga, resuelve y contrasta los valores visibles con los publicados por el motor."""
        vista.cargar_captura(captura_criterio(tipo, parametro))
        visibles = [nombre for nombre, campo in vista.parametros_criterio.items()
                    if campo.parent_slot.parent.visible]
        assert visibles == [tipo]
        await vista.resolver()
        assert len(vista.ultimo_resultado["iteraciones"]) == filas
        assert vista.ultimo_resultado["criterio_solicitado"]["tipo"] == tipo
        assert vista.reproductor_pasos is not None
    ejecutar_escenario(monkeypatch, comprobar)


def test_estimacion_y_condicion_aparecen_antes_de_calcular(monkeypatch):
    """La consulta geométrica no necesita ejecutar el motor ni publica un resultado."""
    async def comprobar(vista):
        """Comprueba ancho, residuo y número fijo en la guía reactiva."""
        vista.cargar_captura(captura_criterio("ancho", ".01"))
        assert "Filas previstas: 8" in vista.estimacion.text
        assert "b − a < 0.01" in vista.tolerancia.text
        assert vista.ultimo_resultado is None
        vista.criterio.set_value("residuo")
        assert "Sin estimación general" in vista.estimacion.text
        vista.criterio.set_value("iteraciones")
        assert "Filas previstas: 10" in vista.estimacion.text
    ejecutar_escenario(monkeypatch, comprobar)


def test_parametro_oculto_antes_activo_no_invalida_resultado(monkeypatch):
    """Los listeners del cálculo previo no convierten una edición oculta en cambio matemático."""
    async def comprobar(vista):
        """Alterna criterios y edita un d oculto después de resolver con ambos."""
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        vista.criterio.set_value("relativo")
        await vista.resolver()
        resultado, revision = vista.ultimo_resultado, vista._revision_captura
        vista.decimales.set_value(None)
        assert vista.ultimo_resultado is resultado
        assert vista._revision_captura == revision
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
    ejecutar_escenario(monkeypatch, comprobar)


def test_formato_actualiza_resumen_sin_reiniciar_resultado(monkeypatch):
    """La preferencia visual conserva la huella, el cálculo y el reproductor vigentes."""
    async def comprobar(vista):
        """Cambia precisión visual y comprueba el nuevo texto sobre la misma aproximación."""
        vista.cargar_captura(captura_criterio())
        await vista.resolver()
        resultado, reproductor = vista.ultimo_resultado, vista.reproductor_pasos
        revision, huella = vista._revision_captura, vista._huella_resultado
        vista.formato.set_value(9)
        textos = [getattr(hijo, "text", "") for hijo in vista.detalle_resumen.default_slot.children]
        assert f"x ≈ {resultado['aproximacion']:.9f}" in textos
        assert vista.ultimo_resultado is resultado
        assert vista.reproductor_pasos is reproductor
        assert (vista._revision_captura, vista._huella_resultado) == (revision, huella)
    ejecutar_escenario(monkeypatch, comprobar)


def test_parametro_activo_invalido_limpia_el_resultado(monkeypatch):
    """Una tolerancia no finita activa sí invalida y genera una respuesta de error controlada."""
    async def comprobar(vista):
        """Contrasta el comportamiento de una edición matemática con la de un campo oculto."""
        vista.cargar_captura(captura_criterio("relativo", "1"))
        await vista.resolver()
        vista.parametros_criterio["relativo"].set_value("nan")
        assert vista.ultimo_resultado is None
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "ERROR"
        assert "finita" in vista.ultimo_resultado["mensaje"]
    ejecutar_escenario(monkeypatch, comprobar)


def test_cambio_de_criterio_durante_calculo_descarta_respuesta(monkeypatch):
    """Cambiar y restaurar el criterio mientras trabaja no revive una solicitud anterior."""
    async def comprobar(vista):
        """Simula una carrera sin temporizadores ni llamadas externas."""
        vista.cargar_captura(captura_criterio("relativo", "1"))
        async def trabajar(funcion, captura):
            """Devuelve la captura vieja tras una edición y restauración del criterio."""
            respuesta = funcion(captura)
            vista.criterio.set_value("residuo")
            vista.criterio.set_value("relativo")
            return respuesta
        monkeypatch.setattr(run, "io_bound", trabajar)
        await vista.resolver()
        assert vista.ultimo_resultado is None
        assert vista.obtener_contexto_ia().resultado is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_edicion_oculta_durante_calculo_permite_publicar(monkeypatch):
    """Un dato que no participa en el criterio activo no vuelve obsoleta la respuesta."""
    async def comprobar(vista):
        """Edita el campo decimal oculto durante una resolución relativa."""
        vista.cargar_captura(captura_criterio("relativo", "1"))
        async def trabajar(funcion, captura):
            """Conserva datos matemáticos y solo cambia una preferencia inactiva."""
            vista.decimales.set_value(None)
            return funcion(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
    ejecutar_escenario(monkeypatch, comprobar)
