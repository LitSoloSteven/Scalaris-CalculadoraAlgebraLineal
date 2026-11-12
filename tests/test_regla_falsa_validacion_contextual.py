"""Validación delegada al dominio con errores por campo y sin alterar contratos del cálculo."""
import pytest

from src.frontend.controladores.regla_falsa.validacion_contextual import errores_captura
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("clave,valor", [("expresion", "x+"), ("expresion", "x" * 513),
    ("expresion", "<script>alert(1)</script>"), ("extremo_izquierdo", "nan"),
    ("extremo_derecho", "1"), ("tolerancia", "0"), ("tolerancia", "1e-999"),
    ("limite_iteraciones", "3.2"), ("unidad_angular", "otra")])
def test_error_asociado_al_campo(clave, valor):
    """Cada error conserva el campo concreto y no requiere iterar para detectarlo."""
    errores = errores_captura(captura_regla_falsa(**{clave: valor}))
    assert errores.get(clave)


def test_extremos_invertidos_son_validos_y_no_se_modifica_captura():
    """Se respeta la normalización autorizada del dominio sin copiar la captura canónica."""
    captura = captura_regla_falsa(extremo_izquierdo="2", extremo_derecho="1")
    assert errores_captura(captura) == {}
    assert captura["extremo_izquierdo"] == "2"


def test_errores_nativos_revision_y_limpieza(monkeypatch):
    """Salir de un campo orienta, corregir retira error y limpiar retira las visitas previas."""
    async def comprobar(vista):
        """Verifica mensajes del control, foco solicitado y preservación del resultado de error."""
        vista.cargar_captura(captura_regla_falsa(tolerancia="nan"))
        vista.estados_entrada.revisar("tolerancia")
        assert vista.tolerancia.error and vista.expresion.error is None
        assert not vista.estados_entrada.validar()
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "ERROR" and not vista.historial
        vista.tolerancia.set_value("1e-6")
        assert vista.tolerancia.error is None
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
        vista.limpiar_todo()
        assert not vista.estados_entrada.revisados
        assert vista.expresion.error is None and vista.inferior.error is None
    ejecutar_escenario(monkeypatch, comprobar)
