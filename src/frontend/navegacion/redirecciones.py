"""Reglas de resolución y redirección para rutas heredadas (heredadas)."""
import urllib.parse

from src.frontend.navegacion.modelo import RedireccionHeredada


def _obtener_redirecciones_estaticas() -> list[RedireccionHeredada]:
    """Retorna las reglas fijas de redirección heredadas hacia las nuevas rutas."""
    return [
        RedireccionHeredada(ruta="/sistemas-lineales", ruta_destino="/algebra-lineal/sistemas"),
        RedireccionHeredada(
            ruta="/gauss",
            ruta_destino="/algebra-lineal/sistemas",
            consulta_fija=(("method", "gauss"),),
        ),
        RedireccionHeredada(
            ruta="/gauss-jordan",
            ruta_destino="/algebra-lineal/sistemas",
            consulta_fija=(("method", "gauss-jordan"),),
        ),
        RedireccionHeredada(ruta="/operaciones-matrices", ruta_destino="/algebra-lineal/matrices"),
        RedireccionHeredada(ruta="/matriz-inversa", ruta_destino="/algebra-lineal/inversa"),
        RedireccionHeredada(ruta="/vectores", ruta_destino="/algebra-lineal/vectores"),
        RedireccionHeredada(ruta="/conversor", ruta_destino="/utilidades/bases"),
        RedireccionHeredada(ruta="/romanos", ruta_destino="/utilidades/romanos"),
    ]


def redirecciones_heredadas() -> tuple[RedireccionHeredada, ...]:
    """Devuelve las redirecciones activas según el estado de la página de inicio."""
    import src.frontend.navegacion as modulo_navegacion

    inicio_activo = getattr(modulo_navegacion, "INICIO_HABILITADO", False)
    redirecciones: list[RedireccionHeredada] = []

    if not inicio_activo:
        redirecciones.append(
            RedireccionHeredada(
                ruta="/",
                ruta_destino="/algebra-lineal/sistemas",
                permanente=False,
            )
        )
        redirecciones.append(
            RedireccionHeredada(
                ruta="/ia",
                ruta_destino="/algebra-lineal/sistemas",
                permanente=False,
            )
        )
    else:
        redirecciones.append(
            RedireccionHeredada(
                ruta="/ia",
                ruta_destino="/",
                consulta_fija=(("glosa", "1"),),
                permanente=True,
            )
        )

    redirecciones.extend(_obtener_redirecciones_estaticas())
    return tuple(redirecciones)


def ubicacion_redireccion(redireccion: RedireccionHeredada, elementos_entrantes: list[tuple[str, str]]) -> str:
    """Calcula la URL de destino final preservando parámetros de consulta no colisionantes."""
    pares_fijos: list[tuple[str, str]] = list(redireccion.consulta_fija)
    claves_fijas = {clave for clave, _ in pares_fijos}

    for clave, valor in elementos_entrantes:
        if clave not in claves_fijas:
            pares_fijos.append((clave, valor))

    if pares_fijos:
        consulta_codificada = urllib.parse.urlencode(pares_fijos)
        return f"{redireccion.ruta_destino}?{consulta_codificada}"
    return redireccion.ruta_destino
