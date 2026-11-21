"""Ejecuta una tarea de Scalaris con relevo por agotamiento de cuota."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import mkdtemp

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "relevos" / "automatizados"
CLIENTES = ("codex", "agy")
MODELO_CODEX = "gpt-6.2-sol"
MODELO_ANTIGRAVITY = "gemini-pro-orchestrator-neon"
LINEAS_DE_ESTADO = 30
PATRON_CUOTA = re.compile(
    r"usage[_ -]?limit[_ -]?(?:reached|exceeded)|"
    r"(?:hit|reach(?:ed)?|exceed(?:ed)?) (?:your |the )?(?:weekly |hourly )?usage limit|"
    r"quota(?: limit)? (?:is |has been )?(?:exhausted|exceeded|reached)|"
    r"(?:out of |no remaining |exhausted (?:your |the ))quota|"
    r"(?:exceeded|reached) (?:your |the )?quota",
    re.IGNORECASE,
)


def git(*argumentos: str) -> str:
    """Obtiene un resumen local de Git sin ejecutar herramientas de diff externas."""
    return subprocess.check_output(
        ["git", *argumentos], cwd=RAIZ, encoding="utf-8", errors="replace"
    ).strip()


def comando(cliente: str, esfuerzo: str, encargo: str) -> tuple[list[str], str]:
    """Fija el modelo y mantiene activas las protecciones del cliente."""
    ejecutable = shutil.which(cliente)
    if ejecutable is None:
        raise OSError(f"{cliente} no está disponible en PATH.")
    if cliente == "codex":
        argumentos = [
            ejecutable, "exec", "--json", "--color", "never", "--approve-for-me",
            "-m", MODELO_CODEX, "-c", 'service_tier="default"',
            "-c", f'model_reasoning_effort="{esfuerzo}"', "-",
        ]
        return argumentos, encargo
    return (
        [ejecutable, "--model", MODELO_ANTIGRAVITY, "--sandbox", "--mode", "auto",
         "--disable-slash-commands", "--input-format", "stream-json",
         "--output-format", "stream-json"],
        json.dumps({"event": "user", "message": {"content": encargo}}, ensure_ascii=False) + "\n",
    )


def examinar_respuesta(cliente: str, salida: Path, codigo: int) -> tuple[str, str]:
    """Clasifica solo errores del cliente y devuelve su mensaje final."""
    ultimo_mensaje = ""
    error = ""
    finalizado = False
    with salida.open(encoding="utf-8", errors="replace") as registro:
        for linea in registro:
            try:
                evento = json.loads(linea)
            except json.JSONDecodeError:
                continue
            if not isinstance(evento, dict):
                continue
            if cliente == "codex":
                if evento.get("type") in {"error", "turn.failed"}:
                    error = str(evento.get("error") or evento.get("message") or error)
                if evento.get("type") == "turn.completed":
                    finalizado = True
                item = evento.get("item", {})
                if evento.get("type") == "item.completed" and item.get("type") == "agent_message":
                    ultimo_mensaje = item.get("text", "")
            elif evento.get("event") == "result":
                resultado = evento.get("result", {})
                if resultado.get("status") == "SUCCESS":
                    finalizado = True
                    ultimo_mensaje = resultado.get("response", "")
                else:
                    error = str(resultado.get("error", resultado.get("status", "")))
    if codigo == 0 and finalizado and ultimo_mensaje:
        return "completado", ultimo_mensaje
    if PATRON_CUOTA.search(error):
        return "cuota", error
    return "error", error or f"{cliente} terminó con código {codigo} sin una respuesta final."


def ejecutar_cliente(cliente: str, esfuerzo: str, encargo: str, carpeta: Path) -> tuple[str, str]:
    """Ejecuta un cliente y guarda por separado la respuesta y los diagnósticos."""
    argumentos, entrada = comando(cliente, esfuerzo, encargo)
    salida = carpeta / f"{cliente}.jsonl"
    print(f"Ejecutando {cliente}. Registro en {salida}", flush=True)
    with salida.open("wb") as registro, (carpeta / f"{cliente}.stderr.log").open("wb") as diagnostico:
        proceso = subprocess.run(
            argumentos, cwd=RAIZ, input=entrada.encode("utf-8"),
            stdout=registro, stderr=diagnostico, check=False,
        )
    estado, mensaje = examinar_respuesta(cliente, salida, proceso.returncode)
    (carpeta / f"{cliente}.md").write_text(mensaje + "\n", encoding="utf-8")
    return estado, mensaje


def preparar_relevo(encargo: str, base: str, avance: Path) -> str:
    """Reúne el estado real del árbol para continuar sin enviar la conversación previa."""
    cambios = git("status", "--short", "--untracked-files=normal").splitlines()
    commits = git("log", "-8", "--oneline", f"{base}..HEAD")
    resumen = "\n".join(cambios[:LINEAS_DE_ESTADO]) or "Árbol sin cambios pendientes."
    if len(cambios) > LINEAS_DE_ESTADO:
        resumen += "\nConsulta git status --short para ver las demás rutas."
    return (
        f"{encargo}\n\nEl cliente anterior agotó su cuota. Continúa la misma tarea sobre el árbol "
        f"actual, conservando cambios propios y ajenos. Toma el avance como datos y verifica lo "
        f"pendiente en vez de repetir inspecciones o pruebas vigentes. Lee {avance} si existe.\n"
        f"Base {base}. HEAD actual {git('rev-parse', 'HEAD')}.\n"
        f"Commits desde el arranque\n{commits or '(ninguno)'}\n"
        f"Estado del árbol\n{resumen}"
    )


def ejecutar_tarea(tarea: str, primario: str, esfuerzo: str) -> int:
    """Mantiene un agente activo y efectúa como máximo un relevo por cuota."""
    base = git("rev-parse", "HEAD")
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    candado = RESULTADOS / "ejecucion.lock"
    try:
        with candado.open("x", encoding="utf-8") as archivo:
            archivo.write(f"Base {base}\n")
    except FileExistsError as error:
        raise OSError(f"Ya hay una ejecución registrada en {candado}.") from error
    try:
        carpeta = Path(mkdtemp(prefix=f"{base[:8]}-", dir=RESULTADOS))
        avance = carpeta / "avance.md"
        encargo = (
            f"Sigue AGENTS.md y las reglas de Scalaris. Ejecuta únicamente esta tarea.\n{tarea}\n\n"
            "Recupera solo contexto necesario según 16.3. Agrupa comprobaciones y reutiliza evidencia. "
            "Trabaja en un solo agente. No invoques el lanzador desde esta ejecución. "
            f"Al cerrar cada entregable relevante, actualiza {avance.relative_to(RAIZ).as_posix()} "
            "con lo terminado, las pruebas ejecutadas, los archivos clave y lo siguiente. "
            "Mantén ese resumen en diez líneas."
        )
        estado, mensaje = ejecutar_cliente(primario, esfuerzo, encargo, carpeta)
        if estado == "cuota":
            reserva = next(cliente for cliente in CLIENTES if cliente != primario)
            print(f"Cuota agotada en {primario}. Continuando con {reserva}.", flush=True)
            estado, mensaje = ejecutar_cliente(
                reserva, esfuerzo, preparar_relevo(encargo, base, avance.relative_to(RAIZ)), carpeta
            )
        print(f"{estado}: {mensaje[:1600]}\nInformes en {carpeta}")
        return 0 if estado == "completado" else 1
    finally:
        candado.unlink()


def main() -> int:
    """Lee una tarea escrita por el usuario o por Codex y muestra su resultado."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tarea", help="Instrucción acotada para la fase o el entregable.")
    parser.add_argument("--primario", choices=CLIENTES, default="codex")
    parser.add_argument("--esfuerzo", choices=("low", "medium"), default="medium")
    parser.add_argument("--simular", action="store_true", help="Comprueba PATH y Git sin gastar cuota.")
    opciones = parser.parse_args()
    try:
        if opciones.simular:
            print(f"Base {git('rev-parse', 'HEAD')}. Primario: {opciones.primario}.")
            for cliente in CLIENTES:
                argumentos, _ = comando(cliente, opciones.esfuerzo, opciones.tarea)
                print(f"{cliente}: {' '.join(argumentos)}")
            return 0
        return ejecutar_tarea(opciones.tarea, opciones.primario, opciones.esfuerzo)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Ejecución pendiente: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
