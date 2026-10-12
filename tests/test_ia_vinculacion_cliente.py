import inspect
from src.ai.cliente_openrouter import ClienteOpenRouter

def test_peticiones_post_vinculacion():
    """La petición inyectable no se vincula accidentalmente a la instancia."""
    firma = inspect.signature(ClienteOpenRouter()._peticiones_post)
    primer_parametro = list(firma.parameters.keys())[0]
    assert primer_parametro == "url"
