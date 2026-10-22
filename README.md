# Scalaris

Aplicación educativa de álgebra lineal para la Universidad Americana (UAM). Permite capturar ejercicios, obtener resultados con aritmética racional exacta y recorrer procedimientos paso a paso. Incluye un visualizador geométrico y Glosa, un asistente de explicación conectado a OpenRouter.

La interfaz está construida con NiceGUI, los gráficos con Plotly y el motor matemático con Python. El cálculo algebraico usa `fractions.Fraction`; la representación geométrica convierte los valores a punto flotante para dibujarlos.

## Herramientas

El inicio está en `/`. La navegación organiza las herramientas en tres grupos:

### Álgebra lineal

| Herramienta | Funciones | Ruta |
| --- | --- | --- |
| Sistemas de ecuaciones | Captura matricial o por ecuaciones, eliminación de Gauss y Gauss-Jordan; solución única, infinitas soluciones o sistema incompatible. | `/algebra-lineal/sistemas` |
| Vectores | Suma y resta, multiplicación por escalar, combinación lineal e independencia lineal. | `/algebra-lineal/vectores` |
| Matrices | Evaluación de expresiones con suma, resta, producto, escalares, paréntesis y transpuesta. | `/algebra-lineal/matrices` |
| Matriz inversa | Reducción de la matriz aumentada `[A \| I]` mediante Gauss-Jordan y detección de matrices singulares. | `/algebra-lineal/inversa` |
| Determinantes | Eliminación con pivoteo, identificada como `lu`, y expansión de Laplace por cofactores. | `/algebra-lineal/determinantes` |
| Modelo de Leontief | Resolución del modelo de insumo-producto a partir de la matriz de coeficientes y la demanda. | `/algebra-lineal/leontief` |
| Transformaciones lineales | Núcleo, imagen, rango y nulidad de la transformación representada por una matriz. | `/algebra-lineal/transformaciones` |

La vista de Matrices ya no incluye un panel independiente de factorización LU. El método `lu` de Determinantes sigue disponible: calcula el determinante mediante eliminación con pivoteo.

### Visualizador geométrico

La ruta `/visualizador` reúne tres escenas:

- **Rectas y planos:** representación de sistemas de dos o tres variables.
- **Vectores:** exploración de la suma y el escalamiento de dos vectores.
- **Combinación lineal:** representación del vector objetivo y sus generadores.

Las herramientas compatibles permiten transferir datos al visualizador sin volver a introducirlos. Los gráficos son interactivos y adaptan su paleta al tema de la interfaz.

### Utilidades numéricas

| Herramienta | Funciones | Ruta |
| --- | --- | --- |
| Conversor de bases | Conversión de enteros entre decimal, binario, octal y hexadecimal. | `/utilidades/bases` |
| Números romanos | Suma, resta y multiplicación con presentación del procedimiento. | `/utilidades/romanos` |

## Captura y resultados

- Las entradas algebraicas admiten enteros, decimales y fracciones como `-3/7`. El analizador numérico compartido no admite notación científica.
- Las cuadrículas permiten navegar con flechas y distribuir tablas pegadas en formato TSV, como las copiadas desde una hoja de cálculo.
- Las vistas ofrecen previsualización matemática, validación de entradas y procedimientos según la operación. Los reproductores permiten recorrer los pasos disponibles.
- Al cambiar los datos se invalida el resultado anterior. Las vistas que calculan en segundo plano descartan respuestas que ya no corresponden a la captura vigente.
- Los sistemas permiten alternar entre captura matricial y ecuaciones, y recuperar ejercicios desde el historial de sesión.
- En suma y resta de vectores, el modo estricto rechaza orientaciones incompatibles; sin él, se puede ajustar la orientación y mostrar ese ajuste en el procedimiento.
- Los controles para añadir o eliminar vectores se muestran cuando la cantidad es variable. Se ocultan en suma/resta, escalar y la escena de dos vectores del visualizador.

### Límites principales

| Entrada | Límite |
| --- | --- |
| Dimensiones de sistemas | Hasta 10 ecuaciones y 10 variables; la vista previa de ecuaciones tiene un presupuesto adicional de 48 celdas de coeficientes. |
| Matrices del evaluador | Hasta 10 filas y 10 columnas por matriz. |
| Expresión matricial | Hasta 2048 caracteres y 32 operaciones; también se limita el volumen de la traza. |
| Matriz inversa | Orden máximo de 50; las vistas previas y el contexto de explicación tienen límites menores. |
| Determinante por cofactores | Orden máximo de 8, con presupuesto adicional de expansión. |
| Dimensión de vectores | Hasta 10 componentes. |
| Combinación lineal | Hasta 9 vectores en la captura: el objetivo `b` y hasta 8 generadores. |
| Independencia lineal | De 1 a 10 vectores. |
| Modelo de Leontief | De 2 a 8 sectores. |
| Transformaciones lineales | Hasta 8 filas y 8 columnas. |

