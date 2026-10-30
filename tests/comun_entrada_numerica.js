'use strict';
const vm = require('node:vm');
const archivos = require('node:fs');
const rutas = require('node:path');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

/** Lee el alfabeto y el aviso reales sin duplicarlos en las pruebas de cliente. */
function configuracionNumerica() {
    const raiz = rutas.join(__dirname, '../src/frontend');
    const constantes = archivos.readFileSync(rutas.join(raiz, 'constantes.py'), 'utf8');
    const textos = archivos.readFileSync(rutas.join(raiz, 'textos.py'), 'utf8');
    return { caracteres: constantes.match(/CARACTERES_ENTRADA_NUMERICA = "([^"]+)"/)[1],
        mensaje: textos.match(/MENSAJE_ENTRADA_NUMERICA = "([^"]+)"/)[1] };
}

/** Construye elementos de estado que solo aceptan nodos de texto. */
function crearNodo() {
    const atributos = new Map();
    return { atributos, textContent: '',
        setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        replaceChildren(...nodos) { this.textContent = nodos.map(nodo => nodo.textContent).join(''); },
    };
}

/** Simula una superficie con animaciones de rechazo reiniciables y observables. */
function crearSuperficie() {
    const clases = new Set(), llamadas = [];
    const animaciones = ['sacudida', 'rechazoNumericoOpacidad'].map(animationName => ({ animationName,
        cancel: () => llamadas.push('cancelar:' + animationName),
        play: () => llamadas.push('reproducir:' + animationName) }));
    return { clases, llamadas, classList: { toggle(nombre, activo) {
        if (activo) clases.add(nombre); else clases.delete(nombre);
    } }, getAnimations: () => animaciones.filter(animacion =>
        clases.has(animacion.animationName === 'sacudida' ? 'movimiento-sacudida' : 'captura-rechazo-reducido')) };
}

/** Carga los recursos reales con documento, eventos y configuración controlados. */
function crearClienteNumerico(opciones = {}) {
    const eventos = new Map(), elementos = new Map();
    const configuracion = configuracionNumerica();
    if (!opciones.sinConfiguracion) elementos.set('scalaris-configuracion-numerica', {
        textContent: JSON.stringify(configuracion) });
    const ventana = { scalaris: {}, matchMedia: () => ({ matches: Boolean(opciones.reducido) }) };
    const documento = { body: { appendChild: nodo => elementos.set(nodo.id, nodo) },
        getElementById: nombre => elementos.get(nombre), createElement: crearNodo,
        createTextNode: texto => ({ textContent: texto }), querySelector: () => null,
        addEventListener(nombre, funcion, opcionesEvento) {
            if (!eventos.has(nombre)) eventos.set(nombre, new Map());
            eventos.get(nombre).set(funcion, opcionesEvento);
        }, removeEventListener: (nombre, funcion) => eventos.get(nombre)?.delete(funcion) };
    const contexto = vm.createContext({ window: ventana, document: documento, Event });
    for (const nombre of ['rechazo_entrada_numerica.js', 'entrada_numerica.js', 'captura_celdas.js']) {
        cargarAssetCliente(nombre, contexto);
    }
    return { ventana, documento, elementos, eventos, contexto, configuracion,
        emitir: (nombre, evento) => eventos.get(nombre)?.forEach((_, funcion) => funcion(evento)) };
}

/** Crea una celda que conserva selección, pertenencia numérica y eventos publicados. */
function crearCeldaNumerica(cliente, valor = '', numerica = true) {
    const superficie = crearSuperficie();
    const entrada = { value: valor, tagName: 'INPUT', superficie, publicados: [],
        dataset: { soloNumerico: numerica ? 'true' : 'false', matrizFila: '0' },
        matches: () => numerica, closest: () => superficie,
        selectionStart: valor.length, selectionEnd: valor.length, selectionDirection: 'forward',
        setSelectionRange(inicio, fin, direccion) {
            this.selectionStart = inicio; this.selectionEnd = fin; this.selectionDirection = direccion;
        }, dispatchEvent(evento) {
            this.publicados.push(evento);
            cliente.emitir(evento.type, { target: this, isTrusted: false });
        } };
    return entrada;
}

/** Emite una inserción cancelable de confianza, con opciones para los casos de pegado e IME. */
function insertar(cliente, entrada, texto, opciones = {}) {
    const evento = { target: entrada, inputType: 'insertText', data: texto, isTrusted: true,
        cancelable: true, bloqueado: false, preventDefault() { this.bloqueado = true; }, ...opciones };
    cliente.emitir('beforeinput', evento);
    return evento;
}

module.exports = { crearClienteNumerico, crearCeldaNumerica, insertar };
