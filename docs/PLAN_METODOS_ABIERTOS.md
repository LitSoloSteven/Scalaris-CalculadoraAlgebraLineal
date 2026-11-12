# Plan de ejecución — Métodos abiertos (Newton-Raphson y secante)

Documento de trabajo para implementar el módulo básico de métodos abiertos de Scalaris.
Base revisada: rama `develop`, commit `38a2a7b`.
Fecha: 12 de noviembre de 2026.

## 1. Objetivo

Agregar una herramienta que resuelva `f(x) = 0` con dos métodos abiertos:

- Newton-Raphson: usa `x0` y calcula `f'(x)` automáticamente.
- Secante: usa `x0` y `x1`, sin derivada explícita.

La herramienta debe mostrar la gráfica de la función después de escribirla, ejecutar el método con tolerancia y máximo de iteraciones, y reportar raíz aproximada, residuo e iteraciones. El alcance es deliberadamente básico para tener una versión funcional rápida.

### Cobertura de los requisitos del PDF

| Requisito del PDF | Dónde se implementa |
| --- | --- |
| Resolver `f(x) = 0` | `newton.py`, `secante.py` |
| Newton usa `x0` y `f'(x)` | `newton.py` + `derivada_simbolica.py` |
| Secante usa `x0` y `x1` | `secante.py` |
| Parada por `abs(f(x_n)) < epsilon` | Ambos motores |
| Parada por `abs(x_n - x_{n-1}) < epsilon` | Ambos motores |
| Máximo de iteraciones | `validacion_abiertos.py` y ambos motores |
| Reportar raíz, residuo e iteraciones | `ResultadoMetodoAbierto` y vista |
| Tolerancia por defecto `1e-6` | Contrato y captura |
| Máximo por defecto `100` | Contrato y captura |
| Gráfica después de ingresar la función | `vista_previa.py` |
| Ejemplos `x^3 - x - 2`, `x^3 - 2x - 5` | Pruebas y ejemplos precargados |

## 2. Estado actual y hallazgos

- El proyecto ya tiene dos métodos de raíces: bisección y regla falsa.
- La lógica de dominio vive en `src/backend/resolutores/raices/` y no depende de NiceGUI.
- La interfaz sigue el patrón `controladores/<herramienta>` + `vistas/<herramienta>`, con componentes compartidos para gráfica, tabla, pasos y tema.
- La gramática de funciones (`gramatica_funcion.py`) valida un AST acotado y el evaluador (`evaluador_funcion.py`) ya compile expresiones con funciones reales, constantes y unidades angulares.
- No hay SymPy ni un derivador simbólico. La derivada debe construirse sobre el AST ya validado.
- La gráfica previa ya existe para bisección y regla falsa. Se puede reutilizar `preparar_vista_previa`, `muestrear_funcion`, `crear_figura_previa` y el coordinador de trabajos.
- La tabla paginada y el reproductor de pasos son componentes compartidos.
- `formatear_expresion` en `src/frontend/controladores/formato_funcion_real.py` proyecta el AST a LaTeX, pero fija la etiqueta `f(x)`. Hay que permitir una etiqueta configurable para mostrar `f'(x)`.

### Línea base de pruebas

- El Python global no tiene `reportlab`; ejecutar `python -m pytest -q` produce 61 errores de colección.
- Usar siempre el entorno del proyecto:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

- Línea base confirmada: `5731 passed, 1 warning in 256.81s` con `venv`. La advertencia es de Starlette/httpx y no está relacionada con este módulo.
- Los cambios de navegación romperán dos pruebas que fijan listas exactas:
  - `tests/test_navegacion_elementos.py`: lista de utilidades y conteo total de claves.
  - `tests/test_inicio_modelo_seleccion.py`: cantidad y lista de tarjetas de utilidades.
  Hay que actualizarlas junto con el catálogo.

## 3. Decisiones de diseño

1. **Una sola página con selector de método.**
   Ruta: `/utilidades/metodos-abiertos`.
   Evita duplicar captura, gráfica, tabla y estilos. El selector cambia los campos y el motor.

2. **Derivada simbólica sobre el AST existente, sin SymPy.**
   Se construye un AST derivado, se serializa con `ast.unparse`, se normaliza y se compila con el evaluador actual. Esto evita agregar dependencias y reutiliza la validación de tamaño, profundidad y dominio.

3. **v1 trabaja en radianes.**
   No se muestra selector de unidad angular para reducir alcance y evitar factores de conversión en la derivada. La captura y la gráfica usan radianes por defecto. Si más adelante se necesita grados, se extiende `derivada_simbolica.py` con los factores correspondientes.

4. **Un contrato común para ambos métodos.**
   Las filas de iteración comparten campos; Newton deja `x_anterior` y `f_x_anterior` en `None`. Esto simplifica serialización, tabla y pruebas.

5. **Criterios de parada alternativos.**
   Se detiene cuando `abs(f(x)) < tolerancia` o cuando `abs(x_nuevo - x_actual) < tolerancia`. Si se cumple el segundo pero el residuo sigue siendo grande, se agrega una advertencia visible. El PDF pide revisar ambos criterios; no se exige que se cumplan simultáneamente.

6. **Sin Glosa, PDF, historial ni modo examen en v1.**
   La página usa la estructura común de navegación, pero no integra `PanelIA` ni exportación. Eso reduce trabajo y pruebas. Se puede agregar después siguiendo el patrón de regla falsa.

7. **Errores como resultado, no como excepción.**
   Los motores devuelven `ResultadoMetodoAbierto` con estado y código. El controlador nunca deja escapar una excepción de dominio hacia NiceGUI.

## 4. Plan de backend

### 4.1 Estructura de archivos

```text
src/backend/resolutores/raices/metodos_abiertos/
  __init__.py
  contrato_abiertos.py
  derivada_simbolica.py
  validacion_abiertos.py
  aritmetica_abierta.py
  newton.py
  secante.py
```

Responsabilidades:

