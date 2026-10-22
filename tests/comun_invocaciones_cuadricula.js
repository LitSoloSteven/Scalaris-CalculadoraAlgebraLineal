"use strict";

const sistemaArchivos = require("node:fs");
const maquinaVirtual = require("node:vm");
const { crearCuadriculaSimulada, crearCeldaCuadricula } = require("./comun_cuadricula_cliente.js");

/** Ejecuta el JavaScript emitido por los consumidores Python contra los assets reales. */
async function comprobarInvocacion(codigo, ubicaciones = null) {
    const cliente = crearCuadriculaSimulada();
    const celdas = (ubicaciones || [{}]).map(ubicacion => ({ ...crearCeldaCuadricula(), ubicacion }));
    const selectores = [];
    cliente.documento.querySelectorAll = selector => {
        selectores.push(selector);
        return celdas.filter(celda => coincideUbicacion(celda.ubicacion, selector)).map(celda => celda.entrada);
    };
    await maquinaVirtual.runInContext(`(async function () { ${codigo} })()`, cliente.contexto);
    const observacion = {
        selectores,
        duraciones: celdas.flatMap(celda => celda.control.animaciones.map(animacion => animacion.opciones.duration)),
        inyeccion: cliente.contexto.inyeccion_detectada === true,
    };
    if (ubicaciones) observacion.animaciones_por_celda = celdas.map(celda => celda.control.animaciones.length);
    return observacion;
}

function coincideUbicacion(ubicacion, selector) {
    const panel = selector.match(/^#([^ ]+)/)?.[1];
    const indice = selector.match(/data-geometria-indice=['"]([^'"]*)/)?.[1];
    return (ubicacion.panel === undefined || panel === undefined || ubicacion.panel === panel) &&
        (ubicacion.indice === undefined || indice === undefined || ubicacion.indice === indice);
}

/** Comprueba las invocaciones de pruebas recibidas y devuelve observaciones serializables. */
async function comprobarInvocaciones() {
    const codigos = JSON.parse(sistemaArchivos.readFileSync(0, "utf8"));
    const observaciones = [];
    for (const invocacion of codigos) {
        const datos = typeof invocacion === "string" ? { codigo: invocacion } : invocacion;
        observaciones.push(await comprobarInvocacion(datos.codigo, datos.ubicaciones));
    }
    process.stdout.write(JSON.stringify(observaciones));
}

if (require.main === module) {
    comprobarInvocaciones().catch(error => { process.stderr.write(String(error)); process.exitCode = 1; });
}

module.exports = { comprobarInvocacion };
