"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { analizarJavascript } = require("./comun_auditoria_javascript.js");

prueba("distingue ramas alternativas y condiciones realmente anidadas", () => {
    const alternativas = analizarJavascript("function elegir(valor) { if (valor) {} else if (valor > 2) {} }");
    const anidada = analizarJavascript("function elegir(valor) { if (valor) {} else { if (valor > 2) {} } }");
    afirmar.equal(alternativas.funciones[0].anidamiento, 1);
    afirmar.equal(alternativas.funciones[0].complejidad, 3);
    afirmar.equal(anidada.funciones[0].anidamiento, 2);
});

prueba("incluye callbacks flecha, métodos y parámetros desestructurados", () => {
    const resumen = analizarJavascript("const enviar = ({datos}, ...opciones) => datos; class Cliente { recibir(valor) { return valor; } }");
    afirmar.deepEqual(resumen.funciones.map(funcion => funcion.nombre), ["enviar", "recibir"]);
    afirmar.deepEqual(resumen.funciones.map(funcion => funcion.parametros), [2, 1]);
    afirmar.equal(resumen.clases[0].nombre, "Cliente");
});

prueba("las funciones interiores conservan métricas independientes", () => {
    const resumen = analizarJavascript("function exterior() { function interior(valor) { if (valor) { while (valor) {} } } }");
    afirmar.equal(resumen.funciones[0].complejidad, 1);
    afirmar.equal(resumen.funciones[0].anidamiento, 0);
    afirmar.equal(resumen.funciones[1].complejidad, 3);
    afirmar.equal(resumen.funciones[1].anidamiento, 2);
});

prueba("los literales y comentarios no crean funciones ficticias", () => {
    const resumen = analizarJavascript('const texto = "function falsa(a,b,c,d,e,f) {}"; /* function otra() {} */');
    afirmar.deepEqual(resumen.funciones, []);
    afirmar.throws(() => analizarJavascript("function sinCierre() {"), SyntaxError);
});

prueba("la selección anidada cuenta bloque y cada caso no predeterminado", () => {
    const resumen = analizarJavascript("function elegir(valor) { if (valor) { switch (valor) { case 1: break; case 2: break; default: break; } } }");
    afirmar.equal(resumen.funciones[0].anidamiento, 2);
    afirmar.equal(resumen.funciones[0].complejidad, 4);
});

prueba("las decisiones de parámetros predeterminados participan en complejidad", () => {
    const resumen = analizarJavascript("function elegir(valor = condicion ? primero : segundo) { return valor; }");
    afirmar.equal(resumen.funciones[0].complejidad, 2);
});