| Archivo | Responsabilidad |
| --- | --- |
| `contrato_abiertos.py` | Dataclasses, literales de estado, constantes y valores por defecto. |
| `derivada_simbolica.py` | Derivación del AST y serialización a una expresión normalizada. |
| `validacion_abiertos.py` | Validación de expresión, `x0`, `x1`, tolerancia y límite de iteraciones. |
| `aritmetica_abierta.py` | Guardas de derivada, denominador, magnitud, error relativo y formato numérico seguro. |
| `newton.py` | Motor iterativo de Newton-Raphson. |
| `secante.py` | Motor iterativo de la secante. |
| `__init__.py` | Exporta `newton`, `secante`, `derivar_expresion` y `validar_entrada_abierta`. |

### 4.2 Contrato

```python
from dataclasses import dataclass
from typing import Literal

MetodoAbierto = Literal["newton", "secante"]
EstadoAbierto = Literal[
    "EXITO", "LIMITE_ITERACIONES", "DERIVADA_NULA",
    "DENOMINADOR_NULO", "DIVERGENCIA", "ERROR",
]
CriterioParada = Literal["", "residuo", "cambio"]


@dataclass(frozen=True, kw_only=True)
class EntradaMetodoAbierto:
    metodo: MetodoAbierto
    expresion: str
    x0: float
    x1: float | None = None
    tolerancia: float = 1e-6
    limite_iteraciones: int = 100


@dataclass(frozen=True)
class IteracionMetodoAbierto:
    i: int
    x_anterior: float | None
    f_x_anterior: float | None
    x_n: float
    f_x_n: float
    derivada: float | None
    x_siguiente: float | None
    f_x_siguiente: float | None
    residuo: float | None
    error_absoluto: float | None
    error_relativo_porcentual: float | None
    criterio: CriterioParada = ""


@dataclass(frozen=True)
class ResultadoMetodoAbierto:
    metodo: MetodoAbierto
    entrada: EntradaMetodoAbierto | None = None
    estado: EstadoAbierto = "ERROR"
    mensaje: str = ""
    codigo_diagnostico: str = ""
    raiz: float | None = None
    residuo: float | None = None
    iteraciones: tuple[IteracionMetodoAbierto, ...] = ()
    iteraciones_totales: int = 0
    derivada_expresion: str | None = None
    advertencias: tuple[str, ...] = ()
    contexto_fallo: dict | None = None
```

Notas:

- `x_anterior` y `f_x_anterior` solo se usan en secante.
- `derivada` solo se usa en Newton.
- Los campos de la aproximación siguiente son opcionales para poder registrar fallos parciales (derivada nula, denominador nulo, evaluación fallida).
- `contexto_fallo` es un diccionario serializable con datos como `x`, `f_x`, `derivada`, `denominador` o `detalle`. No se acopla a `ContextoFallo` de bisección.

### 4.3 Derivada simbólica

API pública:

```python
def derivar_expresion(expresion: str) -> str:
    """Devuelve f'(x) normalizada y validada; lanza ValueError si no se puede derivar."""
```

Implementación:

1. `arbol = analizar_expresion(expresion)`.
2. Derivar el nodo con reglas recursivas.
3. Serializar con `ast.unparse(ast.Expression(body=derivada))`.
4. Normalizar con `normalizar_expresion`.
5. Volver a `analizar_expresion` para validar longitud, nodos y profundidad.
6. Devolver el texto normalizado.

Reglas soportadas:

| Expresión | Derivada |
| --- | --- |
| Constante | `0` |
| `x` | `1` |
| `u + v` / `u - v` | `u' + v'` / `u' - v'` |
| `u * v` | `u' * v + u * v'` |
| `u / v` | `(u' * v - u * v') / v^2` |
| `u^c`, con `c` sin `x` | `c * u^(c - 1) * u'` |
| `c^u`, con `c` constante | `c^u * ln(c) * u'` |
| `u^v`, con `u` y `v` dependientes de `x` | No soportado en v1; error claro |
| `sin(u)`, `cos(u)`, `tan(u)` | `cos(u)u'`, `-sin(u)u'`, `(1 + tan(u)^2)u'` |
| `asin(u)`, `acos(u)`, `atan(u)` | `u'/sqrt(1-u^2)`, `-u'/sqrt(1-u^2)`, `u'/(1+u^2)` |
| `sinh(u)`, `cosh(u)`, `tanh(u)` | `cosh(u)u'`, `sinh(u)u'`, `(1-tanh(u)^2)u'` |
| `exp(u)` | `exp(u)u'` |
| `ln(u)`, `log(u)` | `u'/u` |
| `log10(u)`, `log2(u)` | `u'/(u ln 10)`, `u'/(u ln 2)` |
| `sqrt(u)` | `u'/(2 sqrt(u))` |
| `abs(u)` | `u * u'/abs(u)`; no definida en `u = 0` |

Detalles importantes:

- Si un subárbol no contiene `x`, su derivada es `0`. Esto evita evaluar derivadas de constantes y simplifica el resultado.
- Simplificación básica para que la salida sea legible:
  - `0 + u = u`, `u + 0 = u`, `u - 0 = u`, `0 - u = -u`.
  - `0 * u = 0`, `u * 0 = 0`, `1 * u = u`, `u * 1 = u`, `-1 * u = -u`.
  - `u / 1 = u`, `u^1 = u`, `u^0 = 1`.
  - Plegado de constantes en sumas, restas, productos y cocientes.
- Para `x^3 - x - 2` la salida esperada es equivalente a `3*x^2 - 1`.
- Para `x^3 - 2*x - 5` la salida esperada es equivalente a `3*x^2 - 2`.
- Para `x^x` se devuelve un `ValueError` orientativo: la derivada de una potencia con base y exponente variables no está disponible en esta versión.
- Si la derivada supera los límites de la gramática (512 caracteres, 256 nodos, 32 de profundidad), se devuelve un `ValueError` claro. El motor lo convierte en `ERROR` con código `DERIVADA_DEMASIADO_GRANDE`.
- No se modifica `evaluador_funcion.py`: la derivada se compila con `compilar(derivada_texto)`, que ya valida y evalúa.
- No se admite `abs` en `x = 0` porque la derivada no existe; la evaluación falla con error de dominio y el motor lo reporta.

### 4.4 Validación

`validar_entrada_abierta(datos: Mapping[str, object]) -> EntradaMetodoAbierto`:

- `metodo` debe ser `"newton"` o `"secante"`.
- `expresion`: reutilizar `validar_expresion` (obligatoria, máximo 512 caracteres).
- `x0`: reutilizar `validar_extremo` con nombre `x0`; debe ser finito.
- `x1`:
  - En Newton se ignora o se exige ausente.
  - En secante es obligatorio, finito y distinto de `x0`.
- `tolerancia`:
  - Debe ser numérica, finita y mayor que cero.
  - Valor por defecto `1e-6`.
  - Se recomienda limitar a `1e-15 <= tolerancia <= 1` para evitar tolerancias absurdas; el mensaje debe explicar el rango.
- `limite_iteraciones`: reutilizar `validar_limite_iteraciones` (entero entre 1 y 500; por defecto 100).
- Devolver una `EntradaMetodoAbierto` inmutable.

La validación lanza `ValueError` con mensajes en español. El motor captura ese error y devuelve `ERROR` con `codigo_diagnostico="ENTRADA_INVALIDA"`.

### 4.5 Aritmética y guardas

En `aritmetica_abierta.py`:

```python
UMBRAL_DERIVADA = 1e-12
UMBRAL_DENOMINADOR_RELATIVO = 1e-14
LIMITE_MAGNITUD = 1e12


def derivada_utilizable(derivada: float, x: float) -> bool:
    return abs(derivada) > UMBRAL_DERIVADA * max(1.0, abs(x))


def denominador_utilizable(f_actual: float, f_anterior: float) -> bool:
    escala = max(1.0, abs(f_actual), abs(f_anterior))
    return abs(f_actual - f_anterior) > UMBRAL_DENOMINADOR_RELATIVO * escala


def paso_representable(x: float) -> bool:
    return math.isfinite(x) and abs(x) <= LIMITE_MAGNITUD


def error_relativo_porcentual(x_nuevo: float, x_actual: float) -> float | None:
    if x_nuevo == 0:
        return None
    return abs((x_nuevo - x_actual) / x_nuevo) * 100.0
```

Todas las evaluaciones de `f` y `f'` se envuelven para capturar:

- `ErrorDominio`, `ErrorNoFinito`, `ErrorCapacidadNumerica`.
- `ValueError`, `ZeroDivisionError`, `OverflowError`.

Si falla una evaluación, se devuelve `ERROR` con `codigo_diagnostico="EVALUACION"` y `contexto_fallo` con la abscisa y el detalle. Se conservan las iteraciones ya calculadas.

### 4.6 Motor Newton-Raphson

```python
def newton(entrada: EntradaMetodoAbierto) -> ResultadoMetodoAbierto:
    ...
```

Algoritmo:

1. Validar entrada con `validar_entrada_abierta` si se recibe un mapping; si ya es tipada, comprobar `metodo == "newton"`.
2. Compilar `f = compilar(expresion)`.
3. Calcular `derivada_texto = derivar_expresion(expresion)` y `f_prima = compilar(derivada_texto)`.
4. Evaluar `f_x = f(x0)`.
5. Si `abs(f_x) < tolerancia`, devolver `EXITO` con `codigo_diagnostico`:
   - `PUNTO_INICIAL_RAIZ` si `f_x == 0`.
   - `PUNTO_INICIAL_TOLERANCIA` si no.
   - `iteraciones_totales = 0`, `raiz = x0`, `residuo = abs(f_x)`.
6. Para `i = 1..limite_iteraciones`:
   1. Evaluar `d = f_prima(x)`.
   2. Si no es finita o `not derivada_utilizable(d, x)`, devolver `DERIVADA_NULA` con una fila parcial (si se desea) y contexto `{x, f_x, derivada}`.
   3. Calcular `x_siguiente = x - f_x / d`.
   4. Si no es finita o `not paso_representable(x_siguiente)`, devolver `DIVERGENCIA` con contexto.
   5. Evaluar `f_siguiente = f(x_siguiente)`; si falla, devolver `ERROR` de evaluación.
   6. Calcular `error = abs(x_siguiente - x)` y `error_relativo`.
   7. Crear `IteracionMetodoAbierto` con `x_anterior=None`, `f_x_anterior=None`, `derivada=d`.
   8. Si `abs(f_siguiente) < tolerancia`, marcar `criterio="residuo"` y devolver `EXITO` con código `TOLERANCIA_RESIDUO`.
   9. Si `error < tolerancia`, marcar `criterio="cambio"` y devolver `EXITO` con código `TOLERANCIA_CAMBIO`; agregar advertencia si `abs(f_siguiente) >= tolerancia`.
   10. Actualizar `x = x_siguiente`, `f_x = f_siguiente`.
7. Si se agota el límite, devolver `LIMITE_ITERACIONES` con `raiz = x_siguiente`, `residuo = abs(f_siguiente)` y todas las filas. El mensaje debe indicar que no se alcanzó la tolerancia.

Orden de comprobación: residuo primero, cambio después. Si ambos se cumplen, prevalece `residuo`.

### 4.7 Motor secante

```python
def secante(entrada: EntradaMetodoAbierto) -> ResultadoMetodoAbierto:
    ...
```

Algoritmo:

1. Validar entrada; exigir `x1` y `x0 != x1`.
2. Compilar `f`.
3. Evaluar `f0 = f(x0)` y `f1 = f(x1)`.
4. Si `abs(f0) < tolerancia` o `abs(f1) < tolerancia`, devolver `EXITO` con 0 iteraciones y el punto correspondiente (`PUNTO_INICIAL_RAIZ` o `PUNTO_INICIAL_TOLERANCIA`).
5. Para `i = 1..limite_iteraciones`:
   1. Comprobar `denominador_utilizable(f1, f0)`. Si no, devolver `DENOMINADOR_NULO` con contexto `{x0, x1, f0, f1, denominador}`.
   2. Calcular `x_siguiente = x1 - f1 * (x1 - x0) / (f1 - f0)`.
   3. Comprobar finitud y magnitud; si falla, `DIVERGENCIA`.
   4. Evaluar `f_siguiente = f(x_siguiente)`.
   5. Calcular `error = abs(x_siguiente - x1)` y `error_relativo`.
   6. Crear fila con `x_anterior=x0`, `f_x_anterior=f0`, `x_n=x1`, `f_x_n=f1`, `derivada=None`.
   7. Si `abs(f_siguiente) < tolerancia`, `criterio="residuo"`, `EXITO` con `TOLERANCIA_RESIDUO`.
   8. Si `error < tolerancia`, `criterio="cambio"`, `EXITO` con `TOLERANCIA_CAMBIO` y advertencia si el residuo no es pequeño.
   9. Desplazar: `x0, f0 = x1, f1`; `x1, f1 = x_siguiente, f_siguiente`.
