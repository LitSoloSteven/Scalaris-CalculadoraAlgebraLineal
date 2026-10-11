/* Los cuadros ya calculados cambian sin eventos de servidor ni animación. */
(function () {
  'use strict';
  window.scalaris = window.scalaris || {};
  window.scalaris.geometria?.limpiar();
  const registro = new Map();
  const celdasInvalidas = new Set();

  function registrar(identificador, cuadros) {
    const anterior = registro.get(identificador);
    if (anterior?.solicitud) cancelAnimationFrame(anterior.solicitud);
    const montada = Boolean(document.getElementById(identificador));
    registro.set(identificador, { cuadros, elemento: null, solicitud: null, revision: 0, montada });
  }

  function obtenerGrafica(identificador, entrada) {
    if (entrada.elemento?.isConnected) return entrada.elemento;
    entrada.elemento = document.getElementById(identificador)?.querySelector('.js-plotly-plot');
    return entrada.elemento;
  }

  function actualizarDosDimensiones(elemento, cuadro, etiqueta) {
    const vector = cuadro.ku;
    const suma = cuadro.ku_plus_v;
    return window.Plotly.restyle(elemento, {
      x: [[0, vector[0]], [0, suma[0]]],
      y: [[0, vector[1]], [0, suma[1]]],
      name: ['k·u (k=' + etiqueta + ')', 'k·u + v']
    }, [0, 2]);
  }

  function actualizarTresDimensiones(elemento, cuadro, etiqueta) {
    const vector = cuadro.ku;
    const suma = cuadro.ku_plus_v;
    // Cada flecha tridimensional tiene una traza de línea y otra de punta.
    return Promise.all([
      window.Plotly.restyle(elemento, {
        x: [[0, vector[0]]], y: [[0, vector[1]]], z: [[0, vector[2]]], name: ['k·u (k=' + etiqueta + ')']
      }, [0]),
      window.Plotly.restyle(elemento, { x: [[vector[0]]], y: [[vector[1]]], z: [[vector[2]]] }, [1]),
      window.Plotly.restyle(elemento, {
        x: [[0, suma[0]]], y: [[0, suma[1]]], z: [[0, suma[2]]], name: ['k·u + v']
      }, [4]),
      window.Plotly.restyle(elemento, { x: [[suma[0]]], y: [[suma[1]]], z: [[suma[2]]] }, [5])
    ]);
  }

  function establecerCuadro(identificador, indice) {
    const entrada = registro.get(identificador);
    const cuadro = entrada?.cuadros?.[indice];
    if (!window.Plotly || !cuadro) return;
    const elemento = obtenerGrafica(identificador, entrada);
    if (!elemento) return;
    const etiqueta = cuadro.k_exact || String(cuadro.k);
    const actualizar = cuadro.ku.length === 2 ? actualizarDosDimensiones : actualizarTresDimensiones;
    const revision = ++entrada.revision;
    try {
      Promise.resolve(actualizar(elemento, cuadro, etiqueta)).then(
        () => mostrarErrorCuadro(identificador, entrada, revision, ''),
        () => mostrarErrorCuadro(identificador, entrada, revision)
      );
    } catch (error) {
      mostrarErrorCuadro(identificador, entrada, revision);
    }
  }

  function mostrarErrorCuadro(identificador, entrada, revision, mensaje = 'No pudimos actualizar el parámetro. Vuelve a mover el control.') {
    if (registro.get(identificador) !== entrada || entrada.revision !== revision) return;
    const aviso = document.getElementById('geometria-error-cuadro-' + identificador);
    if (aviso) aviso.textContent = mensaje;
  }

  function marcarInvalido(selector) {
    celdasInvalidas.forEach(elemento => {
      (elemento.closest('.q-field__control') || elemento).classList.remove('geometria-celda-error');
      elemento.removeAttribute('aria-invalid');
    });
    celdasInvalidas.clear();
    const elemento = selector ? document.querySelector(selector) : null;
    if (!elemento) return;
    (elemento.closest('.q-field__control') || elemento).classList.add('geometria-celda-error');
    elemento.setAttribute('aria-invalid', 'true');
    celdasInvalidas.add(elemento);
  }

  function enfocarCelda(selector) {
    const elemento = document.querySelector(selector);
    elemento?.focus();
    elemento?.scrollIntoView({ block: 'center', behavior: 'instant' });
  }

  function actualizarDeslizador(evento) {
    const entrada = evento.target;
    if (!entrada?.matches('input[type="range"][data-geometria-deslizador]')) return;
    const identificador = entrada.getAttribute('data-geometria-deslizador');
    const indice = Number.parseInt(entrada.value, 10);
    const datos = registro.get(identificador);
    const cuadro = datos?.cuadros?.[indice];
    if (!cuadro) return;
    const etiqueta = cuadro.k_exact || String(cuadro.k);
    entrada.setAttribute('aria-valuetext', etiqueta);
    const texto = entrada.closest('.geometria-deslizador-fila')?.querySelector('.geometria-deslizador-valor');
    if (texto) texto.textContent = etiqueta;
    if (datos.solicitud) cancelAnimationFrame(datos.solicitud);
    datos.solicitud = requestAnimationFrame(() => {
      datos.solicitud = null;
      if (registro.get(identificador) !== datos) return;
      establecerCuadro(identificador, indice);
    });
  }

  function purgarFiguras() {
    registro.forEach((entrada, identificador) => {
      if (document.getElementById(identificador)) {
        entrada.montada = true;
        return;
      }
      if (!entrada.montada) return;
      if (entrada.solicitud) cancelAnimationFrame(entrada.solicitud);
      registro.delete(identificador);
    });
  }

  const observador = new MutationObserver(purgarFiguras);
  observador.observe(document.documentElement, { childList: true, subtree: true });
  document.addEventListener('input', actualizarDeslizador);

  function limpiar() {
    document.removeEventListener('input', actualizarDeslizador);
    observador.disconnect();
    registro.forEach(entrada => {
      if (entrada.solicitud) cancelAnimationFrame(entrada.solicitud);
    });
    registro.clear();
    marcarInvalido(null);
  }

  window.scalaris.geometria = { registrar, establecerCuadro, marcarInvalido, enfocarCelda, limpiar };
})();
