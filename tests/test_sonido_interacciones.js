'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { readFileSync: leerArchivo } = require('node:fs');
const { runInNewContext: ejecutar } = require('node:vm');
const { superficie } = require('./comun_sonido_cliente.js');

function boton(tipo = 'accion') {
    const atributos = new Map([['aria-pressed', 'false']]);
    const iconos = ['activo', 'silenciado'].map(nombre => ({ hidden: nombre !== 'activo',
        getAttribute: () => nombre }));
    return {
        tipo, atributos, iconos,
        setAttribute: (clave, valor) => atributos.set(clave, valor),
        getAttribute: clave => atributos.get(clave),
        querySelectorAll: () => iconos,
        closest(selector) {
            if (selector.includes('data-sonido-control')) return tipo === 'silencio' ? this : null;
            if (selector === '[inert]') return this.inerte ? this : null;
            return this;
        },
        matches(selector) {
            if (selector.includes(':disabled')) return this.disabled || atributos.get('aria-disabled') === 'true';
            return { '.inicio-fila': 'apertura', '.inicio-dialogo-cerrar': 'cierre',
                'a[href], [href]': 'navegacion' }[selector] === tipo;
        }
    };
}

function preparar(valor = null, bloquear = false) {
    const documento = superficie();
    const ventana = superficie();
    const botones = [boton('silencio')];
    const sonidos = [];
    const estados = [];
    const observadores = [];
    const almacen = new Map(valor === null ? [] : [['scalaris:sonido-silenciado', valor]]);
    documento.documentElement = {};
    documento.querySelectorAll = () => botones;
    documento.querySelector = () => documento.dialogoAbierto ? {} : null;
    ventana.scalaris = { sonido: { reproducir: nombre => sonidos.push(nombre),
        silenciar: estado => estados.push(estado) } };
    const entorno = { window: ventana, document: documento,
        localStorage: {
            getItem(clave) { if (bloquear) throw new Error('Bloqueado'); return almacen.get(clave); },
            setItem(clave, dato) { if (bloquear) throw new Error('Bloqueado'); almacen.set(clave, dato); }
        },
        MutationObserver: class {
            constructor(funcion) { this.funcion = funcion; observadores.push(this); }
            observe() {}
            disconnect() { this.desconectado = true; }
        } };
    const cargar = nombre => ejecutar(leerArchivo(`src/frontend/recursos/js/${nombre}.js`, 'utf8'), entorno);
    cargar('catalogo_sonidos');
    cargar('preferencia_sonido');
    cargar('interacciones_sonoras');
    const pulsar = (control, opciones = {}) => documento.emitir('click', {
        isTrusted: true, button: 0, target: control, ...opciones
    });
    return { documento, ventana, botones, sonidos, estados, observadores, almacen, cargar, pulsar };
}

test('el silencio persiste y actualiza controles dinámicos e iconos sin emitir audio', () => {
    const caso = preparar('true');
    const control = caso.botones[0];
    comprobar.equal(control.atributos.get('aria-pressed'), 'true');
    comprobar.equal(control.iconos[0].hidden, true);
    comprobar.equal(control.iconos[1].hidden, false);
    caso.botones.push(boton('silencio'));
    caso.observadores[0].funcion();
    comprobar.equal(caso.botones[1].atributos.get('aria-pressed'), 'true');
    caso.pulsar(control);
    comprobar.equal(caso.almacen.get('scalaris:sonido-silenciado'), 'false');
    comprobar.equal(control.atributos.get('title'), 'Silenciar sonidos');
    comprobar.equal(control.atributos.get('aria-pressed'), 'false');
    comprobar.deepEqual(caso.sonidos, []);
    const recargado = preparar(caso.almacen.get('scalaris:sonido-silenciado'));
    comprobar.equal(recargado.estados.at(-1), false);
});

