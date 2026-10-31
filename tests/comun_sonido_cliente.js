'use strict';

/** Crea una superficie de eventos observable para los escenarios de audio y preferencia. */
function superficie() {
    const manejadores = new Map();
    return {
        hidden: false,
        addEventListener(nombre, funcion) {
            const funciones = manejadores.get(nombre) || new Set();
            funciones.add(funcion);
            manejadores.set(nombre, funciones);
        },
        removeEventListener(nombre, funcion) { manejadores.get(nombre)?.delete(funcion); },
        emitir(nombre, datos = {}) { manejadores.get(nombre)?.forEach(funcion => funcion(datos)); },
        contar(nombre) { return manejadores.get(nombre)?.size || 0; }
    };
}

module.exports = { superficie };
