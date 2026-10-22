"use strict";

const maquinaVirtual = require("node:vm");
const catalogo = require("../src/frontend/recursos/catalogo_captura.json");
const { cargarAssetCliente, crearEntradaSimulada } = require("./comun_cliente_javascript.js");
const { crearListaClases } = require("./comun_cuadricula_cliente.js");

/** Crea un destino de eventos con todos sus manejadores observables. */
function crearDestinoEventos() {
    const manejadoresPorEvento = new Map();
    return {
        manejadoresPorEvento,
        addEventListener(nombre, manejador) {
            if (!manejadoresPorEvento.has(nombre)) manejadoresPorEvento.set(nombre, new Set());
            manejadoresPorEvento.get(nombre).add(manejador);
        },
        removeEventListener(nombre, manejador) { manejadoresPorEvento.get(nombre)?.delete(manejador); },
        emitir(nombre, evento) {
            for (const manejador of [...(manejadoresPorEvento.get(nombre) || [])]) manejador(evento);
        },
    };
}

function coincideSelector(entrada, selector) {
    const atributos = [...selector.matchAll(/\[data-([^=\]]+)(?:=['"]([^'"]*)['"])?\]/g)];
    return atributos.every(([, nombre, valor]) => {
        const clave = nombre.replace(/-([a-z])/g, (_, letra) => letra.toUpperCase());
        return valor === undefined ? entrada.dataset[clave] !== undefined : entrada.dataset[clave] === valor;
    });
}

/** Crea un documento y temporizadores controlados para los assets de captura. */
function crearCapturaSimulada() {
    const entradas = [];
    const temporizadores = new Map();
    const ventana = crearDestinoEventos();
    const documento = crearDestinoEventos();
    let siguienteTemporizador = 0;
    documento.querySelectorAll = selector => entradas.filter(entrada => coincideSelector(entrada, selector));
    documento.querySelector = selector => documento.querySelectorAll(selector)[0] || null;
    const contexto = maquinaVirtual.createContext({
        window: ventana, document: documento, Event, CSS: { escape: valor => valor },
        setTimeout(manejador, demora) {
            const identificador = ++siguienteTemporizador;
            temporizadores.set(identificador, { manejador, demora });
            return identificador;
        },
        clearTimeout: identificador => temporizadores.delete(identificador),
    });
    return { ventana, documento, contexto, entradas, temporizadores };
}

/** Añade una entrada con su control visual y un panel delimitado. */
function agregarEntradaCaptura(cliente, datos, valor = "123", panel = "principal") {
    const entrada = crearEntradaSimulada(valor);
    const control = { classList: crearListaClases() };
    entrada.dataset = datos;
    entrada.panel = panel;
    entrada.control = control;
    entrada.selecciones = 0;
    entrada.focus = () => { cliente.documento.activeElement = entrada; entrada.enfocada = true; };
    entrada.select = () => { entrada.selecciones++; };
    entrada.closest = selector => {
        if (selector === ".q-field__control") return control;
        return { querySelectorAll: consulta => entradasPanel(cliente, panel, consulta) };
    };
    cliente.entradas.push(entrada);
    return entrada;
}

function entradasPanel(cliente, panel, selector) {
    const entradas = cliente.entradas.filter(entrada => entrada.panel === panel);
    if (selector === ".cuadricula-resaltado-cruzado") {
        return entradas.map(entrada => entrada.control).filter(control => control.classList.contains("cuadricula-resaltado-cruzado"));
    }
    return entradas.filter(entrada => coincideSelector(entrada, selector));
}

/** Carga juntos los tres adaptadores para detectar interferencias entre ellos. */
function cargarCapturas(cliente) {
    for (const nombre of [...catalogo, "captura_ecuaciones.js", "captura_matrices.js", "captura_vectores.js"]) {
        cargarAssetCliente(nombre, cliente.contexto);
    }
}

/** Emite un evento que cuenta cada cancelación de su acción predeterminada. */
function emitirEventoCaptura(cliente, nombre, opciones = {}) {
    const evento = { target: cliente.documento.activeElement, cancelaciones: 0, ...opciones };
    evento.preventDefault = () => { evento.cancelaciones++; };
    cliente.documento.emitir(nombre, evento);
    return evento;
}

/** Describe los atributos de un adaptador sin conservar alias retirados. */
function datosEntradaCaptura(tipo, fila, columna, grupo = "A") {
    if (tipo === "ecuaciones") return { ecuacionesFila: String(fila), ecuacionesColumna: String(columna) };
    if (tipo === "matrices") return { matrizFila: String(fila), matrizColumna: String(columna), matrizIdentificador: grupo };
    return { geometriaIndice: String(fila), geometriaVector: grupo, geometriaOrientacion: columna };
}

/** Añade celdas de un adaptador y conserva su orden para comprobar el destino. */
function agregarCeldasCaptura(cliente, tipo, coordenadas, grupo = "A") {
    return coordenadas.map(([fila, columna]) => agregarEntradaCaptura(cliente, datosEntradaCaptura(tipo, fila, columna, grupo)));
}

/** Ejecuta los temporizadores pendientes una sola vez. */
function completarSelecciones(cliente) {
    const pendientes = [...cliente.temporizadores.values()];
    cliente.temporizadores.clear();
    pendientes.forEach(temporizador => temporizador.manejador());
}

module.exports = {
    crearCapturaSimulada, agregarEntradaCaptura, cargarCapturas, emitirEventoCaptura,
    datosEntradaCaptura, agregarCeldasCaptura, completarSelecciones,
};
