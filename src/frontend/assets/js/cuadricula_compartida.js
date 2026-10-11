/**
 * Scalaris - Módulo compartido de interacción con cuadrículas y celdas
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  function movimientoActivo() {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return false;
    }
    if (document.documentElement.getAttribute('data-input') === 'keyboard') {
      return false;
    }
    return true;
  }

  function animarEntradaCeldas(elementos) {
    return new Promise(function (resolve) {
      if (!movimientoActivo()) {
        resolve();
        return;
      }
      var animaciones = [];
      elementos.forEach(function (input) {
        var control = input.closest('.q-field__control');
        if (control) {
          animaciones.push(
            control.animate(
              [
                { opacity: 0, transform: 'scale(0.95) translateY(4px)' },
                { opacity: 1, transform: 'scale(1) translateY(0)' }
              ],
              { duration: 180, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards' }
            ).finished
          );
        }
      });
      if (animaciones.length > 0) {
        Promise.all(animaciones).then(resolve).catch(resolve);
      } else {
        resolve();
      }
    });
  }

  function animarSalidaCeldas(elementos) {
    return new Promise(function (resolve) {
      if (!movimientoActivo()) {
        resolve();
        return;
      }
      var animaciones = [];
      elementos.forEach(function (input) {
        var control = input.closest('.q-field__control');
        if (control) {
          animaciones.push(
            control.animate(
              [
                { opacity: 1, transform: 'scale(1) translateY(0)' },
                { opacity: 0, transform: 'scale(0.95) translateY(-4px)' }
              ],
              { duration: 140, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards' }
            ).finished
          );
        }
      });
      if (animaciones.length > 0) {
        Promise.all(animaciones).then(resolve).catch(resolve);
      } else {
        resolve();
      }
    });
  }

  function sacudirCelda(idMatriz, fila, columna) {
    var selector = 'input[data-matrix-id="' + idMatriz + '"][data-matrix-row="' + fila + '"][data-matrix-col="' + columna + '"]';
    var input = document.querySelector(selector);
    if (!input) return;
    input.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
    input.focus();
    var contenedor = input.closest('.matrix-input');
    var control = input.closest('.q-field__control');
    if (contenedor) {
      contenedor.classList.remove('animate-shake');
      void contenedor.offsetWidth;
      contenedor.classList.add('animate-shake');
      contenedor.addEventListener('animationend', function () {
        contenedor.classList.remove('animate-shake');
      }, { once: true });
    }
    if (control) {
      control.style.outline = '2px solid var(--error)';
      setTimeout(function () { control.style.outline = ''; }, 1800);
    }
  }

  function enfocarElemento(id) {
    var el = document.getElementById(id);
    if (!el) return;
    var input = el.tagName === 'INPUT' ? el : (el.querySelector('input') || el);
    input.scrollIntoView({ block: 'center' });
    input.focus();
  }

  function animarSalidaMatriz(nombreMatriz, targetAttr) {
    var celdas = document.querySelectorAll("input[data-matrix-id='" + nombreMatriz + "']" + targetAttr);
    return animarSalidaCeldas(Array.from(celdas));
  }

  function animarEntradaMatriz(nombreMatriz, targetAttr) {
    var celdas = document.querySelectorAll("input[data-matrix-id='" + nombreMatriz + "']" + targetAttr);
    return animarEntradaCeldas(Array.from(celdas));
  }

  function animarSalidaVector(indice) {
    var celdas = document.querySelectorAll("input[data-geometria-indice='" + indice + "']");
    return animarSalidaCeldas(Array.from(celdas));
  }

  function animarEntradaVector(indice) {
    var celdas = document.querySelectorAll("input[data-geometria-indice='" + indice + "']");
    return animarEntradaCeldas(Array.from(celdas));
  }

  window.scalaris.cuadricula = {
    movimientoActivo: movimientoActivo,
    animarEntradaCeldas: animarEntradaCeldas,
    animarSalidaCeldas: animarSalidaCeldas,
    animarSalidaMatriz: animarSalidaMatriz,
    animarEntradaMatriz: animarEntradaMatriz,
    animarSalidaVector: animarSalidaVector,
    animarEntradaVector: animarEntradaVector,
    sacudirCelda: sacudirCelda,
    enfocarElemento: enfocarElemento
  };
})();
