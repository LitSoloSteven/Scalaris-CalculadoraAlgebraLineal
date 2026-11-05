const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const recursos = path.join(__dirname, "../src/frontend/recursos/js");

function cargar(archivo, contexto = {}) {
    const ventana = { scalaris: {} };
    vm.runInNewContext(fs.readFileSync(path.join(recursos, archivo), "utf8"), { window: ventana, ...contexto });
    return ventana;
}

test("proyecta la pulsación según la escala y descarta arrastres, barra y márgenes", () => {
    const ventana = cargar("grafico_biseccion.js");
    const seleccion = ventana.scalaris.graficoBiseccion;
    const grafico = {
        closest: () => ({}),
        _fullLayout: {
            xaxis: { _offset: 30, _length: 200, p2l: pixel => -5 + pixel / 20 },
            yaxis: { _offset: 20, _length: 100 },
        },
        getBoundingClientRect: () => ({ left: 10, top: 5 }),
    };
    const evento = {
        currentTarget: grafico, target: { closest: () => null },
        isPrimary: true, button: 0, clientX: 140, clientY: 50,
    };
    seleccion.iniciar(evento);
    assert.equal(seleccion.abscisa(evento), 0);
    seleccion.iniciar(evento);
    assert.equal(seleccion.abscisa({ ...evento, clientX: 158 }), null);
    const margen = { ...evento, clientX: 20 };
    seleccion.iniciar(margen);
    assert.equal(seleccion.abscisa(margen), null);
    const barra = { ...evento, target: { closest: () => ({}) } };
    seleccion.iniciar(barra);
    assert.equal(seleccion.abscisa(barra), null);
});

test("limpia MathJax por región y omite trabajo encolado ya desmontado", async () => {
    const regiones = new Map();
    let observar;
    class Observador {
        constructor(callback) { observar = callback; }
        observe() {}
        disconnect() {}
    }
    const ventana = cargar("renderizado_mathjax.js", {
        document: { body: {}, getElementById: id => regiones.get(id) },
        MutationObserver: Observador,
    });
    const llamadas = [];
    ventana.MathJax = {
        typesetPromise: ([region]) => llamadas.push("renderizar:" + region.id),
        typesetClear: ([region]) => llamadas.push("limpiar:" + region.id),
    };
    const anterior = { id: "anterior", isConnected: true };
    const actual = { id: "actual", isConnected: true };
    regiones.set(anterior.id, anterior);
    regiones.set(actual.id, actual);
    ventana.scalaris.renderizarMathJaxVigente(anterior.id);
    anterior.isConnected = false;
    observar();
    ventana.scalaris.renderizarMathJaxVigente(actual.id);
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(llamadas, ["limpiar:anterior", "renderizar:actual"]);
});
