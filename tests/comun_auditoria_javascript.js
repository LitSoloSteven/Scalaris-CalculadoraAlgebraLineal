"use strict";

const analizador = require("internal/deps/acorn/acorn/dist/acorn");
const sistemaArchivos = require("node:fs");

const TIPOS_FUNCION = new Set([
    "FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression",
]);
const TIPOS_BLOQUE = new Set([
    "IfStatement", "ForStatement", "ForInStatement", "ForOfStatement",
    "WhileStatement", "DoWhileStatement", "TryStatement", "WithStatement",
    "SwitchStatement",
]);
const TIPOS_DECISION = new Set([
    "IfStatement", "ForStatement", "ForInStatement", "ForOfStatement",
    "WhileStatement", "DoWhileStatement", "CatchClause", "ConditionalExpression",
]);

/** Devuelve los hijos sintácticos sin confundir posiciones con nodos. */
function hijosSintacticos(nodo) {
    const hijos = [];
    for (const valor of Object.values(nodo)) {
        if (Array.isArray(valor)) {
            hijos.push(...valor.filter(esNodoSintactico));
        } else if (esNodoSintactico(valor)) {
            hijos.push(valor);
        }
    }
    return hijos;
}

/** Identifica objetos de nodos del contrato ESTree del parser. */
function esNodoSintactico(valor) {
    return valor !== null && typeof valor === "object" && typeof valor.type === "string";
}

/** Cuenta decisiones de un nodo, incluidos operadores y ramas de selección. */
function decisionesNodo(nodo) {
    if (TIPOS_DECISION.has(nodo.type)) return 1;
    if (nodo.type === "LogicalExpression") return 1;
    if (nodo.type === "SwitchCase" && nodo.test !== null) return 1;
    return 0;
}

/** Acumula métricas de un cuerpo sin incluir funciones o clases interiores. */
function visitarComplejidad(nodo, profundidad, resumen, ramaAlternativa = false) {
    if (TIPOS_FUNCION.has(nodo.type) || nodo.type.startsWith("Class")) return;
    const siguiente = profundidad + Number(TIPOS_BLOQUE.has(nodo.type) && !ramaAlternativa);
    resumen.anidamiento = Math.max(resumen.anidamiento, siguiente);
    resumen.complejidad += decisionesNodo(nodo);
    for (const hijo of hijosSintacticos(nodo)) {
        const esAlternativa = nodo.type === "IfStatement" && hijo === nodo.alternate
            && hijo.type === "IfStatement";
        visitarComplejidad(hijo, siguiente, resumen, esAlternativa);
    }
}

/** Describe una función o callback con límites físicos y estructurales. */
function describirFuncion(nodo, nombreAsignado) {
    const resumen = { anidamiento: 0, complejidad: 1 };
    for (const parametro of nodo.params) visitarComplejidad(parametro, 0, resumen);
    visitarComplejidad(nodo.body, 0, resumen);
    return {
        nombre: nodo.id?.name || nombreAsignado || "funcion_anonima",
        linea: nodo.loc.start.line,
        lineas: nodo.loc.end.line - nodo.loc.start.line + 1,
        parametros: nodo.params.length,
        ...resumen,
    };
}

/** Obtiene el nombre de una función ligada a variable, propiedad o método. */
function nombreFuncionLigada(nodo, padre) {
    if (!padre) return "";
    if (padre.type === "VariableDeclarator" && padre.init === nodo) {
        return padre.id.name || "variable_desestructurada";
    }
    if ((padre.type === "Property" || padre.type === "MethodDefinition") && padre.value === nodo) {
        return padre.key.name || String(padre.key.value);
    }
    return "";
}

/** Recorre declaraciones, callbacks, métodos y clases del archivo completo. */
function recogerDeclaraciones(nodo, resumen, padre = null) {
    if (TIPOS_FUNCION.has(nodo.type)) {
        resumen.funciones.push(describirFuncion(nodo, nombreFuncionLigada(nodo, padre)));
    }
    if (nodo.type === "ClassDeclaration" || nodo.type === "ClassExpression") {
        resumen.clases.push({
            nombre: nodo.id?.name || "clase_anonima",
            linea: nodo.loc.start.line,
            lineas: nodo.loc.end.line - nodo.loc.start.line + 1,
        });
    }
    for (const hijo of hijosSintacticos(nodo)) recogerDeclaraciones(hijo, resumen, nodo);
}

/** Analiza texto JavaScript sin ejecutarlo y devuelve sus declaraciones medidas. */
function analizarJavascript(contenido, opciones = {}) {
    const arbol = analizador.parse(contenido, {
        ecmaVersion: "latest", sourceType: "module", locations: true, ...opciones,
    });
    const resumen = { funciones: [], clases: [] };
    recogerDeclaraciones(arbol, resumen);
    return resumen;
}

/** Lee archivos recibidos por entrada estándar y emite métricas JSON. */
function ejecutarAnalisis() {
    const archivos = JSON.parse(sistemaArchivos.readFileSync(0, "utf8"));
    const resultados = archivos.map(archivo => ({
        ruta: archivo.ruta, linea: archivo.linea || 1, origen: archivo.origen || "archivo",
        ...analizarJavascript(archivo.contenido, {
            allowReturnOutsideFunction: archivo.origen === "python",
        }),
    }));
    process.stdout.write(JSON.stringify(resultados));
}

module.exports = { analizarJavascript };
if (require.main === module) ejecutarAnalisis();
