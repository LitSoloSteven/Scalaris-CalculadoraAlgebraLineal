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
    const ventana = { scalaris: { sonido: { reproducir: nombre => sonidos.push(nombre) } } };
    const entorno = { window: ventana, document: documento };
    for (const nombre of ['catalogo_sonidos', 'asignacion_sonora']) {
        ejecutar(leerArchivo(`src/frontend/recursos/js/${nombre}.js`, 'utf8'), entorno);
    }
    const cargar = () => ejecutar(leerArchivo('src/frontend/recursos/js/sonido_escritura.js', 'utf8'), entorno);
    cargar();
    return { documento, sonidos, ventana, cargar };
}

function campo(etiqueta = 'input', opciones = {}) {
    return { type: 'text', matches: selector => selector === etiqueta,
        closest: () => null, getAttribute: () => null, ...opciones };
}

function insertar(caso, entrada, opciones = {}) {
    caso.documento.emitir('input', { isTrusted: true, inputType: 'insertText', target: entrada, ...opciones });
}

test('las celdas, texto libre, números y contenido editable comparten una señal', () => {
    const caso = preparar();
    for (const entrada of [campo(), campo('textarea'), campo('input', { type: 'number' }),
        campo('div', { isContentEditable: true }), campo('input', { type: 'password' })]) {
        Object.defineProperty(entrada, 'value', { get() { throw new Error('No se debe leer el contenido'); } });
        insertar(caso, entrada);
    }
    comprobar.deepEqual(caso.sonidos, Array(5).fill('escritura'));
});

test('el borrado suena y los eventos inválidos o campos no editables se omiten', () => {
    const caso = preparar();
    for (const opciones of [{ isTrusted: false }, { inputType: 'deleteContentBackward' },
        { inputType: 'historyUndo' }, { inputType: undefined }, { isComposing: true }]) {
        insertar(caso, campo(), opciones);
    }
    for (const entrada of [campo('input', { disabled: true }), campo('textarea', { readOnly: true }),
        campo('input', { type: 'checkbox' }), campo('button'), campo('input', { closest: () => ({}) }),
        campo('input', { getAttribute: () => 'true' })]) insertar(caso, entrada);
    caso.documento.emitir('keydown', { isTrusted: true, key: 'ArrowDown', target: campo() });
    comprobar.deepEqual(caso.sonidos, ['borrado']);
});

test('pegar y soltar una tabla no generan una señal por cada celda programática', () => {
    const caso = preparar();
    insertar(caso, campo(), { inputType: 'insertFromPaste' });
    for (let indice = 0; indice < 100; indice++) insertar(caso, campo(), { isTrusted: false });
    insertar(caso, campo(), { inputType: 'insertFromDrop' });
    comprobar.deepEqual(caso.sonidos, ['escritura', 'escritura']);
});

test('composición confirma una señal al terminar e ignora preediciones y cancelación', () => {
    const caso = preparar();
    insertar(caso, campo(), { inputType: 'insertCompositionText', isComposing: true });
    caso.documento.emitir('compositionend', { isTrusted: true, data: '', target: campo() });
    caso.documento.emitir('compositionend', { isTrusted: false, data: 'a', target: campo() });
    comprobar.deepEqual(caso.sonidos, []);
    caso.documento.emitir('compositionend', { isTrusted: true, data: 'a', target: campo() });
    insertar(caso, campo(), { inputType: 'insertFromComposition' });
    comprobar.deepEqual(caso.sonidos, ['escritura']);
});

test('reinyectar y desmontar libera los listeners sin duplicar señales', () => {
    const caso = preparar();
    caso.cargar();
    comprobar.equal(caso.documento.contar('input'), 1);
    comprobar.equal(caso.documento.contar('compositionend'), 0);
    insertar(caso, campo());
    comprobar.deepEqual(caso.sonidos, ['escritura']);
    caso.ventana.scalaris.escrituraSonora.destruir();
    comprobar.equal(caso.documento.contar('input'), 0);
    comprobar.equal(caso.documento.contar('compositionend'), 0);
});
