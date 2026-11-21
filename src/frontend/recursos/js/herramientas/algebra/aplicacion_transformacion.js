/** Enlaza la componente vigente con su proyección sin recrear escenas ni cámaras. */
{
'use strict';
const estados = new WeakMap();

function actualizar(identificador, componente) {
    const region = document.getElementById(identificador);
    if (!region?.isConnected) return Promise.resolve();
    const anterior = Number(region.dataset.componenteActiva);
    region.dataset.componenteActiva = String(componente);
    if (anterior !== componente) marcarComponente(region, componente);
    return Promise.allSettled(Array.from(region.querySelectorAll('.js-plotly-plot')).map(sincronizar));
}

function marcarComponente(region, componente) {
    for (const fila of region.querySelectorAll('[data-componente-resultado]')) {
        const activa = Number(fila.dataset.componenteResultado) === componente;
        if (activa) fila.setAttribute('aria-current', 'true');
        else fila.removeAttribute('aria-current');
    }
}

function sincronizar(grafico) {
    if (!grafico?.isConnected || !grafico._fullLayout) return Promise.resolve();
    let estado = estados.get(grafico);
    if (!estado) {
        estado = { componente: -1, pendiente: Promise.resolve() };
        estados.set(grafico, estado);
    }
    const region = grafico.closest('[data-procedimiento-aplicacion]');
    const componente = Number(region?.dataset.componenteActiva ?? -1);
    if (estado.componente === componente) return estado.pendiente;
    estado.pendiente = estado.pendiente.catch(() => {}).then(() => aplicarComponente(grafico, estado));
    return estado.pendiente;
}

async function aplicarComponente(grafico, estado) {
    if (!grafico.isConnected) return;
    const region = grafico.closest('[data-procedimiento-aplicacion]');
    const componente = Number(region?.dataset.componenteActiva ?? -1);
    if (estado.componente === componente) return;
    const indice = grafico.data.findIndex(traza => traza.meta?.scalaris_proyeccion);
    if (indice < 0) return;
    const valores = grafico.data[indice].meta.scalaris_proyeccion;
    const cambios = cambiosProyeccion(valores, componente);
    const biblioteca = window.Plotly || window.getElement?.(grafico)?.Plotly;
    if (!biblioteca?.restyle) return;
    estado.componente = componente;
    await biblioteca.restyle(grafico, cambios, [indice]);
}

function cambiosProyeccion(valores, componente) {
    const visible = Number.isInteger(componente) && componente >= 0 && componente < valores.length;
    const cambios = { visible };
    for (const [indice, eje] of ['x', 'y', 'z'].slice(0, valores.length).entries()) {
        cambios[eje] = [[visible && indice === componente ? valores[indice] : 0]];
    }
    cambios.customdata = [[`Componente ${componente + 1}: proyección sobre su eje (aproximada)`]];
    return cambios;
}

window.scalaris = window.scalaris || {};
window.scalaris.aplicacionTransformacion = { actualizar, sincronizar };
}
