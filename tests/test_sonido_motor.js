'use strict';
const { test } = require('node:test');
const comprobar = require('node:assert/strict');
const { readFileSync: leerArchivo } = require('node:fs');
const { runInNewContext: ejecutar } = require('node:vm');
const { superficie } = require('./comun_sonido_cliente.js');
const { inyectarCatalogo } = require('./comun_catalogo_sonoro.js');

function crearCapasAudio(parametro) {
    return {
        createBiquadFilter() { return { frequency: parametro(), Q: parametro(), connect() {}, disconnect() {} }; },
        createBuffer() { return { getChannelData: () => new Float32Array(100) }; },
        createBufferSource() {
            const nodo = { connect() {}, disconnect() {}, start(inicio) { this.inicio = inicio; }, stop(fin) { this.fin = fin; } };
            this.ruidos.push(nodo);
            return nodo;
        },
        sampleRate: 48000 };
}

function crearConstructorAudio(opciones, contextos) {
    const parametro = () => ({ setValueAtTime() {}, exponentialRampToValueAtTime() {},
        linearRampToValueAtTime() {} });
    return class {
        constructor() {
            if (opciones.fallaConstructor) throw new Error('Audio bloqueado');
            this.state = opciones.suspendido ? 'suspended' : 'running';
            this.currentTime = 4;
            this.destination = {};
            this.nodos = [];
            this.ruidos = [];
            Object.assign(this, crearCapasAudio(parametro));
            contextos.push(this);
        }
        resume() {
            if (opciones.rechazarReanudacion) return Promise.reject(new Error('Sin permiso'));
            this.state = 'running';
            return Promise.resolve();
        }
        close() { this.state = 'closed'; return Promise.resolve(); }
        createOscillator() {
            const nodo = { frequency: parametro(), conectado: false, desconectado: false,
                connect() { this.conectado = true; },
                disconnect() { this.desconectado = true; },
                start(inicio) { this.inicio = inicio; },
                stop(fin) { this.fin = fin; } };
            this.nodos.push(nodo);
            return nodo;
        }
        createGain() {
            if (opciones.fallaGanancia) throw new Error('Sin nodo');
            return { gain: parametro(), connect() {}, disconnect() {} };
        }
    };
}

function preparar(opciones = {}) {
    const documento = superficie();
    inyectarCatalogo(documento, opciones.polifonia ? { polifonia: opciones.polifonia } : {});
    const ventana = superficie();
    const contextos = [];
    let ahora = 0;
    ventana.AudioContext = crearConstructorAudio(opciones, contextos);
    if (opciones.sinAudio) delete ventana.AudioContext;
    const entorno = { window: ventana, document: documento, performance: { now: () => ahora } };
    const cargar = nombre => ejecutar(leerArchivo(`src/frontend/recursos/js/${nombre}.js`, 'utf8'), entorno);
    cargar('catalogo_sonidos');
    cargar('sintesis_sonora');
    cargar('sonido');
    return { documento, ventana, contextos, cargar, avanzar: cantidad => { ahora += cantidad; },
        motor: ventana.scalaris.sonido,
        activar: () => documento.emitir('pointerdown', { isTrusted: true }) };
}

test('solo un gesto real habilita sonidos y no reproduce avisos pendientes', () => {
    const caso = preparar();
    comprobar.equal(caso.motor.reproducir('exito'), false);
    caso.documento.emitir('pointerdown', { isTrusted: false });
    comprobar.equal(caso.contextos.length, 0);
    caso.activar();
    comprobar.equal(caso.contextos[0].nodos.length, 0);
    comprobar.equal(caso.motor.reproducir('exito'), true);
    caso.activar();
    comprobar.equal(caso.contextos.length, 1);
});

test('teclado real permite audio sin aceptar repeticiones', () => {
    const caso = preparar();
    caso.documento.emitir('keydown', { isTrusted: true, repeat: true });
    comprobar.equal(caso.contextos.length, 0);
    caso.documento.emitir('keydown', { isTrusted: true, repeat: false });
    comprobar.equal(caso.motor.reproducir('accion'), true);
});

