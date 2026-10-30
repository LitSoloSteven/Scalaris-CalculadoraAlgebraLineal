'use strict';
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');
const { estilosMovimiento } = require('./comun_tokens_movimiento.js');

/** Crea un nodo observable sin interpretar contenido ni reconstruir descendientes. */
function nodoSimulado() {
    const atributos = new Map(), eventos = new Map();
    return { atributos, eventos, isConnected: true, nodeType: 1,
        setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        getAttribute: nombre => atributos.get(nombre),
        removeAttribute: nombre => atributos.delete(nombre),
        addEventListener: (nombre, funcion) => eventos.set(nombre, funcion),
        removeEventListener: nombre => eventos.delete(nombre),
        matches: () => false, querySelectorAll: () => [],
    };
}

/** Carga motor y observación con reloj controlado y nodos de texto independientes. */
function crearRevelado() {
    let ahora = 0, observar;
    const tareas = [], eventos = new Map(), raiz = nodoSimulado();
    const ventana = { matchMedia: () => ({ matches: false }) };
    const documento = { documentElement: raiz, addEventListener: (nombre, funcion) => eventos.set(nombre, funcion),
        querySelectorAll: () => [], createTreeWalker: contenido => {
            let indice = -1;
            return { nextNode() { indice++; this.currentNode = contenido.nodos[indice]; return !!this.currentNode; } };
        } };
    const contexto = vm.createContext({ window: ventana, document: documento,
        getComputedStyle: estilosMovimiento, NodeFilter: { SHOW_TEXT: 4 }, Date: { now: () => ahora },
        setTimeout: (funcion, espera) => { tareas.push({ funcion, espera }); return tareas.length; },
        clearTimeout: indice => { if (indice) tareas[indice - 1].cancelada = true; },
        MutationObserver: class { constructor(funcion) { observar = funcion; } observe() {} },
    });
    cargarAssetCliente('interacciones_globales.js', contexto);
    cargarAssetCliente('escritura_progresiva.js', contexto);
    cargarAssetCliente('revelado_glosa.js', contexto);
    return { ventana, contexto, tareas, raiz, eventos,
        observar: registros => observar(registros),
        avanzar: tarea => { ahora += tarea.espera; tarea.funcion(); },
        tiempo: () => ahora };
}

/** Monta una respuesta en la bitácora simulada y ejecuta la observación del cliente. */
function insertarRespuesta(cliente, textos, bitacora = nodoSimulado()) {
    const respuesta = nodoSimulado(), contenido = nodoSimulado(), burbuja = nodoSimulado();
    contenido.nodos = textos.map(textContent => ({ textContent }));
    contenido.matches = selector => selector === '[data-escritura-pendiente]';
    contenido.closest = selector => ({ '[role="log"]': bitacora,
        '.glosa-respuesta': respuesta, '.glosa-burbuja-asistente': burbuja })[selector];
    bitacora.scrollHeight = 1000;
    cliente.observar([{ addedNodes: [contenido] }]);
    return { contenido, bitacora, respuesta, burbuja };
}

module.exports = { crearRevelado, insertarRespuesta, nodoSimulado };
