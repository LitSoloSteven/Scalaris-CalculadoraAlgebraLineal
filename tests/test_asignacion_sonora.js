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
    const cargar = nombre => ejecutar(leerArchivo(`src/frontend/recursos/js/${nombre}.js`, 'utf8'), entorno);
    ['catalogo_sonidos', 'asignacion_sonora', 'interacciones_sonoras', 'sonido_escritura'].forEach(cargar);
    return { documento, ventana, sonidos, resolver: ventana.scalaris.asignacionSonora.resolver };
}

function control(atributos = {}, selectores = [], icono = '') {
    return { getAttribute: nombre => atributos[nombre] ?? null,
        matches: selector => selectores.includes(selector),
        querySelector: () => icono ? { textContent: icono } : null,
        closest: () => null };
}

function pulsar(caso, boton, datos = {}) {
    const objetivo = { closest: () => boton };
    caso.documento.emitir('click', { isTrusted: true, button: 0, target: objetivo, ...datos });
}

test('la prioridad es atributo valido, regla ordenada, icono y accion generica', () => {
    const caso = preparar();
    const reglas = ['[data-destino-matriz]', '.inicio-fila'];
    comprobar.equal(caso.resolver(control({ 'data-sonido': 'pegar' }, reglas, 'add')), 'pegar');
    comprobar.equal(caso.resolver(control({}, reglas, 'add')), 'transferencia');
    comprobar.equal(caso.resolver(control({}, [], 'add')), 'agregar');
    comprobar.equal(caso.resolver(control()), 'accion');
    for (const nombre of ['__proto__', 'constructor', '', 'inexistente']) {
        comprobar.equal(caso.resolver(control({ 'data-sonido': nombre }, reglas, 'add')), null);
    }
});

for (const [icono, esperado] of Object.entries({ calculate: 'calcular', remove: 'quitar',
    delete: 'eliminar', delete_sweep: 'limpiar', content_paste: 'pegar', play_arrow: 'reproducir',
    pause: 'pausa', first_page: 'primero', chevron_left: 'anterior', chevron_right: 'siguiente',
    last_page: 'ultimo', attach_file: 'adjuntar', help_outline: 'ayuda', sync: 'sincronizar', send: null })) {
    test(`el icono ${icono} resuelve su familia sin inspeccionar etiquetas`, () => {
        comprobar.equal(preparar().resolver(control({}, [], icono)), esperado);
    });
}

test('interruptores y paneles resuelven el estado anterior al cambio', () => {
    const caso = preparar();
    const interruptor = '.q-toggle, [role=switch], [role=checkbox]';
    comprobar.equal(caso.resolver(control({ 'aria-checked': 'false' }, [interruptor])), 'activar');
    comprobar.equal(caso.resolver(control({ 'aria-checked': 'true' }, [interruptor])), 'desactivar');
    comprobar.equal(caso.resolver(control({}, ['[data-glosa-cerrar], [data-glosa-alternar]'])), null);
    for (const cerrada of [true, false]) {
        const selector = '.q-expansion-item__container > .q-item[aria-expanded], .q-expansion-item__container > .q-item .q-item__section[aria-expanded]';
        const boton = control({ 'aria-expanded': String(!cerrada) }, [selector]);
        comprobar.equal(caso.resolver(boton), cerrada ? 'despliegue' : 'pliegue');
    }
});

test('los indices diferencian posiciones y acotan valores invalidos', () => {
    const caso = preparar();
    for (const [indice, esperado] of [['0', 'seleccion_0'], ['1', 'seleccion_1'], ['2', 'seleccion_2'],
        ['3', 'seleccion_3'], ['5', 'seleccion_1'], ['-1', 'seleccion_0'], ['NaN', 'seleccion_0'], ['Infinity', 'seleccion_0']]) {
        comprobar.equal(caso.resolver(control({ 'data-sonido-indice': indice }, ['[data-sonido-indice]'])), esperado);
    }
    const opciones = [control(), control(), control()];
    opciones[2].matches = selector => selector === '[role=option]';
    opciones[2].parentElement = { querySelectorAll: () => opciones };
    comprobar.equal(caso.resolver(opciones[2]), 'seleccion_2');
});

test('clic de teclado tactil o puntero emite una vez y respeta omisiones', () => {
    const caso = preparar();
    const boton = control({}, [], 'delete');
    for (const detail of [0, 1]) pulsar(caso, boton, { detail });
    comprobar.deepEqual(caso.sonidos.splice(0), ['eliminar', 'eliminar']);
    boton.closest = () => ({});
    pulsar(caso, boton);
    comprobar.deepEqual(caso.sonidos, []);
    boton.closest = () => null;
    pulsar(caso, control({}, [], 'send'));
    pulsar(caso, boton, { isTrusted: false });
    comprobar.deepEqual(caso.sonidos, []);
});

