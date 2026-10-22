"use strict";
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const archivos = require('node:fs');
const rutas = require('node:path');
const maquina = require('node:vm');
const fuente = archivos.readFileSync(rutas.join(__dirname,
    '../src/frontend/recursos/js/selector_opciones.js'), 'utf8');

function crearSelector() {
    const ventana = {};
    const propiedades = {};
    const grupo = { style: { setProperty: (nombre, valor) => { propiedades[nombre] = valor; } } };
    const botones = Array.from({ length: 4 }, () => ({
        atributos: {}, clics: 0, enfocado: false,
        closest: () => grupo,
        setAttribute(nombre, valor) { this.atributos[nombre] = valor; },
        focus() { this.enfocado = true; },
        click() {
            this.clics += 1;
            ventana.scalaris.selectorOpciones.activar({ currentTarget: this });
        },
    }));
    grupo.querySelectorAll = () => botones;
    maquina.runInNewContext(fuente, { window: ventana });
    return { ventana, botones, propiedades };
}

for (const [tecla, origen, destino] of [['ArrowRight', 0, 1], ['ArrowLeft', 0, 3],
    ['ArrowRight', 3, 0], ['ArrowLeft', 2, 1]]) {
    prueba(`la flecha ${tecla} selecciona ${destino} desde ${origen} al instante`, () => {
        const selector = crearSelector();
        let cancelado = false;
        selector.ventana.scalaris.selectorOpciones.teclado({ key: tecla,
            currentTarget: selector.botones[origen], preventDefault: () => { cancelado = true; } });
        afirmar.equal(cancelado, true);
        afirmar.equal(selector.botones[destino].enfocado, true);
        afirmar.equal(selector.botones[destino].clics, 1);
        afirmar.equal(selector.botones[destino].atributos['aria-checked'], 'true');
        afirmar.equal(selector.propiedades['--selector-indice'], destino);
        afirmar.equal(selector.botones.filter(boton => boton.atributos.tabindex === '0').length, 1);
    });
}

prueba('Tab y atajos modificados conservan su comportamiento nativo', () => {
    const selector = crearSelector();
    const cancelar = () => { afirmar.fail('No debe cancelar esta tecla'); };
    for (const opciones of [{ key: 'Tab' }, { key: 'ArrowRight', ctrlKey: true }]) {
        selector.ventana.scalaris.selectorOpciones.teclado({ ...opciones,
            currentTarget: selector.botones[0], preventDefault: cancelar });
    }
    afirmar.equal(selector.botones.reduce((total, boton) => total + boton.clics, 0), 0);
});

prueba('seleccionar no cambia otro grupo ni añade listeners globales', () => {
    const primero = crearSelector();
    const segundo = crearSelector();
    primero.botones[2].click();
    afirmar.equal(primero.botones[2].atributos['aria-checked'], 'true');
    afirmar.deepEqual(segundo.propiedades, {});
});
