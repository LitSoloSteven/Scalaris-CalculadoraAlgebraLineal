/** Renderizado de fórmulas con espera limitada por disponibilidad de MathJax. */
(function registrarRenderizadoMathJax() {
    'use strict';
    window.scalaris.renderizarMathJax = function (idsElementos, esperaMaximaMs) {
        esperaMaximaMs = esperaMaximaMs || 5000;
        var inicio = Date.now();
        function intentar() {
            if (window.MathJax && window.MathJax.typesetPromise) {
                if (idsElementos && idsElementos.length) {
                    var elementos = idsElementos.map(function (id) {
                        return document.getElementById(id);
                    }).filter(Boolean);
                    if (elementos.length > 0) {
                        window.MathJax.typesetClear(elementos);
                        window.MathJax.typesetPromise(elementos).catch(function () {});
                    } else if (Date.now() - inicio < esperaMaximaMs) {
                        setTimeout(intentar, 100);
                    }
                } else {
                    window.MathJax.typesetClear();
                    window.MathJax.typesetPromise().catch(function () {});
                }
            } else if (Date.now() - inicio < esperaMaximaMs) {
                setTimeout(intentar, 100);
            }
        }
        intentar();
    };
})();
