"""La caché de IA conserva la privacidad de clientes e historiales."""
from src.ai.cliente_openrouter import ClienteOpenRouter
from src.ai.respuestas import OpcionesConsulta
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_cache_separa_clientes_y_cambios_de_historial(monkeypatch):
    """Cada cliente e historial recibe la respuesta de su propia petición."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    peticiones = []

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        peticiones.append(json)
        return RespuestaSimulada(200, {
            "choices": [{"message": {"content": str(len(peticiones))}}],
        })

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    primer_cliente, segundo_cliente = ClienteOpenRouter(), ClienteOpenRouter()
    historial = [{"enviado": True, "texto": "Mi dato privado es alfa"}]
    primera = primer_cliente.preguntar("Explícalo", historial=historial, opciones=OpcionesConsulta(True))
    repetida = primer_cliente.preguntar("Explícalo", historial=historial, opciones=OpcionesConsulta(True))
    ajena = segundo_cliente.preguntar("Explícalo", historial=historial, opciones=OpcionesConsulta(True))
    modificada = primer_cliente.preguntar("Explícalo", historial=[{
        "enviado": True, "texto": "Mi dato privado es beta",
    }], opciones=OpcionesConsulta(True))
    assert primera.exito and ajena.exito and modificada.exito
    assert repetida.desde_cache and repetida.texto == primera.texto
    assert not ajena.desde_cache and ajena.texto != primera.texto
    assert not modificada.desde_cache and modificada.texto != primera.texto
    assert len(peticiones) == 3
    assert peticiones[0]["messages"] != peticiones[2]["messages"]
