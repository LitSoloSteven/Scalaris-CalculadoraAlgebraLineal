'use strict';
const { readFileSync: leerArchivo } = require('node:fs');
const { runInNewContext: ejecutar } = require('node:vm');
const { superficie } = require('./comun_sonido_cliente.js');
const { inyectarCatalogo } = require('./comun_catalogo_sonoro.js');

/** Emula parámetros con sus valores y tiempos observables. */
function parametroAudio() {
    return { valores: [],
        setValueAtTime(...datos) { this.valores.push(datos); },
        linearRampToValueAtTime(...datos) { this.valores.push(datos); },
        exponentialRampToValueAtTime(...datos) { this.valores.push(datos); } };
}

/** Crea un contexto con todos sus nodos inspeccionables y fallos parciales. */
function contextoAudio(opciones = {}) {
    return { state: 'running', currentTime: 2, sampleRate: 48000, destination: {}, nodos: [], buffers: [],
        createOscillator() { return crearNodo(this, 'tono', opciones); },
        createBufferSource() { return crearNodo(this, 'ruido', opciones); },
        createBiquadFilter() { return crearNodo(this, 'filtro', opciones); },
        createGain() { return crearNodo(this, 'ganancia', opciones); },
        createBuffer(canales, longitud, frecuencia) {
            const datos = new Float32Array(longitud);
            this.buffers.push({ canales, longitud, frecuencia, datos });
            return { getChannelData: () => datos };
        },
        close() { this.state = 'closed'; return Promise.resolve(); },
        resume() { return Promise.resolve(); } };
}

function crearNodo(contexto, tipo, opciones) {
    if (opciones.fallar === tipo) throw new Error('Fallo simulado de nodo');
    const nodo = { tipo, frequency: parametroAudio(), gain: parametroAudio(), Q: parametroAudio(),
        connect(destino) { this.destino = destino; },
        disconnect() { this.desconectado = true; },
        start(inicio) { this.inicio = inicio; },
        stop(fin) { this.fin = fin; } };
    contexto.nodos.push(nodo);
    return nodo;
}

/** Monta el motor con reloj manual y contexto Web Audio observable. */
function prepararSintesis(opciones = {}) {
    const documento = superficie();
    inyectarCatalogo(documento);
    const ventana = superficie();
    const contextos = [];
    let ahora = 0;
    ventana.AudioContext = function () {
        const contexto = contextoAudio(opciones);
        contextos.push(contexto);
        return contexto;
    };
    const entorno = { window: ventana, document: documento, performance: { now: () => ahora } };
    const cargar = nombre => ejecutar(leerArchivo(`src/frontend/recursos/js/${nombre}.js`, 'utf8'), entorno);
    ['catalogo_sonidos', 'sintesis_sonora', 'sonido'].forEach(cargar);
    return { documento, ventana, contextos, cargar, avanzar: cantidad => { ahora += cantidad; },
        activar: () => documento.emitir('pointerdown', { isTrusted: true }), motor: ventana.scalaris.sonido };
}

module.exports = { prepararSintesis };
