"""Interfaz del contexto pedagógico y serialización segura para Glosa."""
from src.ai.constantes import MAXIMO_CARACTERES_CONTEXTO
from src.ai.datos_contexto import CapturaPaso, ContextoIA, EstadoContexto, ReferenciaPaso
from src.ai.estrategias_recorte import construir_contexto_minimo, ejecutar_cascada_recortes
from src.ai.matrices_contexto import describir_matriz, extraer_filas, generar_nota_ventana
from src.ai.texto_contexto import compactar_numero, recortar_texto, sanear_cadena_usuario


def serializar_contexto(
    contexto: ContextoIA, *, maximo_caracteres: int = MAXIMO_CARACTERES_CONTEXTO,
) -> str:
    """Serializa un bloque delimitado y usa contexto mínimo ante datos defectuosos."""
    try:
        return ejecutar_cascada_recortes(contexto, maximo_caracteres=maximo_caracteres)
    except Exception:
        herramienta = getattr(contexto, "herramienta", "")
        vista = getattr(contexto, "vista", "")
        return construir_contexto_minimo(herramienta, vista, maximo_caracteres)
