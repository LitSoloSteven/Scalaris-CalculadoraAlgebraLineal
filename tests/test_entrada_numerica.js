'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
const { crearClienteNumerico, crearCeldaNumerica, insertar } = require('./comun_entrada_numerica.js');

prueba('beforeinput conserva caracteres admitidos y bloquea letras antes de cambiar el valor', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente, '12');
    afirmar.equal(insertar(cliente, entrada, '+-./0123456789').bloqueado, false);
    afirmar.equal(insertar(cliente, entrada, 'e').bloqueado, true);
    afirmar.equal(entrada.value, '12');
    const aviso = cliente.elementos.get('captura-aviso-numerico');
    afirmar.equal(aviso.textContent, cliente.configuracion.mensaje);
    afirmar.equal(aviso.atributos.get('role'), 'status');
    afirmar.equal(aviso.atributos.get('aria-live'), 'polite');
    afirmar.equal(aviso.atributos.get('aria-atomic'), 'true');
});

prueba('el rechazo de teclado cancela y reinicia sin apilar animaciones', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente);
    insertar(cliente, entrada, 'a');
    insertar(cliente, entrada, 'b');
    afirmar.equal(entrada.superficie.llamadas.filter(nombre => nombre === 'reproducir:sacudida').length, 2);
    afirmar.equal(entrada.superficie.llamadas.filter(nombre => nombre === 'cancelar:sacudida').length, 2);
});

prueba('movimiento reducido usa únicamente la variante de opacidad', () => {
    const cliente = crearClienteNumerico({ reducido: true }), entrada = crearCeldaNumerica(cliente);
    insertar(cliente, entrada, 'a');
    afirmar.equal(entrada.superficie.clases.has('movimiento-sacudida'), false);
    afirmar.equal(entrada.superficie.clases.has('captura-rechazo-reducido'), true);
    afirmar.deepEqual(entrada.superficie.llamadas,
        ['cancelar:rechazoNumericoOpacidad', 'reproducir:rechazoNumericoOpacidad']);
});

prueba('pegados, arrastres y cargas sin confianza no disparan la sacudida', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente);
    for (const inputType of ['insertFromPaste', 'insertFromDrop']) {
        afirmar.equal(insertar(cliente, entrada, '<1>', { inputType }).bloqueado, true);
    }
    insertar(cliente, entrada, 'a', { isTrusted: false });
    afirmar.deepEqual(entrada.superficie.llamadas, []);
});

prueba('el fallback sanea antes del transporte y conserva selección y dirección', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente, 'a1\uD83D\uDE002b/3');
    entrada.selectionStart = 2; entrada.selectionEnd = 6; entrada.selectionDirection = 'backward';
    cliente.emitir('input', { target: entrada, isTrusted: false });
    afirmar.equal(entrada.value, '12/3');
    afirmar.equal(entrada.selectionStart, 1);
    afirmar.equal(entrada.selectionEnd, 2);
    afirmar.equal(entrada.selectionDirection, 'backward');
    afirmar.equal(entrada.publicados.length, 0);
    afirmar.equal([...cliente.eventos.get('input').values()][0].capture, true);
});

prueba('la composición se conserva hasta terminar y publica entonces el valor saneado', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente, '1あ2');
    cliente.emitir('compositionstart', { target: entrada });
    afirmar.equal(insertar(cliente, entrada, 'あ').bloqueado, false);
    cliente.emitir('input', { target: entrada, isComposing: true });
    afirmar.equal(entrada.value, '1あ2');
    cliente.emitir('compositionend', { target: entrada, isTrusted: true });
    afirmar.equal(entrada.value, '12');
    afirmar.equal(entrada.publicados.length, 1);
    afirmar.deepEqual(entrada.superficie.llamadas, []);
});

prueba('texto libre y nombres quedan fuera de filtro y adaptadores de pegado', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente, 'Sector Épsilon 2', false);
    afirmar.equal(insertar(cliente, entrada, 'α').bloqueado, false);
    cliente.emitir('input', { target: entrada, isTrusted: true });
    afirmar.equal(entrada.value, 'Sector Épsilon 2');
    afirmar.equal(cliente.ventana.scalaris.capturaCeldas.perteneceCaptura(entrada, { tipo: 'matrices' }), false);
});

prueba('asignarCelda filtra cada pegado y comunica un único cambio sin animar', () => {
    const cliente = crearClienteNumerico(), entrada = crearCeldaNumerica(cliente);
    cliente.documento.querySelector = () => entrada;
    const configuracion = { tipo: 'matrices', atributos: { fila: 'matrizFila', columna: 'matrizColumna' } };
    cliente.ventana.scalaris.capturaCeldas.asignarCelda({ fila: 0, columna: 0 }, configuracion, ' a-1/2字 ');
    afirmar.equal(entrada.value, '-1/2');
    afirmar.equal(entrada.publicados.length, 1);
    afirmar.deepEqual(entrada.superficie.llamadas, []);
});

prueba('falta de configuración conserva el texto y registrar de nuevo no duplica listeners', () => {
    const cliente = crearClienteNumerico({ sinConfiguracion: true }), entrada = crearCeldaNumerica(cliente, 'A');
    cliente.emitir('input', { target: entrada });
    afirmar.equal(entrada.value, 'A');
    cargarAssetCliente('entrada_numerica.js', cliente.contexto);
    for (const nombre of ['beforeinput', 'input', 'compositionstart', 'compositionend']) {
        afirmar.equal(cliente.eventos.get(nombre).size, 1);
    }
});
