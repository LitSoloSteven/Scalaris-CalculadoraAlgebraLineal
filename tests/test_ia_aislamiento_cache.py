"""La caché de IA conserva la privacidad de clientes e historiales."""
from src.ai.openrouter_ai import OpenRouterIA
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_cache_separa_clientes_y_cambios_de_historial(monkeypatch):
    """Cada cliente e historial recibe la respuesta de su propia petición."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    peticiones = []

    def responder(url, headers=None, json=None, timeout=None):
        peticiones.append(json)
        return RespuestaSimulada(200, {
            "choices": [{"message": {"content": str(len(peticiones))}}],
        })

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(responder))
    primer_cliente, segundo_cliente = OpenRouterIA(), OpenRouterIA()
    historial = [{"role": "user", "content": "Mi dato privado es alfa"}]
    primera = primer_cliente.ask("Explícalo", history=historial, cacheable=True)
    repetida = primer_cliente.ask("Explícalo", history=historial, cacheable=True)
    ajena = segundo_cliente.ask("Explícalo", history=historial, cacheable=True)
    modificada = primer_cliente.ask("Explícalo", history=[{
        "role": "user", "content": "Mi dato privado es beta",
    }], cacheable=True)
    assert primera.ok and ajena.ok and modificada.ok
    assert repetida.cached and repetida.text == primera.text
    assert not ajena.cached and ajena.text != primera.text
    assert not modificada.cached and modificada.text != primera.text
    assert len(peticiones) == 3
    assert peticiones[0]["messages"] != peticiones[2]["messages"]
