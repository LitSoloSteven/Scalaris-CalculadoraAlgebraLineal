"""Registro de regiones y armado de figuras a partir de imágenes verificadas."""
from io import BytesIO

from reportlab.platypus import Image, KeepTogether
from src.frontend import constantes as medidas, textos
from .estilos import parrafo
from .imagenes import ImagenValidada, validar_imagenes


def preparar_figuras(herramienta: str, resultado: dict, capturas: list) -> list[dict]:
    """Asocia PNG con títulos registrados; rechaza claves desconocidas mediante ValueError."""
    estados = textos.PDF_ESTADOS_POR_HERRAMIENTA.get(herramienta, {})
    if resultado.get('estado') not in estados:
        raise ValueError(textos.PDF_ERROR_OBSOLETO)
    registro = textos.PDF_REGIONES_POR_HERRAMIENTA[herramienta]
    imagenes = validar_imagenes(capturas, tuple(registro))
    por_clave = {imagen.clave: imagen for imagen in imagenes}
    obligatorias = textos.PDF_REGIONES_OBLIGATORIAS.get(herramienta, (f'{herramienta}-resumen',))
    if any(clave not in por_clave for clave in obligatorias):
        raise ValueError(textos.PDF_ERROR_IMAGEN)
    estado = estados[resultado['estado']]
    figuras = []
    for clave, (titulo, descripcion) in registro.items():
        if clave in por_clave:
            figuras.append({'titulo': titulo, 'descripcion': descripcion + textos.PDF_DESCRIPCION_ESTADO.format(estado=estado),
                            'imagen': por_clave[clave]})
    return figuras


def construir_figura(figura: dict, numero: int, estilos: dict, espacio: tuple) -> tuple[KeepTogether, bool]:
    """Escala sin deformar y mantiene cita, rótulos, imagen y nota juntos; avisa reducciones."""
    ancho_util, alto_util = espacio
    imagen: ImagenValidada = figura['imagen']
    descripcion = figura['descripcion']
    cita = descripcion[:1].lower() + descripcion[1:]
    bloques = [parrafo(textos.PDF_CITA.format(numero=numero, descripcion=cita), estilos['cuerpo']),
               parrafo(textos.PDF_FIGURA.format(numero=numero), estilos['nivel2']),
               parrafo(figura['titulo'], estilos['cursiva'])]
    nota = parrafo(descripcion, estilos['figura'], nota=True)
    aviso = parrafo(textos.PDF_AVISO_REDUCCION, estilos['figura'])
    alto_textos = sum(bloque.wrap(ancho_util, alto_util)[1] for bloque in (*bloques, nota, aviso))
    alto_maximo = alto_util - max(alto_textos, medidas.PDF_RESERVA_FIGURA_PUNTOS)
    escala_ancho = min(1, ancho_util / imagen.ancho)
    escala = min(escala_ancho, alto_maximo / imagen.alto)
    reducida = escala < escala_ancho
    bloques.append(Image(BytesIO(imagen.datos), width=imagen.ancho * escala,
                         height=imagen.alto * escala, hAlign='CENTER'))
    bloques.append(nota)
    if reducida:
        bloques.append(aviso)
    return KeepTogether(bloques), reducida
