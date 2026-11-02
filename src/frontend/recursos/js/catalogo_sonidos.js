/** Comparte el catálogo declarativo sin mantener una segunda copia de perfiles. */
{
    'use strict';
    window.scalaris = window.scalaris || {};

    function congelar(datos) {
        if (datos && typeof datos === 'object') {
            Object.values(datos).forEach(congelar);
            Object.freeze(datos);
        }
        return datos;
    }

    const etiqueta = document.getElementById('scalaris-configuracion-sonidos');
    window.scalaris.catalogoSonidos = congelar(JSON.parse(etiqueta.textContent));
}
