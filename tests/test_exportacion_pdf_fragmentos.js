"use strict";
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarCapturadorPdf} = require('./comun_capturador_pdf.js');

function prepararCliente() {
    const png = 'ABCD'.repeat(350000);
    const region = {dataset: {pdfCaptura: 'matrices-resumen'}, scrollWidth: 100, scrollHeight: 50,
        querySelectorAll: () => [], getClientRects: () => [{}], getBoundingClientRect: () => ({width: 100, height: 50})};
    const raiz = {inert: false, querySelectorAll: () => [region]};
    const relojes = new Map();
    let consecutivo = 0;
    const ventana = {MathJax: {startup: {promise: Promise.resolve()}, typesetPromise: () => Promise.resolve()},
        html2canvas: async () => ({width: 100, height: 50, toDataURL: () => 'data:image/png;base64,' + png})};
    const documento = {getElementById: () => raiz, querySelectorAll: () => [], fonts: {ready: Promise.resolve()}};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento,
        setTimeout: tarea => { relojes.set(++consecutivo, tarea); return consecutivo; },
        clearTimeout: identificador => relojes.delete(identificador)});
    cargarCapturadorPdf(contexto);
    const api = ventana.scalaris.capturaPdf;
    const configuracion = {maximoFiguras: 12, maximoBytesImagen: 2000000, maximoBytesTotal: 4000000,
        maximoLado: 4096, maximoPixeles: 12000000, plazoMathjax: 15, plazoCaptura: 50, escala: 2};
    return {api, png, relojes, preparar: () => api.preparar('resultado', configuracion)};
}

prueba('el manifiesto es pequeño y los fragmentos conservan el PNG mayor que un mensaje', async () => {
    const cliente = prepararCliente();
    const manifiesto = await cliente.preparar();
    afirmar.ok(JSON.stringify(manifiesto).length < 1000);
    afirmar.equal(manifiesto.capturas[0].longitud, cliente.png.length);
    const fragmentos = [];
    for (let inicio = 0; inicio < cliente.png.length; inicio += 262144) {
        fragmentos.push(cliente.api.leer(manifiesto.solicitud, 0, inicio, 262144));
    }
    afirmar.equal(fragmentos.join(''), cliente.png);
    afirmar.equal(cliente.api.liberar(manifiesto.solicitud), true);
    afirmar.equal(cliente.api.leer(manifiesto.solicitud, 0, 0, 4), null);
});

prueba('un testigo anterior no lee ni libera capturas posteriores y la caducidad limpia la memoria', async () => {
    const cliente = prepararCliente();
    const anterior = await cliente.preparar();
    const actual = await cliente.preparar();
    afirmar.equal(cliente.api.leer(anterior.solicitud, 0, 0, 4), null);
    afirmar.equal(cliente.api.liberar(anterior.solicitud), false);
    afirmar.equal(cliente.api.leer(actual.solicitud, 0, 0, 4), 'ABCD');
    afirmar.equal(cliente.relojes.size, 1);
    cliente.relojes.values().next().value();
    afirmar.equal(cliente.api.leer(actual.solicitud, 0, 0, 4), null);
    afirmar.equal(cliente.relojes.size, 0);
});
