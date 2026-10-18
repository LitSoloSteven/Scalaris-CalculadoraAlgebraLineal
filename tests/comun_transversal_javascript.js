"use strict";
const analizador = require("internal/deps/acorn/acorn/dist/acorn");
const sistemaArchivos = require("node:fs");

function hijos(nodo) {
    return Object.values(nodo).flatMap(valor => Array.isArray(valor)
        ? valor.filter(hijo => hijo && typeof hijo.type === "string")
        : valor && typeof valor.type === "string" ? [valor] : []);
}

function nombresPatron(nodo) {
    if (!nodo) return [];
    if (nodo.type === "Identifier") return [{ nombre: nodo.name, linea: nodo.loc.start.line }];
    if (nodo.type === "Property") return nombresPatron(nodo.value);
    if (nodo.type === "AssignmentPattern") return nombresPatron(nodo.left);
    return hijos(nodo).flatMap(nombresPatron);
}

function declaraciones(nodo) {
    if (nodo.type === "VariableDeclarator") return nombresPatron(nodo.id);
    if (["FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"].includes(nodo.type)) {
        return [...nombresPatron(nodo.id), ...nodo.params.flatMap(nombresPatron)];
    }
    if (nodo.type === "CatchClause") return nombresPatron(nodo.param);
    return [];
}

function claveBloque(sentencias) {
    return JSON.stringify(sentencias, (clave, valor) =>
        ["start", "end", "loc", "raw"].includes(clave) ? undefined : valor);
}

function registrarBloques(sentencias, fuente, bloques) {
    if (!sentencias.length || !sentencias.every(nodo => nodo &&
        (/Statement$/.test(nodo.type) || nodo.type === "VariableDeclaration"))) return;
    for (let inicio = 0; inicio < sentencias.length; inicio++) {
        for (let fin = inicio + 1; fin <= sentencias.length; fin++) {
            const primero = sentencias[inicio].loc.start.line;
            const ultimo = sentencias[fin - 1].loc.end.line;
            if (ultimo - primero + 1 < 5) continue;
            const clave = claveBloque(sentencias.slice(inicio, fin));
            if (!bloques.has(clave)) bloques.set(clave, []);
            bloques.get(clave).push({ ruta: fuente.ruta, inicio: fuente.linea + primero - 1,
                fin: fuente.linea + ultimo - 1 });
        }
    }
}

function visitar(nodo, fuente, resumen, bloques) {
    resumen.nombres.push(...declaraciones(nodo));
    for (const valor of Object.values(nodo)) {
        if (Array.isArray(valor)) registrarBloques(valor, fuente, bloques);
    }
    for (const hijo of hijos(nodo)) visitar(hijo, fuente, resumen, bloques);
}

function analizarFuentes(fuentes) {
    const bloques = new Map();
    const resultados = fuentes.map(fuente => {
        const resumen = { ruta: fuente.ruta, linea: fuente.linea, nombres: [], comentarios: [] };
        const arbol = analizador.parse(fuente.contenido, {
            ecmaVersion: "latest", sourceType: "module", locations: true,
            allowReturnOutsideFunction: fuente.origen === "python",
            onComment: resumen.comentarios,
        });
        visitar(arbol, fuente, resumen, bloques);
        return resumen;
    });
    const duplicaciones = [...bloques.values()].filter(grupo => grupo.length > 1);
    return { resultados, duplicaciones };
}

module.exports = { analizarFuentes };
if (require.main === module) {
    process.stdout.write(JSON.stringify(analizarFuentes(JSON.parse(sistemaArchivos.readFileSync(0, "utf8")))));
}
