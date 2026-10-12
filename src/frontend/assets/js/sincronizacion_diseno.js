'use strict';
{
    window.scalaris = window.scalaris || {};
    window.scalaris.diseno = {
        emitir: function(motivo) {
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    setTimeout(() => {
                        document.dispatchEvent(new CustomEvent('scalaris:layout', { detail: { motivo } }));
                    }, 120);
                });
            });
        }
    };

    let temporizadorRedimension;
    function redimensionarGraficos() {
        clearTimeout(temporizadorRedimension);
        temporizadorRedimension = setTimeout(() => {
            const graficos = document.querySelectorAll('.js-plotly-plot');
            graficos.forEach(grafico => {
                if (grafico.isConnected && window.Plotly) {
                    try {
                        const es3D = grafico._fullLayout && grafico._fullLayout._has && grafico._fullLayout._has('gl3d');
                        if (es3D) {
                            setTimeout(() => {
                                if (grafico.isConnected) Plotly.Plots.resize(grafico);
                            }, 250);
                        } else {
                            Plotly.Plots.resize(grafico);
                        }
                    } catch (e) {}
                }
            });
        }, 120);
    }

    document.addEventListener('scalaris:layout', redimensionarGraficos);
    document.addEventListener('scalaris:glosa', redimensionarGraficos);

    const observadorRedimension = new ResizeObserver((entradas) => {
        let debeRedimensionar = false;
        for (let entrada of entradas) {
            if (entrada.target.classList.contains('js-plotly-plot')) {
                debeRedimensionar = true;
                break;
            }
        }
        if (debeRedimensionar) redimensionarGraficos();
    });

    let escaneoPendiente = false;
    function escanearGraficos() {
        document.querySelectorAll('.js-plotly-plot').forEach(grafico => {
            observadorRedimension.observe(grafico);
        });
        escaneoPendiente = false;
    }

    const observadorMutaciones = new MutationObserver((mutaciones) => {
        let nodosNuevos = false;
        for (let mutacion of mutaciones) {
            if (mutacion.addedNodes.length > 0) {
                nodosNuevos = true;
                break;
            }
        }
        if (nodosNuevos && !escaneoPendiente) {
            escaneoPendiente = true;
            requestAnimationFrame(escanearGraficos);
        }
    });

    observadorMutaciones.observe(document.documentElement, { childList: true, subtree: true });
    document.addEventListener('DOMContentLoaded', escanearGraficos);
    escanearGraficos();
}
