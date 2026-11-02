'use strict';
const afirmar = require('node:assert/strict');
const prueba = require('node:test');
const maquinaVirtual = require('node:vm');
const {cargarAssetCliente} = require('./comun_cliente_javascript.js');

function crearApi(ventana = {}, opciones = {}) {
    const contexto = maquinaVirtual.createContext({window: ventana, setTimeout, ...opciones});
    cargarAssetCliente('clon_pdf.js', contexto);
    return ventana.scalaris.clonPdf;
}

function crearNodo(padre = null) {
    const clases = new Set(['q-expansion-item--collapsed']);
    return {parentElement: padre, scrollWidth: 0, clientWidth: 0,
        style: {setProperty(nombre, valor, prioridad) { this[nombre] = valor; this.prioridad = prioridad; }},
        classList: {add: nombre => clases.add(nombre), remove: nombre => clases.delete(nombre),
            contains: nombre => clases.has(nombre)},
        matches: () => false, querySelectorAll: () => [],
        contains(nodo) {
            for (let actual = nodo; actual; actual = actual.parentElement) if (actual === this) return true;
            return false;
        }};
}

function crearClon(nodos = []) {
    const registro = {lecturas: 0, conversiones: 0, retirado: false};
    const lienzo = {width: 0, height: 0, getContext: () => ({clearRect() {}, fillRect() { registro.conversiones++; },
        getImageData: () => ({data: [35, 38, 46, 255]})})};
    const propiedades = ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor',
        'borderBottomColor', 'borderLeftColor', 'outlineColor', 'textDecorationColor', 'boxShadow', 'backgroundImage'];
    const estilos = Object.fromEntries(propiedades.map(propiedad => [propiedad, 'oklch(0.5 0.1 30)']));
    const documento = {documentElement: {setAttribute(nombre, valor) { registro.tema = valor; }},
        body: {classList: {remove() {}}, style: {}}, createElement: () => lienzo,
        defaultView: {getComputedStyle(nodo) {
            if (nodos.includes(nodo)) registro.lecturas++;
            return {display: 'none', ...estilos};
        }},
        querySelectorAll(selector) {
            if (selector === '[data-pdf-excluir]') return [{remove() { registro.retirado = true; }}];
            return selector.includes('data-pdf-captura') ? nodos : [];
        }};
    return {documento, registro, lienzo};
}

prueba('el indicador espera dos fotogramas completos antes de continuar', async () => {
    const fotogramas = [];
    const api = crearApi({requestAnimationFrame: resolver => fotogramas.push(resolver)});
    let terminado = false;
    const espera = api.pintarIndicador().then(() => { terminado = true; });
    afirmar.equal(fotogramas.length, 1);
    fotogramas.shift()();
    await Promise.resolve();
    afirmar.equal(terminado, false);
    afirmar.equal(fotogramas.length, 1);
    fotogramas.shift()();
    await espera;
    afirmar.equal(terminado, true);
});

prueba('la cesion usa scheduler cuando esta disponible', async () => {
    let cesiones = 0;
    const api = crearApi({scheduler: {yield: async () => { cesiones++; }}});
    await api.ceder();
    afirmar.equal(cesiones, 1);
});

prueba('la alternativa MessageChannel cierra sus dos puertos', async () => {
    let cierres = 0;
    const api = crearApi({MessageChannel: class {
        constructor() {
            this.port1 = {close() { cierres++; }};
            this.port2 = {close() { cierres++; }, postMessage: () => queueMicrotask(() => this.port1.onmessage())};
        }
    }});
    await api.ceder();
    afirmar.equal(cierres, 2);
});

prueba('sin scheduler ni canales la cesion programa una tarea de espera cero', async () => {
    const esperas = [];
    const api = crearApi({}, {setTimeout: (resolver, espera) => { esperas.push(espera); resolver(); }});
    await api.ceder();
    afirmar.deepEqual(esperas, [0]);
});

