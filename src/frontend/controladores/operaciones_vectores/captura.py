"""Adaptación de la captura vectorial al contrato de los resolutores existentes."""
import json

from src.backend.geometria.transferencia import preparar_vectores_visualizador
from .controlador_operaciones_vectores import ControladorOperacionesVectores


def capturar_vectores(vectores: dict, dimension: int) -> dict:
    """Devuelve orientación y celdas crudas; el dominio valida sus valores."""
    return {
        nombre: {"orientacion": vector["orientacion"],
                 "datos": [vector["celdas"].get(indice, "").strip() or "0" for indice in range(dimension)]}
        for nombre, vector in vectores.items()
    }


def resolver_captura(operacion: str, opciones: dict, vectores: dict) -> str:
    """Delega una operación capturada y devuelve su JSON sin modificar las entradas."""
    valores = list(vectores.values())
    if operacion == "suma_resta" and len(valores) == 2:
        carga = {"operacion": opciones["operacion"],
                 "vector_1": valores[0], "vector_2": valores[1], "estricto": opciones["estricto"]}
        return ControladorOperacionesVectores.procesar_suma_resta(json.dumps(carga))
    if operacion == "escalar" and len(valores) == 1:
        carga = {"escalar": opciones["escalar"], "vector": valores[0]}
        return ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(carga))
    if operacion == "combinacion_lineal" and opciones["objetivo"] in vectores:
        objetivo = opciones["objetivo"]
        carga = {"objetivo": vectores[objetivo], "vectores": [valor for nombre, valor in vectores.items() if nombre != objetivo]}
        return ControladorOperacionesVectores.procesar_combinacion_lineal(json.dumps(carga))
    return json.dumps({"estado": "ERROR", "mensaje": "No se encontraron los vectores necesarios para la operación."})


def preparar_transferencia(operacion: str, vectores: dict) -> tuple[list, str]:
    """Delega al dominio las restricciones de escena para la captura recibida."""
    return preparar_vectores_visualizador(operacion, vectores)
