"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

/** Ejecuta el activo real con almacenamiento observable. */
function crearRecientes(almacenado = null) {
    const almacen = new Map();
    if (almacenado !== null) almacen.set("scalaris:recientes", almacenado);
    const ventana = {};
    const contexto = maquinaVirtual.createContext({
        window: ventana,
        localStorage: { getItem: clave => almacen.get(clave) ?? null,
            setItem: (clave, valor) => almacen.set(clave, valor) },
    });
    cargarAssetCliente("inicio_recientes.js", contexto);
    return { almacen, recientes: ventana.scalaris.recientes };
}

prueba("las visitas se guardan en orden sin duplicados y con límite de cuatro", () => {
    const cliente = crearRecientes();
    for (const nombre of ["sistemas", "inversa", "vectores", "matrices", "bases", "inversa"]) {
        cliente.recientes.registrar(nombre);
    }
    afirmar.deepEqual(JSON.parse(cliente.almacen.get("scalaris:recientes")),
        ["inversa", "bases", "matrices", "vectores"]);
    const resultado = cliente.recientes.leer();
    afirmar.equal(resultado.valido, true);
    afirmar.deepEqual(Array.from(resultado.identificadores), ["inversa", "bases", "matrices", "vectores"]);
    afirmar.equal(Object.hasOwn(resultado, "ids"), false);
});

prueba("el registro recupera almacenamiento corrupto sin propagar errores", () => {
    for (const almacenado of ["{", "null", "{}", '"sistemas"']) {
        const cliente = crearRecientes(almacenado);
        afirmar.equal(cliente.recientes.leer().valido, false);
        afirmar.doesNotThrow(() => cliente.recientes.registrar("sistemas"));
        afirmar.deepEqual(JSON.parse(cliente.almacen.get("scalaris:recientes")), ["sistemas"]);
    }
});

prueba("los elementos ajenos a cadenas se filtran y las visitas inválidas no escriben", () => {
    const cliente = crearRecientes('["inversa",3,null,"vectores"]');
    afirmar.deepEqual(Array.from(cliente.recientes.leer().identificadores), ["inversa", "vectores"]);
    for (const visita of [null, undefined, 3, {}, ""]) cliente.recientes.registrar(visita);
    afirmar.equal(cliente.almacen.get("scalaris:recientes"), '["inversa",3,null,"vectores"]');
    cliente.recientes.registrar("bases");
    afirmar.deepEqual(JSON.parse(cliente.almacen.get("scalaris:recientes")), ["bases", "inversa", "vectores"]);
});
