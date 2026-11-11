"""Conversión estructural de candidatos exploratorios para los contratos de lote."""
from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion


def convertir_candidato(registro: dict) -> CandidatoResolucion:
    """Convierte un registro serializable; lanza ValueError si carece de intervalo o candidato."""
    if not isinstance(registro, dict) or not isinstance(registro.get("candidato"), dict):
        raise ValueError("El candidato no tiene la forma esperada.")
    datos = registro["candidato"]
    intervalo = datos.get("intervalo")
    if not isinstance(intervalo, (tuple, list)) or len(intervalo) != 2:
        raise ValueError("El candidato requiere dos extremos.")
    candidato = CandidatoExploracion(datos.get("tipo"), tuple(intervalo), datos.get("abscisa"), datos.get("valor"))
    return CandidatoResolucion(registro.get("identificador"), candidato)
