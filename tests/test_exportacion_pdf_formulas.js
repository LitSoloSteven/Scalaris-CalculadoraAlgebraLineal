"use strict";
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

prueba('el clon excluye MathML asistivo y recolorea los elementos personalizados de MathJax', async () => {
    const formula = {style: {color: 'rgb(234, 246, 255)'}};
    const region = {dataset: {pdfCaptura: 'matrices-procedimiento'}, scrollWidth: 100, scrollHeight: 50,
        querySelectorAll: () => [], getClientRects: () => [{}],
        getBoundingClientRect: () => ({width: 100, height: 50}), style: {setProperty() {}}};
    const clon = {documentElement: {setAttribute() {}}, body: {classList: {remove() {}}, style: {}},
        defaultView: {getComputedStyle: () => ({getPropertyValue: () => 'rgb(35, 38, 46)'})},
        createElement: () => ({getContext: () => ({})}),
        querySelectorAll: selector => selector === '.MathJax, .MathJax *' ? [formula] : []};
    const ventana = {MathJax: {startup: {promise: Promise.resolve()}, typesetPromise: () => Promise.resolve()},
        html2canvas: async (nodo, opciones) => {
            afirmar.equal(opciones.ignoreElements({tagName: 'MJX-ASSISTIVE-MML'}), true);
            afirmar.equal(opciones.ignoreElements({tagName: 'MJX-MATH'}), false);
            opciones.onclone(clon, region);
            return {width: 100, height: 50, toDataURL: () => 'data:image/png;base64,AAAA'};
        }};
    const raiz = {inert: false, querySelectorAll: () => [region]};
    const documento = {getElementById: () => raiz, querySelectorAll: () => [], fonts: {ready: Promise.resolve()}};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout});
    cargarAssetCliente('captura_pdf.js', contexto);
    const respuesta = await ventana.scalaris.capturaPdf.capturar('raiz', {maximoFiguras: 12,
        maximoBytesImagen: 1024, maximoBytesTotal: 2048, maximoLado: 4096, maximoPixeles: 12000000,
        plazoMathjax: 0.1, plazoCaptura: 0.2, escala: 2});
    afirmar.equal(respuesta.capturas.length, 1);
    afirmar.equal(formula.style.color, 'rgb(35, 38, 46)');
});
