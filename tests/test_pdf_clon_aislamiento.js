'use strict';
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarCapturadorPdf} = require('./comun_capturador_pdf.js');

prueba('cada clon omite las otras figuras y conserva su region y ancestros', async () => {
    const region = {tagName: 'DIV', dataset: {pdfCaptura: 'inversa-entrada'}, scrollWidth: 100,
        scrollHeight: 50, querySelectorAll: () => [], getClientRects: () => [{}],
        getBoundingClientRect: () => ({width: 100, height: 50})};
    const otra = {tagName: 'DIV', dataset: {pdfCaptura: 'inversa-comprobaciones'}, contains: () => false};
    const ancestro = {...otra, contains: elemento => elemento === region};
    const ventana = {MathJax: {typesetPromise: async () => {}}, html2canvas: async (nodo, opciones) => {
        afirmar.equal(opciones.ignoreElements(region), false);
        afirmar.equal(opciones.ignoreElements(otra), true);
        afirmar.equal(opciones.ignoreElements(ancestro), false);
        afirmar.equal(opciones.ignoreElements({tagName: 'MJX-ASSISTIVE-MML'}), true);
        afirmar.equal(opciones.ignoreElements({tagName: 'BUTTON', hasAttribute: () => true}), true);
        afirmar.equal(opciones.ignoreElements({tagName: 'MJX-MATH'}), false);
        return {width: 100, height: 50, toDataURL: () => 'data:image/png;base64,AAAA'};
    }};
    const raiz = {inert: false, querySelectorAll: () => [region]};
    const documento = {getElementById: () => raiz, querySelectorAll: () => [], fonts: {ready: Promise.resolve()}};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout});
    cargarCapturadorPdf(contexto);
    const respuesta = await ventana.scalaris.capturaPdf.capturar('resultado', {
        maximoFiguras: 12, maximoBytesImagen: 1024, maximoBytesTotal: 8192,
        maximoLado: 4096, maximoPixeles: 12000000, plazoMathjax: 1, plazoCaptura: 2, escala: 2});
    afirmar.equal(respuesta.capturas[0].clave, 'inversa-entrada');
});