6. Si se agota el límite, `LIMITE_ITERACIONES` con la última aproximación y su residuo.

La fórmula debe implementarse exactamente como en el PDF:

```text
x_{n+1} = x_n - f(x_n) * (x_n - x_{n-1}) / (f(x_n) - f(x_{n-1}))
```

### 4.8 Estados y códigos

| Estado | Código | Significado |
| --- | --- | --- |
| `EXITO` | `TOLERANCIA_RESIDUO` | `abs(f(x)) < tolerancia` |
| `EXITO` | `TOLERANCIA_CAMBIO` | `abs(x_nuevo - x_actual) < tolerancia` |
| `EXITO` | `PUNTO_INICIAL_RAIZ` | El punto inicial ya evalúa exactamente cero |
| `EXITO` | `PUNTO_INICIAL_TOLERANCIA` | El punto inicial ya cumple la tolerancia de residuo |
| `LIMITE_ITERACIONES` | `LIMITE_ITERACIONES` | Se agotó el máximo sin cumplir tolerancia |
| `DERIVADA_NULA` | `DERIVADA_NULA` | `f'(x)` nula o demasiado pequeña |
| `DENOMINADOR_NULO` | `DENOMINADOR_NULO` | `f(x_n) - f(x_{n-1})` nulo o demasiado pequeño |
| `DIVERGENCIA` | `DIVERGENCIA` | Valor no finito o magnitud mayor que `1e12` |
| `ERROR` | `ENTRADA_INVALIDA` | Expresión, puntos, tolerancia o límite inválidos |
| `ERROR` | `EVALUACION` | La función no es real o no se puede evaluar |
| `ERROR` | `DERIVADA_NO_DISPONIBLE` | La derivada simbólica no está soportada |
| `ERROR` | `DERIVADA_DEMASIADO_GRANDE` | La derivada excede los límites de la gramática |

### 4.9 Pruebas de backend

Crear:

```text
tests/test_metodos_abiertos_derivada.py
tests/test_metodos_abiertos_newton.py
tests/test_metodos_abiertos_secante.py
tests/test_metodos_abiertos_validacion.py
tests/test_metodos_abiertos_serializacion.py
```

Casos mínimos:

**Derivada**

- `x^3 - x - 2` → evaluar la derivada en `x = 1.5` y comparar con `5.75`.
- `x^3 - 2*x - 5` → evaluar en `x = 2` y comparar con `10`.
- `sin(x)` → `cos(x)` en `0`, `pi/2`.
- `x^2 + 3*x - 1` → `2*x + 3`.
- `1/x` → `-1/x^2` en `x != 0`.
- `sqrt(x)` → `1/(2*sqrt(x))` en `x > 0`.
- `abs(x)` → `1` en `x > 0`, `-1` en `x < 0`; error en `x = 0`.
- `x^x` → `ValueError`.
- Expresión inválida → `ValueError`.
- Derivada demasiado grande → `ValueError` controlado.

**Newton**

- `x^3 - x - 2`, `x0 = 1.5`, `tol = 1e-6`: `EXITO`, 2 iteraciones, raíz `1.5213798059647863`, residuo `5.893874259754739e-07`, criterio `residuo`.
- `x^3 - 2*x - 5`, `x0 = 2`, `tol = 1e-6`: `EXITO`, 3 iteraciones, raíz `2.094551481698199`, residuo `1.7397612239733462e-09`.
- `x - 2`, `x0 = 2`: 0 iteraciones, `PUNTO_INICIAL_RAIZ`.
- `x - 1.5000001`, `x0 = 1.5000001`, `tol = 1e-6`: 0 iteraciones, `PUNTO_INICIAL_TOLERANCIA`.
- `x^2 + 1`, `x0 = 0`: `DERIVADA_NULA`, sin excepción.
- `1/x`, `x0 = 1`, `limite = 100`: `DIVERGENCIA`.
- `ln(x)`, `x0 = -1`: `ERROR` de evaluación.
- `x^2 - 2`, `x0 = 1`, `tol = 1e-15`, `limite = 1`: `LIMITE_ITERACIONES` con 1 fila.
- Tolerancia `0`, negativa, `NaN`, `inf`: `ERROR` de entrada.
- Límite `0`, `501`, flotante, booleano: `ERROR` de entrada.
- `x0` vacío, `NaN`, `inf` o texto: `ERROR` de entrada.

**Secante**

- `x^3 - x - 2`, `x0 = 1`, `x1 = 2`, `tol = 1e-6`: `EXITO`, 6 iteraciones, raíz `1.5213797079848717`, residuo `7.015477976324291e-09`.
- `x^3 - 2*x - 5`, `x0 = 2`, `x1 = 3`, `tol = 1e-6`: `EXITO`, 5 iteraciones, raíz `2.094551481227599`, residuo `3.511...e-09` en valor absoluto.
- Puntos invertidos `x0 = 2`, `x1 = 1`: misma raíz, sin error.
- `x0 == x1`: `ERROR` de entrada.
- `f(x) = 1`, `x0 = 1`, `x1 = 2`: `DENOMINADOR_NULO`.
- `x - 2`, `x0 = 2`, `x1 = 3`: 0 iteraciones, `PUNTO_INICIAL_RAIZ`.
- `x^2 - 2`, `x0 = 1`, `x1 = 2`, `tol = 1e-15`, `limite = 1`: `LIMITE_ITERACIONES`.
- `1/x`, `x0 = 1`, `x1 = 2`, `limite = 100`: `DIVERGENCIA`.
- `ln(x)` con un punto negativo: `ERROR` de evaluación.
- Serialización `asdict` + `json.dumps(..., allow_nan=False)` para todos los estados.

**Validación y serialización**

