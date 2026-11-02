'use strict';
const { readFileSync: leerArchivo } = require('node:fs');

/** Inyecta el mismo bloque JSON que entrega la cabecera de producción. */
function inyectarCatalogo(documento, cambios = {}) {
    const anterior = documento.getElementById?.bind(documento);
    documento.getElementById = identificador => identificador === 'scalaris-configuracion-sonidos' ? {
        textContent: JSON.stringify({ ...JSON.parse(leerArchivo('src/frontend/recursos/catalogo_sonidos.json', 'utf8')), ...cambios })
    } : anterior?.(identificador);
}

module.exports = { inyectarCatalogo };