prueba('el clon abre la expansion raiz y fuerza sus ancestros sin dejar controles diferidos', async () => {
    const {documento, registro} = crearClon();
    const region = crearNodo();
    const contenedor = crearNodo(region);
    const contenido = crearNodo(contenedor);
    const anidada = crearNodo(contenido);
    const interior = crearNodo(anidada);
    region.matches = selector => selector === '.q-expansion-item';
    region.querySelectorAll = selector => ({'.q-expansion-item': [anidada],
        '.q-expansion-item__content': [contenido, interior]}[selector] || []);
    anidada.querySelectorAll = selector => selector === '.q-expansion-item__content' ? [interior] : [];
    const api = crearApi({scheduler: {yield: async () => {}}});
    await api.preparar(documento, region, 800, {cancelada: false});
    afirmar.equal(registro.retirado, true);
    afirmar.equal(registro.tema, 'papel');
    afirmar.equal(region.classList.contains('q-expansion-item--collapsed'), false);
    afirmar.equal(anidada.classList.contains('q-expansion-item--expanded'), true);
    for (const nodo of [region, contenedor, contenido, anidada, interior]) {
        afirmar.equal(nodo.style.display, 'block');
        afirmar.equal(nodo.style.height, 'auto');
        afirmar.equal(nodo.style['max-height'], 'none');
        afirmar.equal(nodo.style.overflow, 'visible');
        afirmar.equal(nodo.style.visibility, 'visible');
        afirmar.equal(nodo.style.opacity, '1');
        afirmar.equal(nodo.style.prioridad, 'important');
    }
    afirmar.equal(region.style.width, '800px');
});

prueba('los colores se normalizan en lotes de 250 sin alterar la conversion ni retener el lienzo', async () => {
    const nodos = Array.from({length: 501}, () => crearNodo());
    const {documento, registro, lienzo} = crearClon(nodos);
    const lecturasPorCesion = [];
    const api = crearApi({scheduler: {yield: async () => { lecturasPorCesion.push(registro.lecturas); }}});
    await api.preparar(documento, crearNodo(), 800, {cancelada: false});
    afirmar.deepEqual(lecturasPorCesion.filter(Boolean), [250, 500, 501]);
    afirmar.equal(registro.lecturas, 501);
    afirmar.equal(registro.conversiones, 1);
    afirmar.ok(nodos.every(nodo => nodo.style.color === 'rgba(35, 38, 46, 1)'));
    afirmar.equal(lienzo.width, 0);
    afirmar.equal(lienzo.height, 0);
});

prueba('una cancelacion entre lotes interrumpe la normalizacion y libera su lienzo', async () => {
    const nodos = Array.from({length: 501}, () => crearNodo());
    const {documento, registro, lienzo} = crearClon(nodos);
    const estado = {cancelada: false};
    const api = crearApi({scheduler: {yield: async () => {
        if (registro.lecturas) estado.cancelada = true;
    }}});
    await afirmar.rejects(api.preparar(documento, crearNodo(), 800, estado), /cancelada/);
    afirmar.equal(registro.lecturas, 250);
    afirmar.equal(nodos[250].style.color, undefined);
    afirmar.equal(lienzo.width, 0);
    afirmar.equal(lienzo.height, 0);
});

prueba('los fotogramas tardios no cargan bibliotecas ni componen formulas despues del plazo', async () => {
    const fotogramas = [];
    let bibliotecas = 0, composiciones = 0;
    const ventana = {requestAnimationFrame: resolver => fotogramas.push(resolver),
        scheduler: {yield: async () => {}},
        get html2canvas() { bibliotecas++; return async () => ({}); },
        MathJax: {typesetPromise: async () => { composiciones++; }}};
    const raiz = {inert: false, querySelectorAll: () => []};
    const documento = {getElementById: () => raiz, querySelectorAll: () => []};
    const contexto = maquinaVirtual.createContext({window: ventana, document: documento, setTimeout, clearTimeout});
    cargarAssetCliente('clon_pdf.js', contexto);
    cargarAssetCliente('captura_pdf.js', contexto);
    const respuesta = await ventana.scalaris.capturaPdf.capturar('raiz', {plazoCaptura: 0.001});
    afirmar.equal(respuesta.error, 'captura');
    afirmar.equal(raiz.inert, false);
    fotogramas.shift()();
    await Promise.resolve();
    fotogramas.shift()();
    await new Promise(resolver => setImmediate(resolver));
    afirmar.equal(bibliotecas, 0);
    afirmar.equal(composiciones, 0);
});
