"""Asociación del mensaje contextual con el campo de captura vigente."""
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


def test_error_contextual_enlaza_su_mensaje_hasta_corregir_el_campo(monkeypatch):
    """El destino existe en el campo y se desvincula al retirar el error."""
    async def comprobar(vista):
        """Inspecciona la ranura de error y corrige la expresión en el mismo control."""
        vista.cargar_captura(captura_regla_falsa(expresion="x+"))
        campo = vista.expresion
        assert not vista.estados_entrada.validar()
        mensaje, = campo.slots["error"].children
        assert campo.props["aria-describedby"] == mensaje.html_id
        assert campo.props["aria-invalid"] == "true"
        assert "error-message" not in campo.props
        assert mensaje.props["role"] == "alert" and mensaje.text == campo.error

        campo.set_value("x^2-2")
        assert vista.estados_entrada.validar()
        assert "aria-describedby" not in campo.props
        assert campo.props["aria-invalid"] == "false" and not mensaje.text

    ejecutar_escenario(monkeypatch, comprobar)


def test_cambio_de_criterio_retira_la_asociacion_del_parametro_oculto(monkeypatch):
    """El mensaje de un borrador inválido no queda asociado a un control oculto."""
    async def comprobar(vista):
        """Alterna de ancho a residuo con un error activo en el borrador de ancho."""
        vista.cargar_captura(captura_regla_falsa(criterio={"tipo": "ancho", "parametro": "0"}))
        ancho = vista.parametros_criterio["ancho"]
        vista.estados_entrada.revisar("criterio")
        assert ancho.props.get("aria-describedby")

        vista.criterio.set_value("residuo")
        assert "aria-describedby" not in ancho.props and ancho.error is None
        assert "aria-describedby" not in vista.tolerancia.props

    ejecutar_escenario(monkeypatch, comprobar)


def test_resultado_anuncia_su_estado_en_una_sola_region_viva(monkeypatch):
    """El título sigue disponible como encabezado y solo el estado persistente anuncia el cambio."""
    async def comprobar(vista):
        """Contrasta el título del detalle con el estado vivo de la captura."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        titulo = next(e for e in vista.contenedor_resultados if getattr(e, "text", None) == vista.estado.text)
        assert titulo.props["role"] == "heading" and titulo.props["aria-level"] == "3"
        assert "aria-live" not in titulo.props
        assert vista.estado.props["role"] == "status" and vista.estado.props["aria-live"] == "polite"

    ejecutar_escenario(monkeypatch, comprobar)