- `EntradaMetodoAbierto` usa `1e-6` y `100` por defecto.
- Un `metodo` desconocido devuelve `ERROR`.
- Un resultado de error también es serializable y no contiene `NaN` ni `inf`.
- Los campos opcionales se serializan como `None`, no se omiten.

### 4.10 Orden de implementación del backend

1. `contrato_abiertos.py` y `validacion_abiertos.py`.
2. `derivada_simbolica.py` con sus pruebas.
3. `aritmetica_abierta.py`.
4. `newton.py` con las pruebas de los ejemplos del PDF.
5. `secante.py` con las pruebas de los ejemplos del PDF.
6. Pruebas de errores, límites y serialización.
7. Revisión de estilo: imports relativos, docstrings en español, sin dependencias de NiceGUI.

## 5. Plan de frontend

### 5.1 Estructura de archivos

```text
src/frontend/controladores/metodos_abiertos/
  __init__.py
  captura.py
  controlador.py
  serializacion.py
  presentacion.py
  tabla.py
  pasos.py              # P1: reproductor de pasos

src/frontend/vistas/metodos_abiertos/
  __init__.py
  pagina.py
  vista_metodos_abiertos.py
  composicion.py
  captura.py
  vista_previa.py
  resultado.py
  procedimiento.py      # tabla + pasos
  ejemplos.py

src/frontend/recursos/css/vistas_metodos_abiertos.css
```

La vista se registra como `metodos_abiertos` en el catálogo y en `recursos_vistas.py`.

### 5.2 Captura

Controles:

- Selector de método: `ui.toggle({"newton": "Newton-Raphson", "secante": "Secante"})`.
- `Función f(x)`: `ui.input`, placeholder `Ejemplo: x^3 - x - 2`, máximo 512 caracteres, sin autocompletar.
- `Punto inicial x0`: obligatorio en ambos métodos.
- `Segundo punto x1`: visible solo en secante.
- `Tolerancia ε`: valor por defecto `1e-6`.
- `Máximo de iteraciones`: valor por defecto `100`.
- Botón `Calcular raíz`.
- Botón `Limpiar`.
- Desplegable `Ejemplos` con:
  - Newton, `x^3 - x - 2`, `x0 = 1.5`.
  - Newton, `x^3 - 2x - 5`, `x0 = 2`.
  - Secante, `x^3 - x - 2`, `x0 = 1`, `x1 = 2`.
  - Secante, `x^3 - 2x - 5`, `x0 = 2`, `x1 = 3`.
  - Caso de derivada nula: `x^2 + 1`, `x0 = 0`.
  - Caso de denominador nulo: `1`, `x0 = 1`, `x1 = 2` (secante).

Comportamiento:

- Al cambiar de método, mostrar/ocultar `x1`, actualizar la fórmula guía y retirar el resultado anterior. No borrar la función.
- Al editar función, `x0`, `x1`, tolerancia o límite, invalidar el resultado anterior y conservar la gráfica.
- `Enter` en los campos numéricos y en la función dispara el cálculo.
- `Limpiar` restaura valores por defecto y borra resultado, tabla y marcas de la gráfica.
- Cargar un ejemplo rellena todos los campos y programa la gráfica previa.

`capturar()` devuelve un diccionario crudo:

```python
{
    "metodo": self.metodo.value,
    "expresion": self.expresion.value,
    "x0": self.x0.value,
    "x1": self.x1.value if self.metodo.value == "secante" else "",
    "tolerancia": self.tolerancia.value,
    "limite_iteraciones": self.limite.value,
}
```

La conversión a tipos reales se hace en `controladores/metodos_abiertos/captura.py` con `real_capturado` y `entero_capturado`, siguiendo el patrón de regla falsa.

### 5.3 Gráfica previa

Requisito principal: la gráfica debe aparecer después de ingresar la función, sin esperar a pulsar Calcular.

Implementación:

- Reutilizar `preparar_vista_previa` y `muestrear_funcion`.
- Usar `crear_figura_previa` de `src/frontend/componentes/figura_funcion_real.py`.
- Panel `PanelVistaPrevia` propio, inspirado en el de regla falsa pero sin campos de rango:
  - `capturar()`: `{"expresion": vista.expresion.value, "x_min": -10, "x_max": 10}`.
  - `programar()`: invalida la muestra anterior y programa la actualización con `ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS`.
  - `actualizar()`: ejecuta `preparar_vista_previa` en un trabajador (`CoordinadorTrabajosRaices`) para no bloquear la UI.
  - Nodo estable `ui.plotly` para evitar parpadeos.
  - Estado textual con `role=status` y `aria-live=polite`.
- Si la expresión es inválida, mostrar el mensaje de error y limpiar la figura anterior.
- Al obtener un resultado exitoso, agregar a la figura:
  - Marcador de la raíz en `(raiz, 0)`.
  - Punto inicial `x0` y, en secante, `x1`.
  - Opcional P2: recta tangente (Newton) o secante (secante) de la fila seleccionada.
- Mantener la gráfica al mostrar errores de cálculo; solo se actualiza el panel de resultados.

Rango visual: `(-10, 10)` por defecto. No se agregan controles de rango en v1; Plotly permite zoom. Si se necesita, se puede añadir un desplegable "Avanzado" con `x_min`/`x_max` reutilizando `rango_grafica`.

### 5.4 Controlador y serialización

`controladores/metodos_abiertos/captura.py`:

```python
def preparar_entrada(captura: Mapping[str, object]) -> EntradaMetodoAbierto:
    ...
```

- Detecta el método.
- Convierte `x0` y `x1` con `real_capturado`.
- Convierte tolerancia y límite con los helpers existentes.
- Deja que `validar_entrada_abierta` haga las validaciones de dominio.

`controladores/metodos_abiertos/controlador.py`:

```python
def resolver_captura(captura: Mapping[str, object]) -> dict:
    try:
        entrada = preparar_entrada(captura)
    except ValueError as error:
        return _error_adaptacion(str(error), "ENTRADA_INVALIDA")
    if entrada.metodo == "newton":
        resultado = newton(entrada)
    elif entrada.metodo == "secante":
        resultado = secante(entrada)
    else:
        return _error_adaptacion("Método no reconocido.", "ENTRADA_INVALIDA")
    return serializar_resultado(resultado)
```