test('almacenamiento bloqueado conserva el control y sincroniza las pestañas', () => {
    const caso = preparar(null, true);
    comprobar.doesNotThrow(() => caso.pulsar(caso.botones[0]));
    comprobar.equal(caso.estados.at(-1), true);
    caso.ventana.emitir('pageshow');
    comprobar.equal(caso.estados.at(-1), true);
    caso.ventana.emitir('storage', { key: 'scalaris:sonido-silenciado', newValue: 'false' });
    comprobar.equal(caso.estados.at(-1), false);
    caso.ventana.emitir('storage', { key: 'otra', newValue: 'true' });
    comprobar.equal(caso.estados.at(-1), false);
    caso.ventana.emitir('storage', { key: null, newValue: null });
    comprobar.equal(caso.botones[0].atributos.get('aria-pressed'), 'false');
});

test('el control ignora eventos sintéticos, cancelados o deshabilitados', () => {
    const caso = preparar();
    const control = caso.botones[0];
    for (const opciones of [{ isTrusted: false }, { defaultPrevented: true }, { button: 1 }]) {
        caso.pulsar(control, opciones);
        comprobar.equal(control.atributos.get('aria-pressed'), 'false');
    }
    control.disabled = true;
    caso.pulsar(control);
    comprobar.equal(control.atributos.get('aria-pressed'), 'false');
});

test('una activación de puntero, táctil o teclado emite una sola categoría', () => {
    const caso = preparar();
    for (const tipo of ['accion', 'navegacion', 'apertura', 'cierre']) {
        const control = boton(tipo);
        caso.pulsar(control, { detail: 1 });
        caso.pulsar(control, { detail: 0 });
        comprobar.deepEqual(caso.sonidos.splice(0), [tipo, tipo]);
    }
    caso.pulsar(boton(), { pointerType: 'touch' });
    comprobar.deepEqual(caso.sonidos, ['accion']);
});

test('las ráfagas de teclado, controles inertes y navegación modificada no emiten', () => {
    const caso = preparar();
    const control = boton();
    for (const opciones of [{ isTrusted: false }, { defaultPrevented: true }, { button: 2 },
        { ctrlKey: true }, { metaKey: true }, { altKey: true }, { shiftKey: true }]) {
        caso.pulsar(control, opciones);
    }
    control.disabled = true;
    caso.pulsar(control);
    control.disabled = false;
    control.inerte = true;
    caso.pulsar(control);
    caso.documento.emitir('keydown', { isTrusted: true, key: 'a' });
    caso.documento.emitir('click', { isTrusted: true, button: 0, target: {} });
    comprobar.deepEqual(caso.sonidos, []);
});

test('Escape solo suena en un diálogo abierto y no se repite', () => {
    const caso = preparar();
    caso.documento.emitir('keydown', { isTrusted: true, key: 'Escape' });
    comprobar.deepEqual(caso.sonidos, []);
    caso.documento.dialogoAbierto = true;
    caso.documento.emitir('keydown', { isTrusted: true, key: 'Escape', repeat: true });
    caso.documento.emitir('keydown', { isTrusted: false, key: 'Escape' });
    comprobar.deepEqual(caso.sonidos, []);
    caso.documento.emitir('keydown', { isTrusted: true, key: 'Escape' });
    comprobar.deepEqual(caso.sonidos, ['cierre']);
});

test('recargar y destruir retira listeners y observadores anteriores', () => {
    const caso = preparar();
    caso.cargar('preferencia_sonido');
    caso.cargar('interacciones_sonoras');
    comprobar.equal(caso.documento.contar('click'), 2);
    comprobar.equal(caso.observadores[0].desconectado, true);
    caso.pulsar(boton());
    comprobar.deepEqual(caso.sonidos, ['accion']);
    caso.ventana.scalaris.preferenciaSonido.destruir();
    caso.ventana.scalaris.interaccionesSonoras.destruir();
    comprobar.equal(caso.documento.contar('click'), 0);
    comprobar.equal(caso.documento.contar('keydown'), 0);
    comprobar.equal(caso.ventana.contar('storage'), 0);
    comprobar.equal(caso.ventana.contar('pageshow'), 0);
    comprobar.equal(caso.observadores.at(-1).desconectado, true);
});
