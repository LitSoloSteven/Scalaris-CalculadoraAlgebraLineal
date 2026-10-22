"""Catálogo declarativo puro de sugerencias contextuales y seguimientos."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Seguimiento:
    """Opción de profundización posterior en una respuesta de Glosa."""

    identificador: str
    etiqueta: str
    pregunta: str
    mas_simple: bool = False


SEGUIMIENTOS: tuple[Seguimiento, ...] = (
    Seguimiento("mas_simple", "Más simple", "Explícalo de forma más simple", True),
    Seguimiento("ejemplo", "Con un ejemplo numérico", "Dame un ejemplo numérico de eso"),
    Seguimiento("por_que", "¿Por qué funciona?", "¿Por qué funciona?"),
)

CATALOGO_SUGERENCIAS: tuple[tuple[str, str, str, str, str], ...] = (
    ("sistemas", "sin_resultado", "sistemas.sin_resultado.metodo", "¿Qué método uso, Gauss o Gauss-Jordan?", "estado"),
    ("sistemas", "sin_resultado", "sistemas.sin_resultado.fracciones", "¿Cómo escribo fracciones y decimales?", "estado"),
    ("sistemas", "unica", "sistemas.unica.comprobar", "¿Cómo compruebo la solución?", "estado"),
    ("sistemas", "unica", "sistemas.unica.geometria", "¿Qué significa geométricamente?", "estado"),
    ("sistemas", "infinita", "sistemas.infinita.porque", "¿Por qué tiene infinitas soluciones?", "estado"),
    ("sistemas", "infinita", "sistemas.infinita.libre", "¿Qué es una variable libre?", "estado"),
    ("sistemas", "infinita", "sistemas.infinita.parametrica", "¿Cómo leo la solución paramétrica?", "estado"),
    ("sistemas", "sin_solucion", "sistemas.sin_solucion.porque", "¿Por qué no tiene solución?", "estado"),
    ("sistemas", "sin_solucion", "sistemas.sin_solucion.matriz", "¿Cómo se ve una inconsistencia en la matriz?", "estado"),
    ("sistemas", "bandera_intercambio", "sistemas.bandera.intercambio", "¿Por qué se intercambiaron filas?", "bandera"),
    ("sistemas", "bandera_mas_ecuaciones_que_incognitas", "sistemas.bandera.mas_ecuaciones", "¿Qué cambia si hay más ecuaciones que incógnitas?", "bandera"),
    ("inversa", "sin_resultado", "inversa.sin_resultado.existe", "¿Cuándo existe la inversa?", "estado"),
    ("inversa", "exito", "inversa.exito.identidad", "¿Por qué la identidad queda a la izquierda?", "estado"),
    ("inversa", "exito", "inversa.exito.verificar", "¿Cómo verifico A·A⁻¹ = I?", "estado"),
    ("inversa", "exito", "inversa.exito.sistema", "¿Qué relación tiene con Ax = b?", "estado"),
    ("inversa", "singular", "inversa.singular.determinante", "¿Qué significa que el determinante sea cero?", "estado"),
    ("inversa", "singular", "inversa.singular.porque", "¿Por qué una matriz singular no tiene inversa?", "estado"),
    ("matrices", "vacio", "matrices.vacio.sintaxis", "¿Qué sintaxis acepto, por ejemplo 2A − B(C − Dᵀ)?", "estado"),
    ("matrices", "error_dimensiones", "matrices.dimensiones.porque", "¿Por qué no puedo operar estas dimensiones?", "estado"),
    ("matrices", "bandera_contiene_producto", "matrices.bandera.producto", "¿Por qué AB no es igual a BA?", "bandera"),
    ("vectores", "bandera_orientaciones_mixtas", "vectores.bandera.orientacion", "¿Qué pasa si uno es fila y el otro columna?", "bandera"),
    ("vectores", "bandera_escalar_negativo", "vectores.bandera.negativo", "¿Qué hace geométricamente un escalar negativo?", "bandera"),
    ("vectores", "unica", "vectores.combinacion_lineal.unica", "¿Cómo se relaciona con Ax = b?", "estado"),
    ("vectores", "infinita", "vectores.combinacion_lineal.infinita", "¿Por qué hay infinitas combinaciones?", "estado"),
    ("vectores", "infinita", "vectores.combinacion_lineal.dep", "¿Qué es dependencia lineal?", "estado"),
    ("vectores", "sin_solucion", "vectores.combinacion_lineal.espacio_generado", "¿Qué significa que b no esté en el span?", "estado"),
    ("bases", "bandera_division", "bases.division", "¿Por qué las divisiones se leen de abajo hacia arriba?", "estado"),
    ("bases", "bandera_hexadecimal", "bases.hexadecimal", "¿Por qué hex agrupa bits de 4 en 4?", "estado"),
    ("romanos", "bandera_error_resta_cero", "romanos.error.cero", "¿Por qué no existe el cero romano?", "estado"),
    ("romanos", "bandera_error_resta_negativa", "romanos.error.negativo", "¿Por qué no hay números negativos en romano?", "estado"),
    ("romanos", "bandera_error_sintaxis", "romanos.error.sintaxis", "¿Por qué IIII no es válido?", "estado"),
    ("romanos", "bandera_operacion_multiplicacion", "romanos.multiplicacion", "¿Por qué solo multiplico de un dígito?", "estado"),
    ("visualizador", "bandera_paralelas", "visualizador.paralelas", "¿Qué significa que las rectas sean paralelas?", "bandera"),
    ("visualizador", "resultado", "visualizador.espacio_generado", "¿Qué es el span de estos vectores?", "estado"),
)
