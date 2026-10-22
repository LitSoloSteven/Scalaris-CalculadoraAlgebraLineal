"use strict";
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const archivos = require('node:fs');
const rutas = require('node:path');
const maquina = require('node:vm');
const fuente = archivos.readFileSync(rutas.join(__dirname,
    '../src/frontend/recursos/js/selector_opciones.js'), 'utf8');

function crearSelector(cantidad, columnas) {
    const propiedades = {};
    const clases = new Set();
    const lecturas = [];
    const indicador = {};
    const grupo = {
        dataset: { selectorColumnas: String(columnas) },
        style: { setProperty: (nombre, valor) => { propiedades[nombre] = valor; } },
        classList: { add: nombre => clases.add(nombre), remove: nombre => clases.delete(nombre) },
        get offsetWidth() { lecturas.push('medicion'); return 640; },
        querySelector: () => indicador,
    };
    const botones = Array.from({ length: cantidad }, (_, indice) => ({
        atributos: { 'aria-checked': String(indice === 0) },
        closest: () => grupo,
        getAttribute(nombre) { return this.atributos[nombre]; },
        setAttribute(nombre, valor) { this.atributos[nombre] = valor; },
    }));
    grupo.querySelectorAll = () => botones;
    const ventana = { getComputedStyle: () => ({ transform: 'matrix(1, 0, 0, 1, 17, 9)' }) };
    maquina.runInNewContext(fuente, { window: ventana });
    return { ventana, grupo, botones, propiedades, clases, lecturas };
}

for (const cantidad of [2, 4]) {
    prueba(`${cantidad} opciones sincronizan coordenadas y origen en ambos sentidos`, () => {
        const selector = crearSelector(cantidad, 2);
        let anterior = 0;
        const indices = Array.from({ length: cantidad }, (_, indice) => indice);
        for (const indice of [...indices, ...indices.toReversed()]) {
            selector.ventana.scalaris.selectorOpciones.activar({ currentTarget: selector.botones[indice] });
            afirmar.equal(selector.propiedades['--selector-indice'], indice);
            afirmar.equal(selector.propiedades['--selector-columna-compacta'], indice % 2);
            afirmar.equal(selector.propiedades['--selector-fila-compacta'], Math.floor(indice / 2));
            afirmar.equal(selector.propiedades['--selector-indice-anterior'], anterior);
            afirmar.equal(selector.propiedades['--selector-columna-anterior'], anterior % 2);
            afirmar.equal(selector.propiedades['--selector-fila-anterior'], Math.floor(anterior / 2));
            afirmar.equal(selector.clases.has('selector-opciones-cambiando'), indice !== anterior);
            afirmar.equal(selector.botones.filter(boton => boton.atributos.tabindex === '0').length, 1);
            anterior = indice;
        }
    });
}

prueba('las columnas proceden del grupo en lugar de una constante duplicada en JavaScript', () => {
    const selector = crearSelector(4, 3);
    selector.ventana.scalaris.selectorOpciones.activar({ currentTarget: selector.botones[3] });
    afirmar.equal(selector.propiedades['--selector-columna-compacta'], 0);
    afirmar.equal(selector.propiedades['--selector-fila-compacta'], 1);
});

prueba('interrumpir conserva la transformacion visible como origen del siguiente movimiento', () => {
    const selector = crearSelector(4, 2);
    selector.ventana.scalaris.selectorOpciones.activar({ currentTarget: selector.botones[3] });
    afirmar.equal(selector.propiedades['--selector-origen-transformacion'], 'matrix(1, 0, 0, 1, 17, 9)');
    afirmar.equal(selector.lecturas.length, 1);
    selector.ventana.scalaris.selectorOpciones.activar({ currentTarget: selector.botones[1] });
    afirmar.equal(selector.lecturas.length, 2);
    afirmar.equal(selector.propiedades['--selector-indice-anterior'], 3);
});

prueba('repetir la seleccion no reinicia animaciones ni mide la disposicion', () => {
    const selector = crearSelector(2, 2);
    selector.ventana.scalaris.selectorOpciones.activar({ currentTarget: selector.botones[0] });
    afirmar.equal(selector.lecturas.length, 0);
    afirmar.equal(selector.clases.has('selector-opciones-cambiando'), false);
});