Los límites y las tolerancias se definen en [las constantes del dominio](src/backend/constantes.py). Cada herramienta aplica además las restricciones de su operación y de su captura.

## Glosa

Glosa es el asistente de explicación de Scalaris. Puede recibir el contexto del ejercicio y de sus pasos para responder preguntas y ofrecer sugerencias. La comunicación con los modelos se realiza desde Python mediante OpenRouter.

Su configuración es opcional: las herramientas matemáticas no necesitan una clave de IA para calcular. Sin `OPENROUTER_API_KEY`, Glosa informa que el servicio no está configurado. Los modelos disponibles y sus condiciones dependen del proveedor; se pueden seleccionar mediante variables de entorno.

Las consultas enviadas a Glosa pueden incluir datos del ejercicio y mensajes del usuario. Evita introducir información sensible. Sus explicaciones son un apoyo de estudio y conviene contrastarlas con el resultado del motor y el procedimiento mostrado.

## Interfaz

Scalaris dispone de tres temas: **Papel**, **Marea** y **Medianoche**. Comparte tokens de espaciado, tipografía, color y movimiento entre las herramientas.

La interfaz incluye navegación por categorías, presentación inicial, panel lateral de Glosa y selectores de operaciones adaptables. En Vectores, el selector distribuye sus cuatro opciones en dos columnas cuando falta espacio y mantiene el indicador de selección. El mismo componente se utiliza con dos opciones en Determinantes.

Los componentes incorporan estados de foco, manejo de teclado y reglas para movimiento reducido. La compatibilidad visual en un dispositivo o nivel de zoom concreto debe comprobarse en el navegador; la suite automatizada no sustituye esa revisión.

## Instalación y ejecución local

### Requisitos

- Python con soporte para las dependencias indicadas a continuación.
- Un navegador moderno.
- Node.js para ejecutar la suite completa, que incluye pruebas de JavaScript. No se necesita para iniciar el servidor Python.
- Acceso a Internet para instalar dependencias y usar Glosa. La configuración actual también carga MathJax y la tipografía desde servicios externos.

El entorno de referencia comprobado usa **Python 3.14.7**, **NiceGUI 3.16.0**, **Plotly 7.0.0** y **Node.js 24.20.0**. Esto identifica el entorno utilizado; no establece una versión mínima compatible.

### Preparar el entorno

```bash
git clone https://github.com/LitSoloSteven/Scalaris-CalculadoraAlgebraLineal.git
cd Scalaris-CalculadoraAlgebraLineal
python -m venv venv
```

En Windows PowerShell, activa el entorno con:

```powershell
.\venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
source venv/bin/activate
```

Instala las dependencias del entorno de referencia:

```bash
python -m pip install nicegui==3.16.0 plotly==7.0.0 requests==2.34.2 python-dotenv==1.2.3 pytest==9.1.1
```

**Estado de `requirements.txt`:** el archivo conserva el rango `nicegui>=1.4.0, <2.0.0` y no declara `requests` ni `python-dotenv`, aunque el código las importa. Por eso `pip install -r requirements.txt` por sí solo no reproduce el entorno de referencia. La instalación anterior enumera las versiones comprobadas, sin modificar ese archivo.

### Configurar el entorno

Copia `.env.example` a `.env` en la raíz, si este último aún no existe.

En PowerShell:

```powershell
Copy-Item .env.example .env
```

En Linux o macOS:

```bash
cp .env.example .env
```

Edita la copia local y configura `STORAGE_SECRET` con una cadena larga y aleatoria. Puedes generar una con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

No publiques la clave de almacenamiento ni las credenciales de OpenRouter. Los archivos `.env` reales están excluidos del control de versiones.

