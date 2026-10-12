/** Edición de la celda matricial enfocada mediante el teclado numérico. */
'use strict';

{
  window.scalaris = window.scalaris || {};
  let ultimaEntradaEnfocada = null;

  document.addEventListener('focusin', function registrarEntradaEnfocada(evento) {
    const objetivo = evento.target;
    if (objetivo && objetivo.tagName === 'INPUT' && objetivo.closest('.matrix-input')) {
      ultimaEntradaEnfocada = objetivo;
    }
  });

  /** Inserta el símbolo en la última celda conectada o en la primera disponible. */
  function insertarSimbolo(simbolo) {
    if (!simbolo) return;
    let activa = ultimaEntradaEnfocada;
    if (!activa || !activa.isConnected) {
      activa = document.querySelector('.matrix-input input');
      if (!activa) return;
      activa.focus();
    }
    if (activa && activa.tagName === 'INPUT') {
      aplicarSimboloEnEntrada(activa, simbolo);
    }
  }

  function aplicarSimboloEnEntrada(entrada, simbolo) {
    if (simbolo === 'C') {
      entrada.value = '';
    } else if (simbolo === '±') {
      alternarSigno(entrada);
    } else if (simbolo === '⌫') {
      borrarCaracter(entrada);
    } else {
      insertarTextoEnCursor(entrada, simbolo);
    }
    entrada.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function alternarSigno(entrada) {
    const valor = entrada.value;
    if (valor.startsWith('-')) {
      entrada.value = valor.substring(1);
    } else if (valor.startsWith('+')) {
      entrada.value = '-' + valor.substring(1);
    } else if (valor.length > 0) {
      entrada.value = '-' + valor;
    }
    entrada.setSelectionRange(entrada.value.length, entrada.value.length);
  }

  function borrarCaracter(entrada) {
    const inicio = entrada.selectionStart;
    const fin = entrada.selectionEnd;
    const valor = entrada.value;
    if (inicio === fin && inicio > 0) {
      entrada.value = valor.substring(0, inicio - 1) + valor.substring(fin);
      entrada.setSelectionRange(inicio - 1, inicio - 1);
    } else if (inicio !== fin) {
      entrada.value = valor.substring(0, inicio) + valor.substring(fin);
      entrada.setSelectionRange(inicio, inicio);
    }
  }

  function insertarTextoEnCursor(entrada, texto) {
    const inicio = entrada.selectionStart;
    const fin = entrada.selectionEnd;
    const valor = entrada.value;
    entrada.value = valor.substring(0, inicio) + texto + valor.substring(fin);
    const nuevaPosicion = inicio + texto.length;
    entrada.setSelectionRange(nuevaPosicion, nuevaPosicion);
  }

  window.scalaris.calculadora = { insertarSimbolo };
}
