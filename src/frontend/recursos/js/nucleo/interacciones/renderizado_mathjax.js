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

{
    const regiones = new Map();
    let cola = Promise.resolve();
    let observador;

    function serializar(trabajo) {
        cola = cola.then(trabajo).catch(() => {});
    }

    function limpiarDesmontadas() {
        for (const [identificador, region] of regiones) {
            if (!region.isConnected) {
                regiones.delete(identificador);
                serializar(() => window.MathJax?.typesetClear?.([region]));
            }
        }
        if (!regiones.size) observador.disconnect();
    }

    window.scalaris.renderizarMathJaxVigente = function (identificador) {
        const limite = Date.now() + 5000;
        function esperar() {
            const region = document.getElementById(identificador);
            if (!region?.isConnected || !window.MathJax?.typesetPromise) {
                if (Date.now() < limite) setTimeout(esperar, 100);
                return;
            }
            if (regiones.has(identificador)) return;
            regiones.set(identificador, region);
            observador ??= new MutationObserver(limpiarDesmontadas);
            observador.observe(document.body, { childList: true, subtree: true });
            serializar(() => {
                if (region.isConnected) return window.MathJax.typesetPromise([region]);
            });
        }
        esperar();
    };
}
