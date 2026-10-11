/**
 * Scalaris - Conmutación de temas con fundido de opacidad
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  var mapa = { claro: 'papel', aqua: 'marea', oscuro: 'medianoche' };
  var t = localStorage.getItem('theme') || 'papel';
  if (mapa[t]) {
    t = mapa[t];
    localStorage.setItem('theme', t);
  }
  var r = document.documentElement;
  r.setAttribute('data-theme', t);
  r.style.colorScheme = (t === 'medianoche') ? 'dark' : 'light';

  function applyTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    document.documentElement.style.colorScheme = (themeName === 'medianoche') ? 'dark' : 'light';
    localStorage.setItem('theme', themeName);

    var logoSrc = (themeName === 'medianoche') ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
    document.querySelectorAll('img.brand-logo-reactive').forEach(function (img) {
      img.src = logoSrc;
    });

    if (window.scalaris && window.scalaris.actualizarTemaPlotly) {
      setTimeout(function () {
        window.scalaris.actualizarTemaPlotly(themeName);
      }, 50);
    }
  }

  function setTheme(themeName) {
    if (!document.startViewTransition) {
      applyTheme(themeName);
      return;
    }

    var transition = document.startViewTransition(function () {
      applyTheme(themeName);
    });

    transition.ready.then(function () {
      var dur = 240;
      document.documentElement.animate(
        [
          { opacity: 0 },
          { opacity: 1 }
        ],
        {
          duration: dur,
          easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
          pseudoElement: '::view-transition-new(root)'
        }
      );
    }).catch(function () {
      applyTheme(themeName);
    });
  }

  window.scalaris.tema = {
    aplicar: applyTheme,
    establecer: setTheme
  };
})();
