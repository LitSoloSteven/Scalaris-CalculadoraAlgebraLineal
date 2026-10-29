'use strict';
const archivos = require('node:fs');
const rutas = require('node:path');

const css = archivos.readFileSync(rutas.join(__dirname, '../src/frontend/recursos/css/tokens.css'), 'utf8');

function estilosMovimiento() {
    return { getPropertyValue(nombre) {
        const patron = new RegExp(`${nombre}:\\s*([^;]+);`);
        return css.match(patron)?.[1] || '';
    } };
}

module.exports = { estilosMovimiento };
