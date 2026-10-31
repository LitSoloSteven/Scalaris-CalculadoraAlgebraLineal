"use strict";
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

const configuracion = {maximoFiguras: 12, maximoBytesImagen: 1024, maximoBytesTotal: 2048,
    maximoLado: 4096, maximoPixeles: 12000000, plazoMathjax: 0.05, escala: 2};

function crearRegion(clave, visible = true) {
    return {dataset: {pdfCaptura: clave}, scrollWidth: 100, scrollHeight: 50,
        getClientRects: () => visible ? [{}] : [],
        getBoundingClientRect: () => ({width: 100, height: 50})};
}

function crearCliente(regiones = [crearRegion('sistemas-resumen')]) {
    const raiz = {inert: false, querySelectorAll: () => regiones};
    const lienzos = [];
    const opciones = [];
    const ventana = {MathJax: {startup: {promise: Promise.resolve()}, typesetPromise: () => Promise.resolve()},
        html2canvas: async (nodo, ajustes) => {
            opciones.push(ajustes);
            const lienzo = {width: 100, height: 50, toDataURL: () => 'data:image/png;base64,AAAA'};
            lienzos.push(lienzo);
            return lienzo;
        }};
    const documento = {getElementById: () => raiz, fonts: {ready: Promise.resolve()}};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout});
    cargarAssetCliente('captura_pdf.js', contexto);
    return {ventana, raiz, lienzos, opciones, capturar: () => ventana.scalaris.capturaPdf.capturar('resultado', configuracion)};
}

prueba('captura solo regiones visibles y libera lienzos e inert', async () => {
    const cliente = crearCliente([crearRegion('sistemas-resumen'), crearRegion('oculta', false)]);
    const respuesta = await cliente.capturar();
    afirmar.equal(respuesta.capturas.length, 1);
    afirmar.equal(respuesta.capturas[0].clave, 'sistemas-resumen');
    afirmar.equal(cliente.raiz.inert, false);
    afirmar.equal(cliente.lienzos[0].width, 0);
    afirmar.equal(cliente.lienzos[0].height, 0);
    afirmar.equal(cliente.opciones[0].backgroundColor, 'white');
    afirmar.equal(typeof cliente.opciones[0].onclone, 'function');
});

prueba('un error de MathJax conserva el resultado y permite reintentar', async () => {
    const cliente = crearCliente();
    cliente.ventana.MathJax.typesetPromise = () => Promise.reject(new Error('detalle privado'));
    afirmar.equal((await cliente.capturar()).error, 'captura');
    afirmar.equal(cliente.raiz.inert, false);
    cliente.ventana.MathJax.typesetPromise = () => Promise.resolve();
    afirmar.equal((await cliente.capturar()).capturas.length, 1);
});

prueba('el plazo de formulas evita esperas ilimitadas y limpia el bloqueo', async () => {
    const cliente = crearCliente();
    cliente.ventana.MathJax.startup.promise = new Promise(() => {});
    afirmar.equal((await cliente.capturar()).error, 'captura');
    afirmar.equal(cliente.raiz.inert, false);
});

prueba('rechaza capturas simultaneas y presupuestos excesivos', async () => {
    const cliente = crearCliente();
    const primera = cliente.capturar();
    afirmar.equal((await cliente.capturar()).error, 'captura');
    await primera;
    const excesivo = crearCliente(Array.from({length: 13}, () => crearRegion('region')));
    afirmar.equal((await excesivo.capturar()).error, 'captura');
    afirmar.equal(excesivo.raiz.inert, false);
});
