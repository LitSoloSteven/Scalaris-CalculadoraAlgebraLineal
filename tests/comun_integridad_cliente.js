"use strict";

const analizador = require("internal/deps/acorn/acorn/dist/acorn");
const archivos = require("node:fs");

/** Recorre nodos ESTree sin interpretar ni ejecutar los scripts analizados. */
function recorrer(nodo, visitar, padre = null) {
    if (!nodo || typeof nodo.type !== "string") return;
    visitar(nodo, padre);
    for (const valor of Object.values(nodo)) {
        if (Array.isArray(valor)) valor.forEach(hijo => recorrer(hijo, visitar, nodo));
        else if (valor && typeof valor === "object") recorrer(valor, visitar, nodo);
    }
}

/** Obtiene una ruta de propiedades literal, sin confundir acceso con declaración. */
function rutaPropiedad(nodo) {
    if (nodo?.type === "Identifier") return nodo.name;
    if (nodo?.type === "ChainExpression") return rutaPropiedad(nodo.expression);
    if (nodo?.type !== "MemberExpression") return "";
    const base = rutaPropiedad(nodo.object);
    const propiedad = nodo.computed ? nodo.property.value : nodo.property.name;
    return base && typeof propiedad === "string" ? base + "." + propiedad : "";
}

/** Recoge únicamente rutas publicadas por asignación sobre window. */
function registrarObjeto(ruta, valor, publicadas) {
    if (!ruta.startsWith("window.")) return;
    publicadas.add(ruta);
    if (valor?.type !== "ObjectExpression") return;
    for (const propiedad of valor.properties) {
        if (propiedad.type !== "Property") continue;
        const nombre = propiedad.computed ? propiedad.key.value : propiedad.key.name ?? propiedad.key.value;
        if (typeof nombre === "string") registrarObjeto(ruta + "." + nombre, propiedad.value, publicadas);
    }
}

/** Mide el espacio real exportado; funciones internas de IIFE no son globales. */
function publicaciones(contenidos) {
    const publicadas = new Set();
    for (const contenido of contenidos) {
        const arbol = analizador.parse(contenido, { ecmaVersion: "latest", sourceType: "script" });
        recorrer(arbol, nodo => {
            if (nodo.type === "AssignmentExpression") registrarObjeto(rutaPropiedad(nodo.left), nodo.right, publicadas);
        });
        for (const nodo of arbol.body) {
            if (nodo.type === "FunctionDeclaration") publicadas.add(nodo.id.name);
        }
    }
    return [...publicadas];
}

/** Registra enlaces de parámetros y declaraciones, incluida la desestructuración. */
function registrarPatron(patron, nombres) {
    if (!patron) return;
    if (patron.type === "Identifier") nombres.add(patron.name);
    if (patron.type === "RestElement") registrarPatron(patron.argument, nombres);
    if (patron.type === "AssignmentPattern") registrarPatron(patron.left, nombres);
    if (patron.type === "ArrayPattern") patron.elements.forEach(elemento => registrarPatron(elemento, nombres));
    if (patron.type === "ObjectPattern") patron.properties.forEach(propiedad => registrarPatron(propiedad.value ?? propiedad.argument, nombres));
}

/** Distingue bloques léxicos y funciones para resolver var en su ámbito propio. */
function prepararAmbito(nodo, anterior) {
    const funcion = ["Program", "FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"].includes(nodo.type);
    const bloque = ["BlockStatement", "CatchClause", "ForStatement", "ForInStatement", "ForOfStatement", "SwitchStatement"].includes(nodo.type);
    if (!funcion && !bloque) return anterior;
    const ambito = { padre: anterior, nombres: new Set(), funcion };
    if (nodo.params) nodo.params.forEach(parametro => registrarPatron(parametro, ambito.nombres));
    if (nodo.type === "FunctionExpression") registrarPatron(nodo.id, ambito.nombres);
    if (nodo.type === "CatchClause") registrarPatron(nodo.param, ambito.nombres);
    return ambito;
}

/** Construye los ámbitos antes de leer usos para respetar la elevación de enlaces. */
function construirAmbitos(nodo, anterior, ambitos, padre = null) {
    if (!nodo || typeof nodo.type !== "string") return;
    if (nodo.type === "FunctionDeclaration") registrarPatron(nodo.id, anterior.nombres);
    const ambito = prepararAmbito(nodo, anterior);
    ambitos.set(nodo, ambito);
    if (nodo.type === "VariableDeclarator") {
        registrarPatron(nodo.id, ambitoDeclaracion(ambito, padre.kind).nombres);
    }
    for (const valor of Object.values(nodo)) {
        if (Array.isArray(valor)) valor.forEach(hijo => construirAmbitos(hijo, ambito, ambitos, nodo));
        else if (valor && typeof valor === "object") construirAmbitos(valor, ambito, ambitos, nodo);
    }
}

/** Las declaraciones var pertenecen a la función; let y const, al bloque actual. */
function ambitoDeclaracion(ambito, tipo) {
    let destino = ambito;
    if (tipo === "var") { while (!destino.funcion) destino = destino.padre; }
    return destino;
}

/** Busca un nombre solo en el ámbito del uso y sus padres. */
function existeLocal(nombre, ambito) {
    for (let actual = ambito; actual; actual = actual.padre) {
        if (actual.nombres.has(nombre)) return true;
    }
    return false;
}

/** Identifica raíces globales de llamadas y rutas de namespace en un fragmento. */
function referenciasFragmento(contenido) {
    const arbol = analizador.parse(contenido, { ecmaVersion: "latest", allowReturnOutsideFunction: true });
    const ambitos = new WeakMap(), referencias = new Set();
    construirAmbitos(arbol, { nombres: new Set(["__interpolacion__"]), funcion: true }, ambitos);
    recorrer(arbol, nodo => {
        if (nodo.type === "MemberExpression") {
            const ruta = rutaPropiedad(nodo);
            if (ruta.startsWith("window.scalaris.")) referencias.add(ruta);
            else if (nodo.object.type === "Identifier" && !existeLocal(nodo.object.name, ambitos.get(nodo))) referencias.add(nodo.object.name);
        }
        if (nodo.type === "CallExpression" && nodo.callee.type === "Identifier" && !existeLocal(nodo.callee.name, ambitos.get(nodo))) {
            referencias.add(nodo.callee.name);
        }
    });
    return [...referencias];
}

/** Recibe fuentes por stdin y devuelve medición o error sintáctico por fragmento. */
function ejecutar() {
    const entrada = JSON.parse(archivos.readFileSync(0, "utf8"));
    const resultados = entrada.fragmentos.map(fragmento => {
        try { return { referencias: referenciasFragmento(fragmento) }; }
        catch (error) { return { error: error.message }; }
    });
    process.stdout.write(JSON.stringify({ publicadas: publicaciones(entrada.recursos), resultados }));
}

ejecutar();
