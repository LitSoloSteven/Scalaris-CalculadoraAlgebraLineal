/** Actualización de colores de figuras Plotly ya conectadas al documento. */
(function registrarTemaGraficos() {
    'use strict';
    function bibliotecaFigura(figura) {
        if (window.Plotly) return window.Plotly;
        if (typeof window.getElement === 'function') return window.getElement(figura)?.Plotly;
        return null;
    }

    window.scalaris.actualizarTemaPlotly = function (tema) {
        var graficos = window.scalaris.graficos || {};
        var colorTexto = (graficos.texto && graficos.texto[tema]) || '#23262E';
        var colorCuadricula = (graficos.cuadricula && graficos.cuadricula[tema]) || 'rgba(128,128,128,0.2)';
        var actualizaciones = Array.from(document.querySelectorAll('.js-plotly-plot')).map(function (figura) {
            if (!figura.isConnected || !figura._fullLayout) return;
            try {
                var biblioteca = bibliotecaFigura(figura);
                if (biblioteca && biblioteca.relayout) {
                    return biblioteca.relayout(figura, {
                        'font.color': colorTexto,
                        'scene.xaxis.gridcolor': colorCuadricula,
                        'scene.yaxis.gridcolor': colorCuadricula,
                        'scene.zaxis.gridcolor': colorCuadricula
                    }).catch(function () {});
                }
            } catch (error) {}
        });
        return Promise.allSettled(actualizaciones);
    };
})();
