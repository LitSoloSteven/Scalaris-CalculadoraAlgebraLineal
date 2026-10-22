/** Renderizado de fórmulas con espera limitada por disponibilidad de MathJax. */
(function registrarRenderizadoMathJax() {
    'use strict';
    window.scalaris.renderizarMathJax = function (identificadoresElementos, esperaMaximaMs) {
        esperaMaximaMs = esperaMaximaMs || 5000;
        var inicio = Date.now();
        function intentar() {
            if (window.MathJax && window.MathJax.typesetPromise) {
                if (identificadoresElementos && identificadoresElementos.length) {
                    var elementos = identificadoresElementos.map(function (identificador) {
                        return document.getElementById(identificador);
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
