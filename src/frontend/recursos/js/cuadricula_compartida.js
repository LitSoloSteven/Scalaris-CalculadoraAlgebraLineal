/** Animación y foco compartidos por las celdas de captura. */
'use strict';

{
  window.scalaris = window.scalaris || {};
  const FOTOGRAMAS_ENTRADA = [
    { opacity: 0, transform: 'scale(0.95) translateY(4px)' },
    { opacity: 1, transform: 'scale(1) translateY(0)' }
  ];
  const FOTOGRAMAS_SALIDA = [
    { opacity: 1, transform: 'scale(1) translateY(0)' },
    { opacity: 0, transform: 'scale(0.95) translateY(-4px)' }
  ];
  const avisosActivos = new WeakMap();
  const animacionesActivas = new WeakMap();

  /** Consulta la política compartida de teclado y movimiento reducido. */
  function movimientoActivo() {
    return window.scalaris.movimiento.permitido();
  }

  /** Retira únicamente animaciones de captura para devolver las celdas a su estado visible. */
  function restaurarCeldas(elementos) {
    Array.from(elementos).forEach(entrada => {
      const control = entrada.closest('.q-field__control');
      animacionesActivas.get(control)?.cancel?.();
      animacionesActivas.delete(control);
    });
  }

  function retirarAnimacionesPropias(animaciones) {
    animaciones.forEach((animacion, control) => {
      if (animacionesActivas.get(control) !== animacion) return;
      animacion.cancel?.();
      animacionesActivas.delete(control);
    });
  }

  async function animarCeldas(elementos, fotogramas, duracion) {
    restaurarCeldas(elementos);
    if (!movimientoActivo()) return;
    const controles = [...new Set(Array.from(elementos).map(entrada => entrada.closest('.q-field__control')).filter(Boolean))];
    const animaciones = new Map();
    const paso = Math.min(15, 120 / Math.max(controles.length, 1));
    try {
      controles.forEach((control, indice) => {
        const animacion = control.animate(fotogramas, {
          duration: duracion, delay: indice * paso,
          easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards'
        });
        animacionesActivas.set(control, animacion);
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
    return animarCeldas(elementos, FOTOGRAMAS_ENTRADA, 180);
  }

  /** Espera la salida de las celdas con una duración menor que la entrada. */
  function animarSalidaCeldas(elementos) {
    return animarCeldas(elementos, FOTOGRAMAS_SALIDA, 140);
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