test('flechas del selector emiten la opcion destino y omiten su clic sintetico', () => {
    const caso = preparar();
    const opciones = [0, 1].map(indice => control({ 'data-sonido-indice': String(indice) }, ['[data-sonido-indice]']));
    const grupo = { querySelectorAll: () => opciones, closest: () => null };
    const objetivo = { closest: selector => selector === '.selector-opciones' ? grupo : opciones[0] };
    caso.documento.emitir('keydown', { isTrusted: true, key: 'ArrowRight', target: objetivo });
    pulsar(caso, opciones[1], { isTrusted: false });
    comprobar.deepEqual(caso.sonidos, ['seleccion_1']);
    caso.ventana.scalaris.interaccionesSonoras.destruir();
    comprobar.equal(caso.documento.contar('keydown'), 0);
});

test('escribir espacio Enter y borrar usa solo inputType y la comparacion de espacio', () => {
    const caso = preparar();
    const entrada = control({}, ['textarea']);
    Object.defineProperty(entrada, 'value', { get() { throw new Error('Lectura de contenido'); } });
    const casos = [['insertText', 'a', 'escritura'], ['insertText', ' ', 'espacio'],
        ['insertLineBreak', null, 'enter'], ['insertParagraph', null, 'enter'],
        ['deleteContentBackward', null, 'borrado'], ['deleteContentForward', null, 'borrado']];
    for (const [inputType, data, esperado] of casos) {
        caso.documento.emitir('input', { isTrusted: true, inputType, data, target: entrada });
        comprobar.equal(caso.sonidos.pop(), esperado);
    }
});

test('Quasar activa casillas interruptores y radios por keyup sin requerir clic DOM', () => {
    const caso = preparar();
    const regla = '.q-toggle, [role=switch], [role=checkbox]';
    for (const key of ['Enter', ' ']) {
        const boton = control({ 'aria-checked': 'false' }, [regla]);
        const objetivo = { closest: selector => selector.includes('.q-toggle') ? boton : null };
        caso.documento.emitir('keydown', { type: 'keydown', isTrusted: true, key, target: objetivo });
        caso.documento.emitir('keyup', { type: 'keyup', isTrusted: true, key, target: objetivo });
    }
    comprobar.deepEqual(caso.sonidos, ['activar', 'activar']);
    const opciones = [control(), control({}, ['[role=tab], [role=radio], .selector-opciones-opcion'])];
    opciones[1].parentElement = { querySelectorAll: () => opciones };
    const objetivo = { closest: () => opciones[1] };
    caso.documento.emitir('keyup', { type: 'keyup', isTrusted: true, key: ' ', target: objetivo });
    comprobar.equal(caso.sonidos.at(-1), 'seleccion_1');
    pulsar(caso, opciones[1]);
    comprobar.equal(caso.sonidos.at(-1), 'seleccion_1');
});

test('tabs Quasar activan con keydown y omiten controles deshabilitados', () => {
    const caso = preparar();
    const boton = control({ 'data-sonido-indice': '2' }, ['[data-sonido-indice]', '[role=tab]']);
    const objetivo = { closest: () => boton };
    caso.documento.emitir('keydown', { type: 'keydown', isTrusted: true, key: 'Enter', target: objetivo });
    caso.documento.emitir('keyup', { type: 'keyup', isTrusted: true, key: 'Enter', target: objetivo });
    comprobar.deepEqual(caso.sonidos, ['seleccion_2']);
    boton.matches = selector => selector.includes(':disabled');
    caso.documento.emitir('keydown', { type: 'keydown', isTrusted: true, key: 'Enter', target: objetivo });
    comprobar.equal(caso.sonidos.length, 1);
});

test('cabeceras y opciones QItem suenan por keyup y omiten su clic sintetico', () => {
    const caso = preparar();
    const regla = '.q-expansion-item__container > .q-item[aria-expanded], .q-expansion-item__container > .q-item .q-item__section[aria-expanded]';
    const cabecera = control({ 'aria-expanded': 'false' }, [regla]);
    const tema = control({}, ['[data-tema-opcion=marea]']);
    for (const boton of [cabecera, tema]) {
        const objetivo = { closest: () => boton };
        caso.documento.emitir('keyup', { type: 'keyup', isTrusted: true, key: 'Enter', target: objetivo });
        pulsar(caso, boton, { isTrusted: false });
    }
    comprobar.deepEqual(caso.sonidos, ['despliegue', 'tema_marea']);
});
