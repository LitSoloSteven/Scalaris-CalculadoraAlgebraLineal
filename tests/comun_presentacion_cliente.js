"use strict";
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");
const { estilosMovimiento } = require("./comun_tokens_movimiento.js");

/** Reloj determinista que espera las promesas producidas por cada tarea. */
function crearReloj() {
    let tiempo = 0, siguiente = 0;
    const tareas = new Map();
    function programar(accion, demora) {
        const identificador = ++siguiente;
        tareas.set(identificador, { accion, instante: tiempo + demora });
        return identificador;
    }
    async function avanzar(destino) {
        for (let indice = 0; indice < 8; indice++) await Promise.resolve();
        let pendiente;
        while ((pendiente = [...tareas].filter(([, tarea]) => tarea.instante <= destino)
            .sort((a, b) => a[1].instante - b[1].instante)[0])) {
            tiempo = pendiente[1].instante;
            tareas.delete(pendiente[0]);
            pendiente[1].accion();
            for (let indice = 0; indice < 8; indice++) await Promise.resolve();
        }
        tiempo = destino;
    }
    return { programar, cancelar: identificador => tareas.delete(identificador), avanzar, tareas };
}

/** Registra oyentes y permite cancelarlos igual que las superficies del navegador. */
function crearEventos() {
    const oyentes = new Map();
    return {
        oyentes,
        addEventListener: (nombre, manejador) => {
            if (!oyentes.has(nombre)) oyentes.set(nombre, new Set());
            oyentes.get(nombre).add(manejador);
        },
        removeEventListener: (nombre, manejador) => {
            oyentes.get(nombre)?.delete(manejador);
            if (oyentes.get(nombre)?.size === 0) oyentes.delete(nombre);
        },
        emitir: (nombre, evento = {}) => [...(oyentes.get(nombre) || [])].forEach(manejador => manejador(evento)),
    };
}

/** Modelo del DOM limitado a los elementos y animaciones de la presentación. */
function crearDocumento(reloj, opciones) {
    const animaciones = [], atributos = new Map(), observadores = [];
    if (opciones.teclado) atributos.set('data-entrada', 'teclado');
    let montado = false, contenido = opciones.contenido !== false;
    const fondo = { toggleAttribute() {}, remove: () => { montado = false; } };
    function animar(fotogramas, tiempos) {
        if (opciones.animacionFallida) throw new Error("Animación no disponible");
        let resolver, rechazar;
        const finished = new Promise((exito, fallo) => { resolver = exito; rechazar = fallo; });
        const tarea = opciones.animacionCongelada ? null : reloj.programar(resolver, (tiempos.delay || 0) + tiempos.duration);
        const animacion = { fotogramas, tiempos, finished, cancelada: false,
            cancel() { this.cancelada = true; reloj.cancelar(tarea); rechazar(new Error("Cancelada")); } };
        animaciones.push(animacion);
        return animacion;
    }
    const imagen = { animate: animar, decode: () => opciones.imagenFallida ? Promise.reject(new Error("Imagen")) : Promise.resolve() };
    fondo.animate = animar;
    fondo.querySelector = selector => selector === "#presentacion-logotipo" ? imagen : { animate: animar };
    const raiz = { setAttribute: (nombre, valor) => atributos.set(nombre, valor),
        getAttribute: nombre => nombre === "data-tema" ? (opciones.tema || "papel") : atributos.get(nombre),
        removeAttribute: nombre => atributos.delete(nombre), appendChild: () => { montado = true; } };
    const documento = { ...crearEventos(), documentElement: raiz, body: { classList: { add() {} } },
        getElementById: nombre => nombre === "presentacion-plantilla"
            ? { content: { firstElementChild: { cloneNode: () => fondo } } } : (montado ? fondo : null),
        querySelector: () => contenido ? {} : null };
    return { documento, animaciones, atributos, fondo, imagen, observadores,
        montado: () => montado,
        montarContenido: () => { contenido = true; observadores.filter(o => o.activo).forEach(o => o.accion()); } };
}

/** Carga los recursos reales con almacenamiento y ciclos de vida observables. */
function crearPresentacion(opciones = {}) {
    const reloj = crearReloj(), dom = crearDocumento(reloj, opciones);
    const almacen = opciones.almacen || new Map();
    const preferencia = { ...crearEventos(), matches: opciones.reducido || false };
    const ventana = { ...crearEventos(), scalaris: {}, matchMedia: () => preferencia };
    const contexto = maquinaVirtual.createContext({
        window: ventana, document: dom.documento,
        location: { pathname: opciones.ruta || "/", search: opciones.consulta || "" },
        sessionStorage: {
            getItem: nombre => { if (opciones.almacenBloqueado) throw new Error("Almacenamiento"); return almacen.get(nombre); },
            setItem: (nombre, valor) => almacen.set(nombre, valor),
        },
        getComputedStyle: estilosMovimiento,
        setTimeout: reloj.programar, clearTimeout: reloj.cancelar,
        requestAnimationFrame: accion => reloj.programar(accion, 16), cancelAnimationFrame: reloj.cancelar,
        MutationObserver: class {
            constructor(accion) { this.accion = accion; dom.observadores.push(this); }
            observe() { this.activo = true; }
            disconnect() { this.activo = false; }
        },
    });
    function cargar(nombre) { cargarAssetCliente(nombre, contexto); }
    cargar("interacciones_globales.js");
    if (!opciones.sinPresentacion) cargar("presentacion.js");
    if (!opciones.sinEntrada) cargar("inicio_entrada.js");
    return { ...dom, reloj, almacen, preferencia, ventana, contexto, cargar };
}

module.exports = { crearPresentacion };