test('el intervalo global y la polifonía descartan ráfagas sin encolarlas', () => {
    const caso = preparar({ polifonia: 2 });
    caso.activar();
    comprobar.equal(caso.motor.reproducir('error'), true);
    caso.avanzar(89);
    comprobar.equal(caso.motor.reproducir('accion'), false);
    caso.avanzar(1);
    comprobar.equal(caso.motor.reproducir('exito'), true);
    caso.avanzar(90);
    comprobar.equal(caso.motor.reproducir('aviso'), false);
    const nodo = caso.contextos[0].nodos[0];
    nodo.onended();
    caso.contextos[0].ruidos[0].onended();
    comprobar.equal(nodo.desconectado, true);
    comprobar.equal(caso.motor.reproducir('aviso'), true);
});

test('los perfiles son breves, suaves e inmutables y rechazan claves heredadas', () => {
    const caso = preparar();
    const catalogo = caso.ventana.scalaris.catalogoSonidos;
    comprobar.equal(Object.isFrozen(catalogo), true);
    comprobar.ok(catalogo.ganancia <= 0.45);
    caso.activar();
    for (const nombre of ['__proto__', 'constructor', 'desconocido']) {
        comprobar.equal(caso.motor.reproducir(nombre), false);
    }
    for (const [nombre, perfil] of Object.entries(catalogo.perfiles)) {
        comprobar.ok(perfil.duracion <= 0.4);
        comprobar.equal(Object.isFrozen(perfil), true);
        comprobar.equal(caso.motor.reproducir(nombre), true);
        const fuentes = [...caso.contextos[0].nodos, ...caso.contextos[0].ruidos].filter(fuente => fuente.onended);
        const duracion = Math.max(...fuentes.map(fuente => fuente.fin)) - Math.min(...fuentes.map(fuente => fuente.inicio));
        comprobar.ok(Math.abs(duracion - perfil.duracion) < 1e-10);
        fuentes.forEach(fuente => fuente.onended?.());
        caso.avanzar(catalogo.intervalo);
    }
});

test('silenciar detiene y desconecta voces, oculta audio y permite volver', () => {
    const caso = preparar();
    caso.activar();
    caso.motor.reproducir('error');
    const nodo = caso.contextos[0].nodos[0];
    caso.motor.silenciar(true);
    comprobar.equal(nodo.fin, undefined);
    comprobar.equal(nodo.desconectado, true);
    caso.avanzar(200);
    comprobar.equal(caso.motor.reproducir('exito'), false);
    caso.motor.silenciar(false);
    comprobar.equal(caso.motor.reproducir('exito'), true);
    caso.documento.hidden = true;
    caso.documento.emitir('visibilitychange');
    comprobar.equal(caso.contextos[0].nodos.at(-1).desconectado, true);
    comprobar.equal(caso.motor.reproducir('exito'), false);
});

test('pagehide libera el contexto y una vuelta desde caché exige otro gesto', () => {
    const caso = preparar();
    caso.activar();
    caso.motor.reproducir('apertura');
    caso.ventana.emitir('pagehide');
    comprobar.equal(caso.contextos[0].state, 'closed');
    comprobar.equal(caso.contextos[0].nodos[0].desconectado, true);
    comprobar.equal(caso.motor.reproducir('accion'), false);
    caso.activar();
    comprobar.equal(caso.contextos.length, 2);
    comprobar.equal(caso.motor.reproducir('accion'), true);
});

test('recargar el motor elimina listeners y no acumula contextos', () => {
    const caso = preparar();
    caso.activar();
    caso.cargar('sonido');
    comprobar.equal(caso.contextos[0].state, 'closed');
    comprobar.equal(caso.documento.contar('pointerdown'), 1);
    caso.ventana.scalaris.sonido.destruir();
    comprobar.equal(caso.documento.contar('pointerdown'), 0);
    comprobar.equal(caso.documento.contar('keydown'), 0);
    comprobar.equal(caso.ventana.contar('pagehide'), 0);
});

test('audio ausente o bloqueado y asignaciones fallidas conservan la interfaz', async () => {
    for (const opciones of [{ sinAudio: true }, { fallaConstructor: true },
        { suspendido: true, rechazarReanudacion: true }, { fallaGanancia: true }]) {
        const caso = preparar(opciones);
        comprobar.doesNotThrow(caso.activar);
        comprobar.equal(caso.motor.reproducir('error'), false);
        if (opciones.fallaGanancia) comprobar.equal(caso.contextos[0].nodos[0].desconectado, true);
        await Promise.resolve();
        comprobar.doesNotThrow(() => caso.motor.destruir());
    }
});
