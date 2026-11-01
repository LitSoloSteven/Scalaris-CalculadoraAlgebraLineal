'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { prepararSintesis } = require('./comun_sintesis_sonora.js');

test('las capas comparten ruido por contexto y liberan cada nodo al terminar', () => {
    const caso = prepararSintesis();
    caso.activar();
    const contexto = caso.contextos[0];
    for (const nombre of ['escritura', 'espacio', 'enter', 'borrado']) {
        comprobar.equal(caso.motor.reproducir(nombre), true);
        const nodos = contexto.nodos.slice(-5);
        const tono = nodos.find(nodo => nodo.tipo === 'tono');
        const ruido = nodos.find(nodo => nodo.tipo === 'ruido');
        comprobar.equal(tono.inicio, ruido.inicio);
        comprobar.equal(tono.fin, ruido.fin);
        comprobar.equal(nodos[0].type, 'lowpass');
        comprobar.equal(nodos[0].destino, contexto.destination);
        tono.onended();
        comprobar.ok(nodos.every(nodo => nodo.desconectado));
        comprobar.equal(ruido.onended, null);
        caso.avanzar(100);
    }
    comprobar.equal(contexto.buffers.length, 1);
    comprobar.equal(contexto.buffers[0].longitud, 7200);
});

test('un fallo en cualquier nodo limpia también las fuentes aún sin iniciar', () => {
    for (const fallar of ['filtro', 'tono', 'ruido', 'ganancia']) {
        const caso = prepararSintesis({ fallar });
        caso.activar();
        comprobar.equal(caso.motor.reproducir('accion'), false);
        comprobar.ok(caso.contextos[0].nodos.every(nodo => nodo.desconectado));
    }
});

test('cada perfil limita sus ráfagas sin frenar la cadencia de escritura', () => {
    const caso = prepararSintesis();
    caso.activar();
    comprobar.equal(caso.motor.reproducir('escritura'), true);
    caso.avanzar(27);
    comprobar.equal(caso.motor.reproducir('escritura'), false);
    caso.avanzar(1);
    comprobar.equal(caso.motor.reproducir('escritura'), true);
    caso.avanzar(28);
    comprobar.equal(caso.motor.reproducir('escritura'), false);
    caso.motor.silenciar(true);
    comprobar.ok(caso.contextos[0].nodos.every(nodo => nodo.desconectado));
    caso.motor.silenciar(false);
    caso.avanzar(100);
    comprobar.equal(caso.motor.reproducir('limpiar'), true);
    caso.avanzar(100);
    comprobar.equal(caso.motor.reproducir('limpiar'), false);
});

test('ocultar y abandonar la página detiene capas y exige un gesto nuevo al volver', () => {
    const caso = prepararSintesis();
    caso.documento.hidden = true;
    caso.activar();
    comprobar.equal(caso.contextos.length, 0);
    caso.documento.hidden = false;
    caso.activar();
    caso.motor.reproducir('entrada');
    caso.documento.hidden = true;
    caso.documento.emitir('visibilitychange');
    comprobar.ok(caso.contextos[0].nodos.every(nodo => nodo.desconectado));
    caso.ventana.emitir('pagehide');
    caso.ventana.navigator = { userActivation: { hasBeenActive: true } };
    caso.documento.hidden = false;
    comprobar.equal(caso.motor.reproducir('entrada'), false);
    caso.activar();
    comprobar.equal(caso.contextos.length, 2);
    comprobar.equal(caso.motor.reproducir('entrada'), true);
    comprobar.equal(caso.contextos[1].buffers.length, 1);
});
