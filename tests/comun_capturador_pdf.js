'use strict';
const {cargarAssetCliente} = require('./comun_cliente_javascript.js');

/** Monta las dependencias reales con fotogramas y cesiones simulados sin reloj de pared. */
function cargarCapturadorPdf(contexto) {
    contexto.window.requestAnimationFrame ||= resolver => resolver();
    contexto.window.scheduler ||= {yield: async () => {}};
    cargarAssetCliente('clon_pdf.js', contexto);
    cargarAssetCliente('captura_pdf.js', contexto);
}

module.exports = {cargarCapturadorPdf};
