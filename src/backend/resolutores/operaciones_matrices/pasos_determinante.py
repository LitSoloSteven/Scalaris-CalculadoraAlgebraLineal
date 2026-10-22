"""Traza exacta de eliminacion con instantaneas independientes de las matrices."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.formateadores import numero_a_latex, formatear_fraccion_texto

RELACION_LU = (
    "La eliminacion obtiene una triangular U. Es la base de PA = LU si se guardan "
    "los multiplicadores en L y la permutacion P; aqui solo se triangulariza, "
    "sin construir una factorizacion LU completa."
)


class RegistroPasosDeterminante:
    """Convierte eventos del reductor compartido en una traza matematica."""

    def __init__(self, estrategia_pivote: str = "parcial") -> None:
        """Inicializa textos compatibles y pasos estructurados por calculo."""
        self.pasos: list[str] = []
        self.traza: list[dict] = []
        self.estrategia_pivote = estrategia_pivote

    def registrar(self, tipo: str, matriz: Matriz, datos: dict) -> None:
        """Registra evento, coordenadas y copia defensiva de su estado matricial."""
        descripcion, explicacion = self._textos(tipo, datos)
        paso = {"tipo": tipo, "descripcion": descripcion, "explicacion": explicacion,
                "matriz": matriz.clonar(), "operacion": dict(datos)}
        self.pasos.append(descripcion)
        self.traza.append(paso)

    def _textos(self, tipo: str, datos: dict) -> tuple[str, str]:
        if tipo == "inicial":
            return "Matriz inicial A", RELACION_LU
        fila = datos["fila"] + 1
        if tipo == "intercambio":
            return (f"Intercambio de fila {fila} con fila {datos['seleccionada'] + 1}",
                    "Cada intercambio invierte el signo del determinante.")
        if tipo == "eliminacion":
            factor = formatear_fraccion_texto(datos["factor"])
            return (f"Fila {fila} = Fila {fila} - ({factor}) * Fila {datos['fila_pivote'] + 1}",
                    "Sumar un multiplo de otra fila conserva el determinante.")
        valor = formatear_fraccion_texto(datos["valor"])
        seleccion = ("Elegimos el mayor valor absoluto disponible en esta columna (pivoteo parcial)."
                     if self.estrategia_pivote == "parcial" else "Elegimos el primer valor no nulo disponible en esta columna.")
        return (f"Pivote en fila {fila}, columna {datos['columna'] + 1}: {valor}",
                seleccion)

    def cerrar(self, reduccion: dict, determinante: Fraction) -> None:
        """Anade U y el producto diagonal con signo, tambien en el caso singular."""
        triangular = reduccion["matriz_reducida"]
        intercambios = reduccion["intercambios"]
        diagonal = [triangular.obtener(indice, indice) for indice in range(triangular.filas)]
        producto = r" \cdot ".join(f"({numero_a_latex(valor)})" for valor in diagonal)
        valor = numero_a_latex(determinante)
        detalle = (rf"\det(A)=(-1)^s\prod_{{i=1}}^{{n}}u_{{ii}}"
                   rf"=(-1)^{{{intercambios}}}\left({producto}\right)={valor}")
        explicacion = f"Hay {intercambios} intercambios. "
        if determinante == 0:
            explicacion += "La diagonal de U contiene un cero; la matriz es singular."
        else:
            explicacion += "Multiplicamos la diagonal de U y aplicamos el signo de los intercambios."
        descripcion = f"Producto diagonal con signo: det(A) = {formatear_fraccion_texto(determinante)}"
        self.pasos.append(descripcion)
        self.traza.append({"tipo": "final", "descripcion": descripcion, "explicacion": explicacion,
                           "matriz": triangular.clonar(), "detalle_latex": detalle,
                           "diagonal": diagonal, "intercambios": intercambios})
