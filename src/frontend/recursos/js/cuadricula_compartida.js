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

  /** Consulta la política compartida de teclado y movimiento reducido. */
  function movimientoActivo() {
    return window.scalaris.movimiento.permitido();
  }

  function animarCeldas(elementos, fotogramas, duracion) {
    return new Promise(function completarAnimaciones(terminar) {
      if (!movimientoActivo()) {
        terminar();
        return;
      }
      const animaciones = [];
      elementos.forEach(function animarControl(entrada) {
        const control = entrada.closest('.q-field__control');
        if (control) {
          animaciones.push(control.animate(fotogramas, {
            duration: duracion, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards'
          }).finished);
        }
      });
      if (animaciones.length > 0) Promise.all(animaciones).then(terminar).catch(terminar);
      else terminar();
    });
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
    sacudirCelda, enfocarElemento
  };
}
