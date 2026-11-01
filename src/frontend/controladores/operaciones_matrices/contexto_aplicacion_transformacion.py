"""Datos acotados y señales pedagógicas exclusivos de la aplicación Av."""
from src.ai.contexto import ContextoIA, sanear_cadena_usuario
from src.frontend.sugerencias import Senales, primera_celda_invalida

LIMITE_COMPONENTE_CONTEXTO = 32


def _componentes_contexto(componentes: list) -> list[str]:
    return [sanear_cadena_usuario(str(valor), LIMITE_COMPONENTE_CONTEXTO) for valor in componentes]


def describir_aplicacion(contexto: ContextoIA, captura: dict, resultado: dict | None) -> ContextoIA:
    """Completa el contexto con coordenadas y dimensiones comprobadas, sin deducir rango."""
    contexto.entrada.update(modo_transformacion=captura["modo_transformacion"],
                            tipo_objeto=captura["tipo_objeto"],
                            vector_original=_componentes_contexto(captura["vector_original"]))
    contexto.entrada.update(dimension_dominio=len(captura["vector_original"]),
                            dimension_codominio=len(captura["matriz_transformacion"]))
    if resultado:
        contexto.resultado = {clave: resultado[clave] for clave in (
            "estado", "dimension_dominio", "dimension_codominio", "verificacion")}
        contexto.resultado.update({clave: _componentes_contexto(resultado[clave]["exacta"])
                                  for clave in ("vector_original", "vector_transformado")})
    return contexto


def senales_aplicacion(captura: dict, resultado: dict | None) -> Senales:
    """Detecta entradas inválidas y sugiere Av sin atribuir propiedades del análisis."""
    matriz = captura["matriz_transformacion"]
    elementos = [(f"A[{fila + 1},{columna + 1}]", valor, (fila, columna))
                 for fila, valores in enumerate(matriz) for columna, valor in enumerate(valores)]
    elementos.extend((f"v[{indice + 1}]", valor, None)
                     for indice, valor in enumerate(captura["vector_original"]))
    banderas = {"aplicacion_rectangular"} if len(matriz) != len(matriz[0]) else set()
    estado = "aplicacion_exito" if resultado else "aplicacion_sin_resultado"
    return Senales("transformaciones", estado, frozenset(banderas), primera_celda_invalida(elementos))
