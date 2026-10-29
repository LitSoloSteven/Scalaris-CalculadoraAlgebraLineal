/** Animación y foco compartidos por las celdas de captura. */
'use strict';

{
  window.scalaris = window.scalaris || {};
  const FOTOGRAMAS_ENTRADA = [
    { opacity: 0, transform: 'scale(0.95) translateY(16px)' },
    { opacity: 1, transform: 'scale(1) translateY(0)' }
  ];
  const FOTOGRAMAS_SALIDA = [
    { opacity: 1, transform: 'scale(1) translateY(0)' },
    { opacity: 0, transform: 'scale(0.95) translateY(16px)' }
  ];
  const avisosActivos = new WeakMap();
  const animacionesActivas = new WeakMap();
  const capasPorEntrada = new WeakMap();

  /** Consulta la política compartida de teclado y movimiento reducido. */
  function movimientoActivo() {
    return window.scalaris.movimiento.permitido();
  }

  /** Retira únicamente animaciones de captura para devolver las celdas a su estado visible. */
  function restaurarCeldas(elementos) {
    Array.from(elementos).forEach(entrada => {
      const control = capasPorEntrada.get(entrada) || entrada.closest('.q-field__control');
      if (!control) return;
      animacionesActivas.get(control)?.cancel?.();
      animacionesActivas.delete(control);
      capasPorEntrada.delete(entrada);
    });
  }

  function retirarAnimacionesPropias(animaciones) {
    animaciones.forEach((animacion, control) => {
      if (animacionesActivas.get(control) !== animacion) return;
      animacion.cancel?.();
      animacionesActivas.delete(control);
    });
  }

  function seleccionarCapas(entradas) {
    if (!entradas.length) return [];
    const seleccionadas = new Set(entradas);
    const filas = new Set(entradas.map(entrada => entrada.closest('[data-cuadricula-fila], .q-row[data-matriz-fila]')));
    const filasCompletas = [...filas].filter(fila => fila?.querySelectorAll &&
      Array.from(fila.querySelectorAll('input')).every(entrada => seleccionadas.has(entrada)));
    if (filasCompletas.length > 10) return [];
    const controles = entradas.filter(entrada => !filasCompletas.some(fila => fila.contains(entrada)))
      .map(entrada => entrada.closest('.q-field__control')).filter(Boolean);
    return [...filasCompletas, ...new Set(controles)].slice(0, 10);
  }

  async function animarCeldas(elementos, fotogramas, tokenDuracion) {
    restaurarCeldas(elementos);
    if (!movimientoActivo()) return;
    const entradas = Array.from(elementos);
    const controles = seleccionarCapas(entradas);
    const animaciones = new Map();
    const movimiento = window.scalaris.movimiento;
    try {
      controles.forEach(control => {
        const animacion = control.animate(fotogramas, {
          duration: movimiento.duracion(tokenDuracion), easing: movimiento.curva(), fill: 'forwards'
        });
        animacionesActivas.set(control, animacion);
        entradas.forEach(entrada => { if (control === entrada.closest('.q-field__control') || control.contains?.(entrada)) capasPorEntrada.set(entrada, control); });
        animacion.finished.catch(() => {});
        animaciones.set(control, animacion);
      });
      await Promise.all([...animaciones.values()].map(animacion => animacion.finished));
      if (fotogramas === FOTOGRAMAS_ENTRADA) retirarAnimacionesPropias(animaciones);
    } catch (_) {
      retirarAnimacionesPropias(animaciones);
    }
  }

  /** Espera la entrada de todas las celdas que tienen un control visual. */
  function animarEntradaCeldas(elementos) {
    return animarCeldas(elementos, FOTOGRAMAS_ENTRADA, '--dur-panel');
  }

  /** Espera la salida de las celdas con una duración menor que la entrada. */
  function animarSalidaCeldas(elementos) {
    return animarCeldas(elementos, FOTOGRAMAS_SALIDA, '--dur-panel-exit');
  }

  function animarAvisoCelda(contenedor) {
    contenedor.classList.remove('movimiento-sacudida');
    void contenedor.offsetWidth;
    contenedor.classList.add('movimiento-sacudida');
    contenedor.addEventListener('animationend', function retirarAviso() {
      contenedor.classList.remove('movimiento-sacudida');
    }, { once: true });
  }

  function marcarErrorControl(control) {
    const aviso = {};
    avisosActivos.set(control, aviso);
    control.classList.add('cuadricula-error');
    setTimeout(function retirarError() {
      if (avisosActivos.get(control) !== aviso) return;
      control.classList.remove('cuadricula-error');
      avisosActivos.delete(control);
    }, 1800);
  }

  /** Enfoca la celda inválida y mantiene una señal temporal independiente del movimiento. */
  function sacudirCelda(identificadorMatriz, fila, columna) {
    const selector = 'input[data-matriz-identificador="' + identificadorMatriz + '"][data-matriz-fila="' + fila + '"][data-matriz-columna="' + columna + '"]';
    const entrada = document.querySelector(selector);
    if (!entrada) return;
    const permitirMovimiento = movimientoActivo();
    entrada.scrollIntoView({ block: 'center', inline: 'center', behavior: permitirMovimiento ? 'smooth' : 'auto' });
    entrada.focus();
    const contenedor = entrada.closest('.matriz-entrada');
    const control = entrada.closest('.q-field__control');
    if (contenedor && permitirMovimiento) animarAvisoCelda(contenedor);
    if (control) marcarErrorControl(control);
  }

  /** Enfoca la entrada del elemento indicado o el propio elemento cuando carece de ella. */
  function enfocarElemento(identificador) {
    const elemento = document.getElementById(identificador);
    if (!elemento) return;
    const entrada = elemento.tagName === 'INPUT' ? elemento : (elemento.querySelector('input') || elemento);
    entrada.scrollIntoView({ block: 'center' });
    entrada.focus();
  }

  /** Espera la salida de las celdas seleccionadas de una matriz. */
  function animarSalidaMatriz(nombreMatriz, atributoDestino) {
    const celdas = document.querySelectorAll("input[data-matriz-identificador='" + nombreMatriz + "']" + atributoDestino);
    return animarSalidaCeldas(Array.from(celdas));
  }

  /** Espera la entrada de las celdas seleccionadas de una matriz. */
  function animarEntradaMatriz(nombreMatriz, atributoDestino) {
    const celdas = document.querySelectorAll("input[data-matriz-identificador='" + nombreMatriz + "']" + atributoDestino);
    return animarEntradaCeldas(Array.from(celdas));
  }

  /** Espera la salida de las celdas del vector indicado. */
  function animarSalidaVector(indice) {
    const celdas = document.querySelectorAll("input[data-geometria-indice='" + indice + "']");
    return animarSalidaCeldas(Array.from(celdas));
  }

  /** Espera la entrada de las celdas del vector indicado. */
  function animarEntradaVector(indice) {
    const celdas = document.querySelectorAll("input[data-geometria-indice='" + indice + "']");
    return animarEntradaCeldas(Array.from(celdas));
  }

  window.scalaris.cuadricula = {
    movimientoActivo, animarEntradaCeldas, animarSalidaCeldas,
    animarSalidaMatriz, animarEntradaMatriz, animarSalidaVector, animarEntradaVector,
    sacudirCelda, enfocarElemento, restaurarCeldas
  };
}
