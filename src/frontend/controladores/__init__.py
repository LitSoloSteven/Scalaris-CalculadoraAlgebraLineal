"""Paquete de controladores para mediación entre interfaz y dominio matemático."""
from src.frontend.controladores.agrupador_pasos import agrupar_pasos_eliminacion
from src.frontend.controladores.clasificador_pasos import clasificar_paso
from src.frontend.controladores.geometria import (
    ControladorGeometria,
    selector_celda_error,
)
from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
    construir_foco_paso,
)
from src.frontend.controladores.operaciones_matrices import (
    CodificadorMatriz,
    ControladorDeterminante,
    ControladorLeontief,
    ControladorOperacionesMatrices,
    ControladorTransformaciones,
)
from src.frontend.controladores.operaciones_vectores import (
    ControladorOperacionesVectores,
    construir_vector_desde_dict,
)
from src.frontend.controladores.sistemas_lineales import (
    ControladorGauss,
    ControladorGaussJordan,
    construir_metadatos_pasos,
    validar_y_construir_aumentada,
)
from src.frontend.controladores.utilidades import (
    construir_vista_pasos,
    parsear_payload,
    serializar_matriz,
)

__all__ = [
    "CodificadorMatriz",
    "ControladorDeterminante",
    "ControladorGauss",
    "ControladorGaussJordan",
    "ControladorGeometria",
    "ControladorLeontief",
    "ControladorOperacionesInversas",
    "ControladorOperacionesMatrices",
    "ControladorOperacionesVectores",
    "ControladorTransformaciones",
    "agrupar_pasos_eliminacion",
    "clasificar_paso",
    "construir_foco_paso",
    "construir_metadatos_pasos",
    "construir_vector_desde_dict",
    "construir_vista_pasos",
    "parsear_payload",
    "selector_celda_error",
    "serializar_matriz",
    "validar_y_construir_aumentada",
]
