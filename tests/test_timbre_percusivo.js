'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { prepararSintesis } = require('./comun_sintesis_sonora.js');

test('los impactos resuelven el tono al inicio y apagan su cuerpo sin una cola sostenida', () => {
    const caso = prepararSintesis();
    caso.activar();
    const contexto = caso.contextos[0];
    const catalogo = caso.ventana.scalaris.catalogoSonidos;
    for (const [nombre, perfil] of Object.entries(catalogo.perfiles)) {
        const cantidad = contexto.nodos.length;
        comprobar.equal(caso.motor.reproducir(nombre), true, nombre);
        const nodos = contexto.nodos.slice(cantidad);
        for (const tono of nodos.filter(nodo => nodo.tipo === 'tono')) comprobarTono(tono, perfil, catalogo);
        nodos.forEach(nodo => nodo.onended?.());
        caso.avanzar(500);
    }
});

function comprobarTono(tono, perfil, catalogo) {
    const llegada = tono.frequency.valores[1][1] - tono.inicio;
    comprobar.ok(llegada > 0 && llegada <= catalogo.percusion.caidaTono + 1e-10);
    const envolvente = tono.destino.gain.valores;
    const apagado = envolvente.at(-1);
    comprobar.equal(apagado[0], 0);
    comprobar.ok(apagado[1] <= tono.fin);
    comprobar.ok(apagado[1] - tono.inicio <= (perfil.decaimiento ?? catalogo.percusion.decaimiento) + 1e-10);
}

test('el clic usa una banda resonante breve y conserva el pasa bajos maestro', () => {
    const caso = prepararSintesis();
    caso.activar();
    caso.motor.reproducir('escritura');
    const contexto = caso.contextos[0];
    const filtros = contexto.nodos.filter(nodo => nodo.tipo === 'filtro');
    const ruido = contexto.nodos.find(nodo => nodo.tipo === 'ruido');
    comprobar.equal(filtros[0].type, 'lowpass');
    comprobar.equal(filtros[0].frequency.valores[0][0], 2500);
    comprobar.equal(filtros[1].type, 'bandpass');
    comprobar.ok(filtros[1].Q.valores[0][0] > 1);
    comprobar.ok(Math.abs(ruido.fin - ruido.inicio - 0.006) < 1e-10);
    comprobar.equal(caso.ventana.scalaris.catalogoSonidos.ganancia, 0.45);
});

test('vuelo y papel conservan ruido audible durante toda su secuencia', () => {
    const caso = prepararSintesis();
    caso.activar();
    const contexto = caso.contextos[0];
    for (const nombre of ['limpiar_vuelo', 'exportar_inicio']) {
        const cantidad = contexto.nodos.length;
        caso.motor.reproducir(nombre);
        const nodos = contexto.nodos.slice(cantidad);
        const ruido = nodos.find(nodo => nodo.tipo === 'ruido');
        const perfil = caso.ventana.scalaris.catalogoSonidos.perfiles[nombre];
        comprobar.ok(Math.abs(ruido.fin - ruido.inicio - perfil.duracion) < 1e-10);
        comprobar.equal(ruido.destino.gain.valores.at(-1)[1], ruido.fin);
        nodos.forEach(nodo => nodo.onended?.());
        caso.avanzar(500);
    }
});
