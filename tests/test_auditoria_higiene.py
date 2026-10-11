"""Contratos históricos de higiene y ausencia de alias de compatibilidad."""
import ast
from tests.comun import RAIZ
from tests.rutas_auditadas import RUTAS_AUDITADAS


def test_higiene_sin_scripts_residuales():
    """Los scripts de parcheo y su directorio de resultados permanecen ausentes."""
    archivos_residuales = [
        "check_dry_refactor.py", "replace_ls.py", "replace_romanos.py",
        "replace_script.py", "replace_vo.py",
    ]
    for nombre in archivos_residuales:
        ruta = RAIZ / nombre
        assert not ruta.exists(), f"Archivo residual encontrado en raiz: {nombre}"
    assert not (RAIZ / "regression_output").exists(), "Directorio regression_output presente."


def test_cero_alias_de_compatibilidad_historicos():
    """Los nombres retirados no reaparecen como asignaciones de compatibilidad."""
    nombres_alias_prohibidos = {
        "parsear_payload", "validar_y_construir_aumentada", "renderizar_estado_vacio",
    }
    for ruta in RUTAS_AUDITADAS:
        if ruta.suffix != ".py":
            continue
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Assign):
                for destino in nodo.targets:
                    if isinstance(destino, ast.Name):
                        assert destino.id not in nombres_alias_prohibidos, (
                            f"Alias prohibido '{destino.id}' detectado en {ruta.name}"
                        )
