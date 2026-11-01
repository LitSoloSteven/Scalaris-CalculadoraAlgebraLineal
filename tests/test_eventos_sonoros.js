'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { readFileSync: leerArchivo } = require('node:fs');
const { runInNewContext: ejecutar } = require('node:vm');
const { superficie } = require('./comun_sonido_cliente.js');
const { inyectarCatalogo } = require('./comun_catalogo_sonoro.js');

function preparar() {
    const documento = superficie();
    inyectarCatalogo(documento);
    const sonidos = [];
    const ventana = { scalaris: { sonido: { reproducir: nombre => { sonidos.push(nombre); return true; } } } };
    const entorno = { window: ventana, document: documento };
    const cargar = nombre => ejecutar(leerArchivo(`src/frontend/recursos/js/${nombre}.js`, 'utf8'), entorno);
    ['catalogo_sonidos', 'eventos_sonoros'].forEach(cargar);
    return { documento, ventana, sonidos, cargar };
}

test('Glosa usa su evento para abrir cerrar y Escape sin depender del clic', () => {
    const caso = preparar();
    for (const abierto of [true, false, false]) caso.documento.emitir('scalaris:glosa', { detail: { abierto } });
    caso.documento.emitir('scalaris:glosa', { detail: {} });
    comprobar.deepEqual(caso.sonidos, ['glosa_abrir', 'glosa_cerrar', 'glosa_cerrar']);
    caso.cargar('eventos_sonoros');
    comprobar.equal(caso.documento.contar('scalaris:glosa'), 1);
    caso.ventana.scalaris.eventosSonoros.destruir();
    comprobar.equal(caso.documento.contar('scalaris:glosa'), 0);
});

test('el deslizador solo emite por valores distintos en gestos reales', () => {
    const caso = preparar();
    let valor = '0';
    const control = { getAttribute: () => valor, closest: () => null };
    const objetivo = { closest: () => control };
    const evento = { isTrusted: true, target: objetivo, buttons: 1 };
    caso.documento.emitir('pointermove', { ...evento, buttons: 0 });
    caso.documento.emitir('input', { ...evento, isTrusted: false });
    comprobar.deepEqual(caso.sonidos, []);
    caso.documento.emitir('pointermove', evento);
    caso.documento.emitir('pointerup', evento);
    valor = '1';
    caso.documento.emitir('keyup', { ...evento, key: 'ArrowRight' });
    caso.documento.emitir('input', evento);
    comprobar.deepEqual(caso.sonidos, ['deslizador', 'deslizador']);
    control.closest = () => ({});
    valor = '2';
    caso.documento.emitir('input', evento);
    comprobar.equal(caso.sonidos.length, 2);
});

test('rechazo y vuelo resuelven perfiles declarados y desmontan todos sus listeners', () => {
    const caso = preparar();
    comprobar.equal(caso.ventana.scalaris.eventosSonoros.rechazo(), true);
    comprobar.equal(caso.ventana.scalaris.eventosSonoros.limpiezaVuelo(), true);
    comprobar.deepEqual(caso.sonidos, ['rechazo', 'limpiar_vuelo']);
    caso.ventana.scalaris.eventosSonoros.destruir();
    for (const nombre of ['input', 'pointermove', 'pointerup', 'keyup']) {
        comprobar.equal(caso.documento.contar(nombre), 0);
    }
});
