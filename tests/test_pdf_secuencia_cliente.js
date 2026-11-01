'use strict';
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarCapturadorPdf} = require('./comun_capturador_pdf.js');

prueba('las capturas intermedias sustituyen al paso visible sin incluir regiones ocultas', async () => {
    const claves = ['inversa-resumen', 'inversa-procedimiento', 'inversa-comprobaciones',
        'inversa-entrada', 'inversa-paso-1', 'inversa-paso-2', 'inversa-paso-3'];
    const regiones = claves.map(clave => ({dataset: {pdfCaptura: clave}, scrollWidth: 200, scrollHeight: 100,
        querySelectorAll: () => [], getClientRects: () => [{}],
        getBoundingClientRect: () => ({width: 200, height: 100})}));
    regiones.push({dataset: {pdfCaptura: 'oculta'}, getClientRects: () => []});
    const raiz = {inert: false, querySelectorAll: () => regiones};
    const ventana = {MathJax: {typesetPromise: async () => {}}, html2canvas: async () => ({
        width: 200, height: 100, toDataURL: () => 'data:image/png;base64,AAAA'})};
    const documento = {getElementById: () => raiz, querySelectorAll: () => [], fonts: {ready: Promise.resolve()}};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout});
    cargarCapturadorPdf(contexto);
    const respuesta = await ventana.scalaris.capturaPdf.capturar('resultado', {
        maximoFiguras: 12, maximoBytesImagen: 1024, maximoBytesTotal: 8192,
        maximoLado: 4096, maximoPixeles: 12000000, plazoMathjax: 1, plazoCaptura: 2, escala: 2});
    afirmar.deepEqual(Array.from(respuesta.capturas, captura => captura.clave),
        claves.filter(clave => !clave.endsWith('-procedimiento')));
    afirmar.equal(raiz.inert, false);
});
