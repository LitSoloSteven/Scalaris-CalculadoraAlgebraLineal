"""Presentacion historica de eventos de reduccion para los consumidores de sistemas."""
from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import formatear_fraccion_texto


class RegistroPasosSistema:
    """Convierte eventos numericos en textos y copias defensivas para los controladores."""

    def __init__(self, reduccion_completa: bool) -> None:
        """Recibe el tipo de reduccion y crea una lista independiente de pasos."""
        self.reduccion_completa = reduccion_completa
        self.pasos: list[dict] = []

    def registrar(self, tipo: str, matriz: Matriz, datos: dict) -> None:
        """Registra evento y matriz como paso con descripcion; devuelve None."""
        descripcion = self._descripcion(tipo, datos)
        self.pasos.append({"descripcion": descripcion, "matriz": matriz.clonar()})

    def _descripcion(self, tipo: str, datos: dict) -> str:
        if tipo == "inicial":
            return "Matriz inicial aumentada [A|b]:"
        fila = datos["fila"] + 1
        if tipo == "intercambio":
            return f"Intercambio: Fila {fila} ↔ Fila {datos['seleccionada'] + 1}"
        if tipo == "eliminacion":
            factor = formatear_fraccion_texto(datos["factor"])
            return f"Fila {fila} = Fila {fila} − ({factor}) · Fila {datos['fila_pivote'] + 1}"
        if tipo == "normalizacion":
            prefijo = "Normalizar pivote a 1" if self.reduccion_completa else "Normalizar pivote"
            return f"{prefijo}: Fila {fila} = Fila {fila} / {formatear_fraccion_texto(datos['valor'])}"
        columna = datos["columna"] + 1
        descripcion = f"Pivote seleccionado en Fila {fila}, Columna {columna}"
        if not self.reduccion_completa:
            descripcion += f" (valor = {formatear_fraccion_texto(datos['valor'])})"
        return descripcion
