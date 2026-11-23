"""Adaptación de métodos iterativos al contrato compartido de exportación PDF."""
from __future__ import annotations

from src.frontend.componentes.exportacion_pdf.montaje.integracion import (
    completar_exportacion,
    identificador_raiz,
)
from src.frontend.controladores.algebra.sistemas_lineales.resolucion.contexto_iterativos import (
    entrada_iterativa_actual,
)
from src.frontend.controladores.exportacion_pdf.documento.vigencia import EnlacePDF
from src.frontend.nucleo.textos.textos_metodos_iterativos import (
    NOMBRES_METODOS,
    PDF_ESTADOS_ITERATIVOS,
)


def entrada_documental_iterativa(vista) -> dict:
    """Devuelve la captura vigente formateada para la sección inicial del PDF."""
    captura = vista.captura.obtener()
    datos = {'metodo': NOMBRES_METODOS[vista.metodo]}
    if captura['modo'] == 'ecuaciones':
        lineas = [linea.strip() for linea in str(captura['ecuaciones']).splitlines() if linea.strip()]
        datos.update({'modo': 'Ecuaciones', 'ecuaciones': lineas or ['']})
    else:
        datos.update({
            'modo': 'Matriz',
            'matriz_a': captura['matriz_a'],
            'vector_b': captura['vector_b'],
            'nombres_variables': captura['variables'],
        })
    datos.update({
        'vector_inicial': captura['vector_inicial'],
        'tolerancia': captura['tolerancia'],
        'maximo_iteraciones': captura['maximo_iteraciones'],
    })
    return datos


def montar_exportacion_iterativa(vista, resultado: dict) -> None:
    """Monta el control PDF cuando el código del cálculo es exportable y vigente."""
    codigo = resultado.get('codigo')
    if codigo not in PDF_ESTADOS_ITERATIVOS:
        return
    contenedor = getattr(vista, 'contenedor_resultados', None)
    if contenedor is None or contenedor.is_deleted:
        return
    resultado_pdf = {**resultado, 'estado': codigo}

    def leer_estado() -> tuple:
        """Comprueba identidad contra el resultado publicado en la vista."""
        actual = resultado_pdf if getattr(vista, 'ultimo_resultado', None) is resultado else None
        return (
            contenedor,
            actual,
            getattr(vista, '_revision_captura', 0),
            getattr(vista, '_identificador_calculo', 0),
        )

    enlace = EnlacePDF(
        vista,
        lambda: entrada_iterativa_actual(vista),
        identificador_raiz(contenedor),
        leer_estado=leer_estado,
        leer_entrada_documental=lambda: entrada_documental_iterativa(vista),
    )
    completar_exportacion(vista, 'metodos_iterativos', resultado_pdf, enlace)
