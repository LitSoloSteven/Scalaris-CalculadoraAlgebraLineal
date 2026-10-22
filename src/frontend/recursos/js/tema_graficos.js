/** Actualización de roles cromáticos de figuras Plotly conectadas al documento. */
'use strict';
{
    const pendientes = new WeakMap();

    function bibliotecaFigura(figura) {
        if (window.Plotly) return window.Plotly;
        if (typeof window.getElement === 'function') return window.getElement(figura)?.Plotly;
        return null;
    }

    function colorRol(rol, tema, graficos) {
        if (rol.startsWith('serie:')) return graficos.paletas[tema][Number(rol.split(':')[1])];
        return graficos[rol][tema];
    }

    async function actualizarTrazas(figura, biblioteca, tema, graficos) {
        if (!biblioteca.restyle) return;
        for (const [indice, traza] of (figura.data || []).entries()) {
            const cambios = {};
            for (const [ruta, rol] of Object.entries(traza.meta?.scalaris_colores || {})) {
                const color = colorRol(rol, tema, graficos);
                cambios[ruta] = ruta === 'colorscale' ? [[[0, color], [1, color]]] : color;
            }
            if (Object.keys(cambios).length) await biblioteca.restyle(figura, cambios, [indice]);
        }
    }

    function coloresEjes(tema, graficos) {
        const texto = graficos.texto?.[tema] || graficos.texto?.papel;
        const cuadricula = graficos.cuadricula?.[tema] || graficos.cuadricula?.papel;
        const cambios = { 'font.color': texto };
        for (const eje of ['xaxis', 'yaxis', 'scene.xaxis', 'scene.yaxis', 'scene.zaxis']) {
            cambios[eje + '.color'] = texto;
            cambios[eje + '.gridcolor'] = cuadricula;
            cambios[eje + '.zerolinecolor'] = texto;
        }
        return cambios;
    }

    async function actualizarFigura(figura, tema, graficos) {
        if (!figura.isConnected || !figura._fullLayout) return;
        const biblioteca = bibliotecaFigura(figura);
        if (!biblioteca?.relayout) return;
        await biblioteca.relayout(figura, coloresEjes(tema, graficos));
        await actualizarTrazas(figura, biblioteca, tema, graficos);
    }

    function programarFigura(figura, tema, graficos) {
        const anterior = pendientes.get(figura);
        const actualizar = () => actualizarFigura(figura, tema, graficos);
        pendientes.set(figura, anterior || Promise.resolve());
        const siguiente = anterior ? anterior.catch(() => {}).then(actualizar) : actualizar();
        pendientes.set(figura, siguiente);
        const limpiar = () => {
            if (pendientes.get(figura) === siguiente) pendientes.delete(figura);
        };
        siguiente.then(limpiar, limpiar);
        return siguiente;
    }

    function registrarTemaGraficos() {
        /** Sincroniza montajes tardíos sin repetir los eventos del propio recoloreado. */
        window.scalaris.sincronizarTemaPlotly = function () {
            const tema = document.documentElement.getAttribute('data-tema') || 'papel';
            const graficos = window.scalaris.graficos;
            const figuras = Array.from(document.querySelectorAll('.js-plotly-plot')).filter(figura =>
                !pendientes.has(figura) && figura.layout?.font?.color !== graficos.texto[tema]);
            return Promise.allSettled(figuras.map(figura => programarFigura(figura, tema, graficos)));
        };

        window.scalaris.actualizarTemaPlotly = function (tema) {
            const graficos = window.scalaris.graficos || {};
            const actualizaciones = Array.from(document.querySelectorAll('.js-plotly-plot'))
                .map(figura => programarFigura(figura, tema, graficos));
            return Promise.allSettled(actualizaciones);
        };
    }

    registrarTemaGraficos();
}