`controladores/metodos_abiertos/serializacion.py`:

- `asdict(resultado)`.
- `json.dumps(..., allow_nan=False)`.
- Si falla, devolver un error serializable, nunca lanzar desde el controlador.

### 5.5 Presentación del resultado

Títulos por estado:

| Estado / código | Título |
| --- | --- |
| `EXITO` / `TOLERANCIA_RESIDUO` | Convergió por residuo |
| `EXITO` / `TOLERANCIA_CAMBIO` | Convergió por cambio entre aproximaciones |
| `EXITO` / `PUNTO_INICIAL_RAIZ` | El punto inicial ya es una raíz |
| `EXITO` / `PUNTO_INICIAL_TOLERANCIA` | El punto inicial ya cumple la tolerancia |
| `LIMITE_ITERACIONES` | Límite de iteraciones; tolerancia no alcanzada |
| `DERIVADA_NULA` | Derivada nula o demasiado pequeña |
| `DENOMINADOR_NULO` | Denominador nulo o demasiado pequeño |
| `DIVERGENCIA` | Divergencia numérica |
| `ERROR` | Error de entrada o evaluación |

Resumen visible:

- Raíz aproximada.
- Residuo `|f(x)|`.
- Iteraciones realizadas.
- Método usado.
- Derivada `f'(x)` en LaTeX para Newton.
- Mensaje de estado y advertencias.
- Si no hay convergencia, mostrar la última aproximación disponible y el contexto del fallo.

Formato numérico:

- Reutilizar `numero` de `src.frontend.controladores.formato_numerico_raices` (o `biseccion.presentacion.numero`).
- Mostrar 9 decimales por defecto y notación científica para valores muy pequeños.
- No recalcular valores en la interfaz; solo formatear los que devuelve el motor.

Para la derivada:

- Extender `formatear_expresion(expresion, etiqueta="f(x)")`.
- Llamar `formatear_expresion(derivada_expresion, etiqueta="f'(x)")`.
- Si el formateo falla, mostrar la expresión normalizada en texto plano como respaldo.

### 5.6 Tabla y procedimiento

Tabla:

- Reutilizar `PaginacionIteraciones` (15 filas por página).
- Columnas Newton:
  - `i`, `x_n`, `f(x_n)`, `f'(x_n)`, `x_{n+1}`, `f(x_{n+1})`, `|f(x_{n+1})|`, `|Δx|`, `Error rel. %`, `Criterio`.
- Columnas secante:
  - `i`, `x_{n-1}`, `x_n`, `f(x_{n-1})`, `f(x_n)`, `x_{n+1}`, `f(x_{n+1})`, `|f(x_{n+1})|`, `|Δx|`, `Error rel. %`, `Criterio`.
- Mostrar "—" en campos `None`.
- Agregar una fila inicial `0 (inicial)` solo en la presentación de Newton para comparar con la tabla del PDF; no cuenta como iteración.
- Si no hay filas, mostrar el motivo del fallo.

Procedimiento (P1):

- Reutilizar `ReproductorPasos` con `PasoReproductor` y `GrupoReproductor`.
- Paso de planteamiento: función, método, `x0`/`x1`, tolerancia y máximo.
- Un paso por iteración con la fórmula y los valores sustituidos:
  - Newton: `x_{n+1} = x_n - f(x_n)/f'(x_n)`.
  - Secante: `x_{n+1} = x_n - f(x_n)(x_n - x_{n-1})/(f(x_n) - f(x_{n-1}))`.
- Paso de cierre: estado, raíz, residuo e iteraciones.
- Sin Glosa: usar el reproductor en modo de solo lectura; no enlazar `al_explicar` ni contexto IA.
- Si el reproductor resulta costoso de adaptar, v1 puede mostrar las fórmulas y la tabla sin reproductor; el reproductor queda como P1.

### 5.7 Navegación y recursos

Cambios obligatorios:

1. `src/frontend/navegacion/catalogo.py`
   - `_ETIQUETAS_CORTAS["metodos_abiertos"] = "Abiertos"`.
   - Nueva `Herramienta`:
     ```python
     Herramienta(
         identificador="metodos_abiertos",
         nombre="Métodos abiertos",
         descriptor="Newton-Raphson y secante",
         ruta="/utilidades/metodos-abiertos",
         identificador_pilar="utilidades",
         icono="utilidades",
         titulo_pagina="Métodos abiertos | Scalaris",
         ejemplo_latex=r"x_{n+1} = x_n - \frac{f(x_n)}{f'(x_n)}",
         habilitada=True,
     )
     ```
   - Agregar `"metodos_abiertos"` al final de `ORDEN_NAVEGACION_PLANA`.

2. `src/frontend/rutas.py`
   - Nueva `_registrar_pagina_metodos_abiertos()`.
   - Llamarla desde `registrar_rutas()`.
   - Usar `configurar_tema("metodos_abiertos")`.

3. `src/frontend/recursos_vistas.py`
   - `_METODOS_ABIERTOS = frozenset({"metodos_abiertos"})`.
   - Incluirlo en `_RAICES` y, por tanto, en `_VISTAS`.
   - Mapear `"vistas_metodos_abiertos.css": _METODOS_ABIERTOS`.
   - Si se agrega JS propio, mapearlo al mismo conjunto.
   - `tema_graficos.js` ya está asociado a `_RAICES`; al incluir el nuevo conjunto, se carga automáticamente.

4. `src/frontend/recursos/plantillas/cabecera.html`
   - Agregar `<link rel="stylesheet" href="/assets/css/vistas_metodos_abiertos.css">`.
   - El filtro de recursos lo quita en las demás vistas.

5. `tests/comun_construccion_vistas.py`
   - Agregar `"metodos_abiertos": ("metodos_abiertos.vista_metodos_abiertos", "VistaMetodosAbiertos")` a `VISTAS_RUTAS`.

6. Pruebas de navegación existentes
   - `tests/test_navegacion_elementos.py`: agregar `"metodos_abiertos"` a la lista de utilidades; actualizar el conteo total de 15 a 16.
   - `tests/test_inicio_modelo_seleccion.py`: actualizar `len(p_util.tarjetas)` de 4 a 5 y la lista de claves.

