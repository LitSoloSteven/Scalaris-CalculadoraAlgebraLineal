/**
 * Scalaris - Interacciones globales de la aplicación y utilidades
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  document.addEventListener('keydown', function () {
    document.documentElement.setAttribute('data-input', 'keyboard');
  }, { capture: true, passive: true });

  document.addEventListener('pointerdown', function () {
    document.documentElement.setAttribute('data-input', 'pointer');
  }, { capture: true, passive: true });

  window.scalaris.movimiento = {
    rapido: 120,
    medio: 240,
    lento: 250,
    permitido: function () {
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return false;
      }
      return document.documentElement.getAttribute('data-input') !== 'keyboard';
    }
  };

  window.scalaris.navegacion = {
    centrarActivo: function () {
      var el = document.querySelector('.nav-items .nav-active');
      if (el) {
        el.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'auto' });
      }
    }
  };

  window.scalaris.reproducirAnimacionResultado = function (idElemento) {
    var el = document.getElementById(idElemento);
    if (!el) return;
    el.classList.remove('animate-slide-up');
    void el.offsetWidth;
    el.classList.add('animate-slide-up');
    var alFinalizar = function (e) {
      if (e.target !== el) return;
      el.classList.remove('animate-slide-up');
      el.removeEventListener('animationend', alFinalizar);
    };
    el.addEventListener('animationend', alFinalizar);
  };

  window.scalaris.ultimoClic = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
  document.addEventListener('click', function (e) {
    window.scalaris.ultimoClic = { x: e.clientX, y: e.clientY };
  }, { capture: true });

  function ajustarTooltipCelda(e) {
    var target = e.target;
    if (target && target.matches && target.matches('.matrix-input input')) {
      if (target.scrollWidth > target.clientWidth) {
        target.title = target.value || '';
      } else if (target.hasAttribute('title')) {
        target.removeAttribute('title');
      }
    }
  }
  document.addEventListener('mouseover', ajustarTooltipCelda);
  document.addEventListener('focusin', ajustarTooltipCelda);

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

  window.scalaris.efectoMaquinaEscribir = function (idElemento, texto, velocidad) {
    velocidad = velocidad || 18;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var elem = document.getElementById(idElemento);
      if (elem) elem.textContent = texto;
      return;
    }
    var el = document.getElementById(idElemento);
    if (!el) return;

    el.innerHTML = '<span class="tw-text"></span><span class="tw-cursor">▌</span>';
    var textSpan = el.querySelector('.tw-text');
    var cursorSpan = el.querySelector('.tw-cursor');
    var indice = 0;

    var saltar = function () {
      textSpan.textContent = texto;
      cursorSpan.style.display = 'none';
      el.removeEventListener('click', saltar);
    };
    el.addEventListener('click', saltar);

    function escribir() {
      if (indice < texto.length) {
        textSpan.textContent += texto.charAt(indice);
        indice++;
        setTimeout(escribir, velocidad);
      } else {
        cursorSpan.style.display = 'none';
        el.removeEventListener('click', saltar);
      }
    }
    escribir();
  };

  window.scalaris.actualizarTemaPlotly = function (tema) {
    var g = window.scalaris.graficos || {};
    var colorTexto = (g.texto && g.texto[tema]) || '#23262E';
    var colorCuadricula = (g.cuadricula && g.cuadricula[tema]) || 'rgba(128,128,128,0.2)';

    document.querySelectorAll('.js-plotly-plot').forEach(function (plot) {
      if (!plot.isConnected || !plot._fullLayout) return;
      if (window.Plotly && window.Plotly.relayout) {
        try {
          Plotly.relayout(plot, {
            'font.color': colorTexto,
            'scene.xaxis.gridcolor': colorCuadricula,
            'scene.yaxis.gridcolor': colorCuadricula,
            'scene.zaxis.gridcolor': colorCuadricula
          }).catch(function () {});
        } catch (e) {}
      }
    });
  };

  /* Modal y elementos superpuestos emplean tokens estandar como var(--z-modal) */
})();
