"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");
const { crearTemaSimulado } = require("./comun_tema_cliente.js");

prueba("los valores de tema retirados no se traducen mediante alias", () => {
    for (const almacenado of ["claro", "aqua", "oscuro"]) {
        const cliente = crearTemaSimulado(almacenado);
        cargarAssetCliente("inicializacion_tema.js", cliente.contexto);
        afirmar.equal(cliente.atributos.get("data-tema"), almacenado);
        afirmar.equal(cliente.almacen.get("tema"), almacenado);
        afirmar.equal(cliente.documento.documentElement.style.colorScheme, "light");
    }
});