7. `README.md`
   - Agregar la fila de la nueva herramienta en la tabla de utilidades.

### 5.8 Pruebas de frontend

Crear:

```text
tests/comun_metodos_abiertos_vista.py
tests/test_metodos_abiertos_pagina.py
tests/test_metodos_abiertos_controlador_interfaz.py
tests/test_metodos_abiertos_grafica_previa.py
tests/test_metodos_abiertos_registro_publico.py
```

Casos mínimos:

**Registro y navegación**

- `ruta_de("metodos_abiertos") == "/utilidades/metodos-abiertos"`.
- La herramienta está habilitada y visible en utilidades.
- `ORDEN_NAVEGACION_PLANA.count("metodos_abiertos") == 1`.
- La miga de pan termina en `("Métodos abiertos", "/utilidades/metodos-abiertos")`.
- El título de página es correcto.

**Recursos**

- `vistas_metodos_abiertos.css` se carga en `metodos_abiertos` y no en bisección, regla falsa, inicio o álgebra.
- `tema_graficos.js` se carga en `metodos_abiertos`.
- `reproductor_pasos.js` y MathJax siguen disponibles.
- No se filtran scripts exclusivos de bisección.

**Vista**

- La página se construye sin errores.
- El selector de método muestra `x1` solo en secante.
- Los valores por defecto son `1e-6` y `100`.
- `Enter` dispara el cálculo.
- Los campos tienen etiquetas accesibles y el estado usa `role=status`.
- Cargar un ejemplo rellena función y puntos.
- Limpiar restaura el estado inicial.

**Gráfica previa**

- Al escribir `x^3 - x - 2`, la tarea de vista previa termina con `estado == "EXITO"` y una figura con datos.
- Una expresión inválida muestra error y no rompe la vista.
- La gráfica no se reconstruye innecesariamente: el nodo `ui.plotly` se conserva.
- Al calcular, se agrega la marca de la raíz sin perder la curva.

**Cálculo**

- Newton con `x^3 - x - 2`, `x0 = 1.5`, `tol = 1e-6`: raíz y residuo esperados, 2 filas, derivada mostrada.
- Newton con `x^3 - 2x - 5`, `x0 = 2`: 3 filas.
- Secante con `x^3 - x - 2`, `x0 = 1`, `x1 = 2`: 6 filas.
- Secante con `x^3 - 2x - 5`, `x0 = 2`, `x1 = 3`: 5 filas.
- `x^2 + 1`, `x0 = 0`: estado `DERIVADA_NULA` y mensaje visible.
- `1`, `x0 = 1`, `x1 = 2`: estado `DENOMINADOR_NULO`.
- `1/x`, `x0 = 1`, límite 100: `DIVERGENCIA`.
- `ln(x)` con punto negativo: `ERROR` de evaluación.
- Límite 1 con tolerancia exigente: `LIMITE_ITERACIONES`.
- La tabla pagina de 15 en 15 y muestra "—" en campos ausentes.
- El resultado anterior se retira al editar un campo.

**Controlador**

- `resolver_captura` despacha Newton y secante.
- Una captura inválida devuelve un sobre serializable, no una excepción.
- Un método desconocido devuelve `ERROR`.
- `json.dumps(..., allow_nan=False)` funciona para todos los estados.

### 5.9 Orden de implementación del frontend

1. `captura.py` y `controlador.py` con pruebas de adaptación.
2. `presentacion.py` y `tabla.py`.
3. `composicion.py`, `captura.py` de la vista y `vista_metodos_abiertos.py` mínimos.
4. `vista_previa.py` y la gráfica automática.
5. `resultado.py` y `procedimiento.py` con tabla.
6. Registro en catálogo, rutas y recursos.
7. Pruebas de página, navegación y recursos.
8. P1: reproductor de pasos y superposición de tangente/secante por fila.

## 6. Verificación y aceptación

### 6.1 Comandos

```powershell
# Pruebas del módulo
.\venv\Scripts\python.exe -m pytest -q tests/test_metodos_abiertos_derivada.py tests/test_metodos_abiertos_newton.py tests/test_metodos_abiertos_secante.py tests/test_metodos_abiertos_validacion.py

# Pruebas de interfaz y registro
.\venv\Scripts\python.exe -m pytest -q tests/test_metodos_abiertos_pagina.py tests/test_metodos_abiertos_controlador_interfaz.py tests/test_navegacion_elementos.py tests/test_inicio_modelo_seleccion.py

# Suite completa antes de integrar
.\venv\Scripts\python.exe -m pytest -q
```

Arranque manual:

```powershell
.\venv\Scripts\python.exe -m src.main
```

Abrir `http://127.0.0.1:8080/utilidades/metodos-abiertos`.

### 6.2 Casos manuales

| Método | Función | Iniciales | Tolerancia | Resultado esperado |
| --- | --- | --- | --- | --- |
| Newton | `x^3 - x - 2` | `x0 = 1.5` | `1e-6` | 2 iteraciones; raíz `1.521379806`; residuo `5.89e-7` |
| Newton | `x^3 - 2x - 5` | `x0 = 2` | `1e-6` | 3 iteraciones; raíz `2.094551482`; residuo `1.74e-9` |
| Secante | `x^3 - x - 2` | `x0 = 1`, `x1 = 2` | `1e-6` | 6 iteraciones; raíz `1.521379708`; residuo `7.02e-9` |
| Secante | `x^3 - 2x - 5` | `x0 = 2`, `x1 = 3` | `1e-6` | 5 iteraciones; raíz `2.094551481`; residuo `3.51e-9` |

Nota: la tabla del PDF muestra para Newton `x^3 - x - 2` una iteración adicional hasta `1.521379707`. Con tolerancia `1e-6`, el criterio de residuo se cumple antes, en `1.521379806`. Para reproducir la última cifra del PDF, usar una tolerancia más exigente, por ejemplo `1e-9`. Esto no es un defecto; es consecuencia del criterio de parada.

### 6.3 Criterios de aceptación

