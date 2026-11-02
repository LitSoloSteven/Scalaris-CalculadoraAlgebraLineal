"""Presupuesto de reconexión durante capturas que ocupan el hilo del navegador."""
from src.frontend import aplicacion, constantes


def test_arranque_conserva_cliente_durante_el_plazo_de_captura(monkeypatch):
    """El servidor no elimina al cliente con el plazo breve predeterminado de NiceGUI."""
    configuracion = {}
    monkeypatch.setattr(aplicacion, 'inicializar_aplicacion', lambda: None)
    monkeypatch.setattr(aplicacion, 'resolver_secreto_almacenamiento', lambda entorno: 'prueba')
    monkeypatch.setattr(aplicacion.ui, 'run', lambda **opciones: configuracion.update(opciones))
    aplicacion.ejecutar()
    assert configuracion['reconnect_timeout'] >= constantes.PDF_PLAZO_CLIENTE_SEGUNDOS
    assert configuracion['reconnect_timeout'] <= constantes.PDF_PLAZO_CAPTURA_SEGUNDOS
