/**
 * Scalaris - Controlador de botones del teclado numérico y calculadora
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  var ultimoInputEnfocado = null;

  document.addEventListener('focusin', function (evento) {
    var objetivo = evento.target;
    if (objetivo && objetivo.tagName === 'INPUT' && objetivo.closest('.matrix-input')) {
      ultimoInputEnfocado = objetivo;
    }
  });

  function insertarSimbolo(simbolo) {
    if (!simbolo) return;
    var activo = ultimoInputEnfocado;
    if (!activo || !activo.isConnected) {
      activo = document.querySelector('.matrix-input input');
      if (!activo) return;
      activo.focus();
    }
    if (activo && activo.tagName === 'INPUT') {
      aplicarSimboloEnInput(activo, simbolo);
    }
  }

  function aplicarSimboloEnInput(input, simbolo) {
    if (simbolo === 'C') {
      input.value = '';
    } else if (simbolo === '±') {
      alternarSigno(input);
    } else if (simbolo === '⌫') {
      borrarCaracter(input);
    } else {
      insertarTextoEnCursor(input, simbolo);
    }
    input.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function alternarSigno(input) {
    var valor = input.value;
    if (valor.startsWith('-')) {
      input.value = valor.substring(1);
    } else if (valor.startsWith('+')) {
      input.value = '-' + valor.substring(1);
    } else if (valor.length > 0) {
      input.value = '-' + valor;
    }
    input.setSelectionRange(input.value.length, input.value.length);
  }

  function borrarCaracter(input) {
    var inicio = input.selectionStart;
    var fin = input.selectionEnd;
    var valor = input.value;
    if (inicio === fin && inicio > 0) {
      input.value = valor.substring(0, inicio - 1) + valor.substring(fin);
      input.setSelectionRange(inicio - 1, inicio - 1);
    } else if (inicio !== fin) {
      input.value = valor.substring(0, inicio) + valor.substring(fin);
      input.setSelectionRange(inicio, inicio);
    }
  }

  function insertarTextoEnCursor(input, texto) {
    var inicio = input.selectionStart;
    var fin = input.selectionEnd;
    var valor = input.value;
    input.value = valor.substring(0, inicio) + texto + valor.substring(fin);
    var nuevaPos = inicio + texto.length;
    input.setSelectionRange(nuevaPos, nuevaPos);
  }

  window.scalaris.calculadora = {
    insertarSimbolo: insertarSimbolo
  };
})();