- [ ] La ruta `/utilidades/metodos-abiertos` existe y aparece en la navegación de utilidades.
- [ ] La gráfica se actualiza automáticamente al escribir una función válida.
- [ ] Newton calcula y muestra `f'(x)` sin pedirla al usuario.
- [ ] Secante muestra y exige `x1`.
- [ ] Los valores por defecto son tolerancia `1e-6` y máximo `100`.
- [ ] Se aplican ambos criterios de parada y se informa cuál se usó.
- [ ] Se reportan raíz, residuo e iteraciones.
- [ ] La tabla muestra la traza y pagina correctamente.
- [ ] Los estados de derivada nula, denominador nulo, divergencia, límite y error son visibles y no rompen la página.
- [ ] Los cuatro ejemplos del PDF producen los valores esperados.
- [ ] No se cargan recursos de otras vistas y no se rompen las pruebas de navegación existentes.
- [ ] La suite completa con `venv` queda en verde.
- [ ] La disposición funciona en escritorio y en pantalla estrecha.

## 7. Estimación

| Fase | Trabajo | Estimación |
| --- | --- | --- |
| Backend | Contrato, validación, derivada, Newton, secante | 1 día |
| Backend | Pruebas, errores, serialización | 0.5 día |
| Frontend | Captura, composición, controlador | 0.5 día |
| Frontend | Gráfica previa y resultado | 0.5 día |
| Frontend | Tabla y procedimiento | 0.5 día |
| Frontend | Navegación, recursos y pruebas | 0.5 día |
| Verificación | Casos manuales, regresión, ajustes | 0.5 día |
| **Total** | Versión básica (P0 + tabla) | **2.5 a 3 días** |
| Extra P1 | Reproductor de pasos y superposición por fila | +0.5 a 1 día |

Ruta mínima para tener algo usable rápido:

1. Backend completo con pruebas (1.5 días).
2. Captura + gráfica previa + resultado + tabla (1 día).
3. Registro y verificación (0.5 día).

## 8. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| La derivada simbólica no cubre alguna función | Newton falla en casos válidos | Tabla de reglas completa para la gramática actual; error claro para `u^v`; pruebas por función |
| La derivada genera expresiones enormes | Evaluación lenta o error de límites | Simplificación básica y validación con `analizar_expresion`; error `DERIVADA_DEMASIADO_GRANDE` |
| `abs(x)` en `x = 0` | Error de dominio | Reportar `ERROR` de evaluación con mensaje; no ocultar |
| Falsa convergencia por cambio pequeño | Resultado engañoso | Mostrar ambos criterios y advertencia si el residuo no es pequeño |
| Divergencia o desbordamiento | Valores `inf`/`nan` en la UI | Guarda de magnitud `1e12`, comprobación de finitud y serialización estricta |
| Las pruebas de navegación fijan listas exactas | Fallos tras agregar la herramienta | Actualizar `test_navegacion_elementos.py` y `test_inicio_modelo_seleccion.py` en el mismo commit |
| Fuga de recursos entre vistas | CSS/JS incorrectos | Registrar el nuevo conjunto en `recursos_vistas.py` y probar la selección |
| El Python global no tiene dependencias | Errores de colección | Usar siempre `venv`; documentarlo en el plan y en el README si hace falta |
| La vista previa bloquea la UI | Mala experiencia | Reutilizar el coordinador de trabajos y el antirrebote existentes |
| El reproductor de pasos está muy acoplado a Glosa | Retraso | Dejarlo como P1; v1 puede mostrar tabla y fórmulas estáticas |

## 9. Orden sugerido de ramas y commits

Rama:

```text
feature/metodos-abiertos
```

Commits:

1. `feat(metodos-abiertos): contrato, validacion y derivada simbolica`
2. `feat(metodos-abiertos): motor Newton-Raphson`
3. `feat(metodos-abiertos): motor secante`
4. `test(metodos-abiertos): cobertura backend y ejemplos del PDF`
5. `feat(metodos-abiertos): captura, grafica previa y controlador`
6. `feat(metodos-abiertos): resultado, tabla y composicion`
7. `feat(metodos-abiertos): registro, ruta y recursos`
8. `test(metodos-abiertos): integracion de pagina y navegacion`
9. `docs(metodos-abiertos): plan y verificacion`

Cada commit debe dejar la suite dirigida en verde. El commit 7 es el que puede romper pruebas de navegación; por eso incluye las actualizaciones de listas exactas.

## 10. Anexo: valores de referencia calculados

Estos valores se obtuvieron con la fórmula y el criterio de parada propuestos, en radianes y con tolerancia `1e-6`.

### Newton

```text
f(x) = x^3 - x - 2, x0 = 1.5
i = 1: x = 1.5, f = -0.125, f' = 5.75, x_next = 1.5217391304347827
i = 2: x = 1.5217391304347827, f = 0.0021369277554046384,
       f' = 5.947069943289225, x_next = 1.5213798059647863,
       residuo = 5.893874259754739e-07
```

```text
f(x) = x^3 - 2x - 5, x0 = 2
i = 1: x = 2.0, f = -1.0, f' = 10.0, x_next = 2.1
i = 2: x = 2.1, f = 0.06100000000000083, f' = 11.23,
       x_next = 2.094568121104185
i = 3: x = 2.094568121104185, f = 0.0001857231732707021,
       f' = 11.16164684183775, x_next = 2.094551481698199,
       residuo = 1.7397612239733462e-09
```

### Secante

```text
f(x) = x^3 - x - 2, x0 = 1, x1 = 2
6 iteraciones; raíz = 1.5213797079848717;
residuo = 7.015477976324291e-09
```

```text
f(x) = x^3 - 2x - 5, x0 = 2, x1 = 3
5 iteraciones; raíz = 2.094551481227599;
residuo = 3.511...e-09 (valor absoluto)
```

### Comprobaciones rápidas de la derivada

```text
d/dx (x^3 - x - 2)     = 3x^2 - 1      -> en x = 1.5: 5.75
d/dx (x^3 - 2x - 5)    = 3x^2 - 2      -> en x = 2:   10
d/dx (sin x)           = cos x         -> en x = 0:   1
d/dx (1/x)             = -1/x^2        -> en x = 2:   -0.25
d/dx (sqrt x)          = 1/(2 sqrt x)  -> en x = 4:   0.25
```