| Variable | Uso |
| --- | --- |
| `STORAGE_SECRET` | Secreto de almacenamiento de NiceGUI. Obligatorio cuando `SCALARIS_ENV=production`. |
| `SCALARIS_ENV` | Con el valor `production`, exige el secreto y habilita una caché de recursos estáticos de una hora. Fuera de producción, esa caché se configura a cero. |
| `OPENROUTER_API_KEY` | Credencial opcional para Glosa. |
| `OPENROUTER_PRIMARY_MODEL` | Identificador del modelo principal. Si la variable no existe, se usa el valor definido en `src/ai/constantes.py`; un valor vacío no activa ese respaldo. |
| `OPENROUTER_FALLBACK_MODELS` | Modelos de reserva separados por comas. |
| `SCALARIS_NAV` | Activa la navegación actualizada; habilitada por defecto. |
| `SCALARIS_DOCK` | Activa el panel lateral de Glosa; habilitado por defecto. |
| `SCALARIS_PROACTIVE` | Activa las sugerencias proactivas; habilitadas por defecto. |

Las tres banderas aceptan `1/0`, `true/false`, `on/off` y `yes/no`, sin distinguir mayúsculas. El arranque carga `.env` de la raíz y también admite `src/ai/.env`; las variables ya presentes en el entorno tienen prioridad.

La plantilla deja `OPENROUTER_PRIMARY_MODEL=` vacío. Para habilitar Glosa, configura la clave y un identificador de modelo válido, o elimina esa línea si quieres utilizar el modelo predeterminado. Dejarla vacía no equivale a omitirla.

### Iniciar Scalaris

Desde la raíz del repositorio y con el entorno activado:

```bash
python -m src.main
```

También se admite `python src/main.py`. Abre la dirección que indique NiceGUI en la terminal, normalmente `http://localhost:8080`, y detén el servidor con `Ctrl+C`.

El punto de entrada carga la configuración y delega en [la aplicación frontend](src/frontend/aplicacion.py), que registra las rutas y los recursos estáticos. La carpeta de recursos se sirve bajo `/assets`.

## Estructura del proyecto

```text
src/
  main.py                  Punto de entrada
  backend/
    modelos/               Representaciones matemáticas
    resolutores/           Sistemas, matrices, vectores y utilidades numéricas
    geometria/             Cálculo y datos para escenas geométricas
    utilidades/            Validación, formato y funciones compartidas
    constantes.py          Límites y tolerancias del dominio
  frontend/
    aplicacion.py          Arranque de NiceGUI
    rutas.py               Registro de páginas
    navegacion/            Catálogo, consultas y redirecciones
    vistas/                Composición de las herramientas
    controladores/         Adaptación entre interfaz y dominio
    componentes/           Captura, selectores, resultados y Glosa
    recursos/              CSS, JavaScript, plantillas e imágenes
  ai/                      Cliente de OpenRouter, contexto y respuestas
tests/                     Pruebas Python y JavaScript
pytest.ini                 Configuración de descubrimiento de pruebas
requirements.txt           Declaración de dependencias con la salvedad indicada
.env.example               Plantilla de configuración sin credenciales
```

El dominio matemático no depende de NiceGUI. Los controladores adaptan las entradas y las respuestas; las vistas montan la interfaz con componentes compartidos. El catálogo vigente de herramientas y rutas está en [navegación](src/frontend/navegacion/catalogo.py).

## Verificación

Con el entorno activado, ejecuta la suite completa desde la raíz:

```bash
python -m pytest -q
```

La configuración descubre `tests/test_*.py`. Una prueba de integración ejecuta también los archivos `tests/test_*.js` con el ejecutor nativo de Node.js. Algunas comprobaciones de JavaScript usan `--expose-internals`, por lo que se recomienda el entorno de referencia indicado. No hace falta instalar paquetes de npm.

Para ejecutar un archivo de prueba concreto, indica su ruta a `python -m pytest`. Las comprobaciones cubren algoritmos, aritmética exacta, contratos de controladores, captura, ciclo de vida de las vistas y comportamiento de scripts de cliente. Algunas pruebas construyen componentes NiceGUI con el transporte simulado; no equivalen a una prueba visual en un navegador.

Para comprobar además la compilación de los módulos Python:

```bash
python -m compileall -q src tests
```

La revisión visual debe incluir los tres temas, una ventana de 320 píxeles de ancho, zoom al 200 %, navegación con teclado y movimiento reducido. Comprueba las cuatro operaciones de Vectores, los dos métodos de Determinantes y las tres escenas del visualizador; revisa que las fórmulas y tablas se puedan desplazar sin ocultar controles.

## Participantes

- Steven Cuadra
- Carlos Rodriguez
- Roger Sequeira
