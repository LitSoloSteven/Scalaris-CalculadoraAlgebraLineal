"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { analizarJavascript } = require("./comun_auditoria_javascript.js");

prueba("la IIFE se mide completa aunque sus funciones interiores sean pequeñas", () => {
    const contenido = "(() => {\n" + "void 1;\n".repeat(41) + "})();";
    const resumen = analizarJavascript(contenido);
    afirmar.equal(resumen.funciones[0].lineas, 43);
    afirmar.equal(resumen.funciones[0].complejidad, 1);
});

prueba("las firmas cuentan desestructuración y argumentos variádicos", () => {
    const resumen = analizarJavascript("const recibir = ({dato}, [valor], tercero, cuarto, quinto, ...otros) => dato;");
    afirmar.equal(resumen.funciones[0].parametros, 6);
});

prueba("cuatro niveles anidados y once decisiones no se reducen al medir", () => {
    const anidado = analizarJavascript("function recibir() { if (uno) { while (dos) { for (;;) { if (tres) actuar(); } } } }");
    const complejo = analizarJavascript("function recibir() { " + "if (activo) actuar();".repeat(10) + " }");
    afirmar.equal(anidado.funciones[0].anidamiento, 4);
    afirmar.equal(complejo.funciones[0].complejidad, 11);
});

prueba("una clase conserva el tamaño físico de doscientos un líneas", () => {
    const resumen = analizarJavascript("class Cliente {\n" + "dato;\n".repeat(199) + "}");
    afirmar.equal(resumen.clases[0].lineas, 201);
});

prueba("el retorno externo solo se permite para el código emitido por NiceGUI", () => {
    afirmar.throws(() => analizarJavascript("return 1;"), SyntaxError);
    const resumen = analizarJavascript("return () => activo ? 1 : 0;", { allowReturnOutsideFunction: true });
    afirmar.equal(resumen.funciones.length, 1);
    afirmar.equal(resumen.funciones[0].complejidad, 2);
});
