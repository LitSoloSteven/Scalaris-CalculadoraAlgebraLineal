/** Actualización de colores de figuras Plotly ya conectadas al documento. */
(function registrarTemaGraficos() {
    'use strict';
    window.scalaris.actualizarTemaPlotly = function (tema) {
        var graficos = window.scalaris.graficos || {};
        var colorTexto = (graficos.texto && graficos.texto[tema]) || '#23262E';
        var colorCuadricula = (graficos.cuadricula && graficos.cuadricula[tema]) || 'rgba(128,128,128,0.2)';
        document.querySelectorAll('.js-plotly-plot').forEach(function (figura) {
            if (!figura.isConnected || !figura._fullLayout) return;
            if (window.Plotly && window.Plotly.relayout) {
                try {
                    Plotly.relayout(figura, {
                        'font.color': colorTexto,
                        'scene.xaxis.gridcolor': colorCuadricula,
                        'scene.yaxis.gridcolor': colorCuadricula,
                        'scene.zaxis.gridcolor': colorCuadricula
                    }).catch(function () {});
                } catch (error) {}
            }
        });
    };
})();
