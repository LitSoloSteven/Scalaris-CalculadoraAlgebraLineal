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
    ("determinantes", "sin_resultado", "determinantes.sin_resultado.metodo", "¿Cuándo conviene usar cofactores y cuándo eliminación?", "estado"),
    ("determinantes", "exito", "determinantes.exito.inversa", "¿Qué relación tiene este determinante con la inversa?", "estado"),
    ("determinantes", "singular", "determinantes.singular.cero", "¿Qué significa que det(A) sea cero?", "estado"),
    ("determinantes", "bandera_laplace", "determinantes.laplace.fila", "¿Por qué elegimos esa fila para expandir?", "bandera"),
    ("determinantes", "bandera_lu", "determinantes.lu.diagonal", "¿Por qué multiplicamos la diagonal tras triangularizar?", "bandera"),
    ("determinantes", "bandera_intercambio", "determinantes.intercambio.signo", "¿Por qué los intercambios cambian el signo?", "bandera"),
    ("leontief", "sin_resultado", "leontief.sin_resultado.modelo", "¿Qué representan C, d y x en este modelo?", "estado"),
    ("leontief", "exito", "leontief.exito.balance", "¿Cómo compruebo el balance de cada sector?", "estado"),
    ("leontief", "singular", "leontief.singular.modelo", "¿Qué significa que I − C sea singular?", "estado"),
    ("leontief", "bandera_no_viable", "leontief.no_viable.criterio", "¿Qué indica Hawkins-Simon sobre la viabilidad económica?", "bandera"),
    ("transformaciones", "sin_resultado", "transformaciones.sin_resultado.dimensiones", "¿Qué representan el dominio y el codominio?", "estado"),
    ("transformaciones", "aplicacion_sin_resultado", "transformaciones.aplicacion.entrada", "¿Cómo se relacionan las columnas de A con las coordenadas originales?", "estado"),
    ("transformaciones", "aplicacion_exito", "transformaciones.aplicacion.producto", "¿Cómo calcula cada fila de A una componente de Av?", "estado"),
    ("transformaciones", "aplicacion_exito", "transformaciones.aplicacion.comprobacion", "¿Qué comprueba exactamente la igualdad Av = y?", "estado"),
    ("transformaciones", "bandera_aplicacion_rectangular", "transformaciones.aplicacion.rectangular", "¿Por qué las coordenadas originales y transformadas tienen distintas dimensiones?", "bandera"),
    ("transformaciones", "exito", "transformaciones.exito.pivotes", "¿Cómo determinan los pivotes la imagen?", "estado"),
    ("transformaciones", "exito", "transformaciones.exito.dimension", "¿Por qué rango más nulidad es la dimensión del dominio?", "estado"),
    ("transformaciones", "bandera_nucleo_no_trivial", "transformaciones.nucleo.base", "¿Qué significa que el núcleo tenga vectores no nulos?", "bandera"),
    ("transformaciones", "bandera_rectangular", "transformaciones.rectangular.propiedades", "¿Cómo cambian inyectividad y sobreyectividad en una matriz rectangular?", "bandera"),
    ("factorizacion_lu", "sin_resultado", "lu.sin_resultado.convencion", "¿Qué significa PA = LU?", "estado"),
    ("factorizacion_lu", "exito", "lu.exito.multiplicadores", "¿Cómo leo los multiplicadores de L?", "estado"),
    ("factorizacion_lu", "exito", "lu.exito.verificacion", "¿Cómo verifico que LU = PA?", "estado"),
    ("factorizacion_lu", "bandera_intercambio", "lu.bandera.intercambio", "¿Por qué se intercambiaron filas y qué hace P?", "bandera"),
    ("factorizacion_lu", "bandera_rectangular", "lu.bandera.rectangular", "¿Se puede factorizar una matriz que no es cuadrada?", "bandera"),
    ("factorizacion_lu", "bandera_rango_deficiente", "lu.bandera.rango", "¿Por qué puedo factorizar una matriz singular?", "bandera"),
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
