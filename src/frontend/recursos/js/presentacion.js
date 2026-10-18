(function () {
  'use strict';

  if (location.pathname !== '/' || (location.search && location.search !== '')) {
    sessionStorage.setItem('presentacion-mostrada', '1');
    return;
  }
  if (sessionStorage.getItem('presentacion-mostrada')) return;
  sessionStorage.setItem('presentacion-mostrada', '1');

  var tema = document.documentElement.getAttribute('data-tema');
  var logotipo = (tema === 'medianoche') ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';

  var fondo = document.createElement('div');
  fondo.id = 'aplicacion-presentacion-fondo';
  fondo.style.cssText = 'position: fixed; inset: 0; z-index: 99999; background: var(--bg-page); display: flex; flex-direction: column; align-items: center; justify-content: center; view-transition-name: none; transform-origin: center;';

  fondo.innerHTML =
    '<div style="position: relative; display: flex; align-items: center; justify-content: center; width: 120px; height: 120px;">' +
      '<img id="presentacion-logotipo" src="' + logotipo + '" style="width: 80px; height: 80px; object-fit: contain; opacity: 1; transform: scale(1);" alt="Scalaris Logo">' +
    '</div>' +
    '<div style="margin-top: 16px; font-family: \'Space Grotesk\', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;">' +
      '<span id="presentacion-nombre" style="font-size: 28px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-main); display: inline-block;">Scalaris</span>' +
      '<span id="presentacion-organizacion" style="font-size: 11px; font-weight: 700; letter-spacing: 0.25em; text-transform: uppercase; color: var(--accent); margin-top: 2px;">UAM</span>' +
    '</div>';

  document.documentElement.appendChild(fondo);

  setTimeout(function () {
    var animacion = fondo.animate(
      [{ opacity: 1 }, { opacity: 0 }],
      { duration: 240, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards' }
    );
    animacion.finished.then(function () {
      fondo.remove();
    }).catch(function () {
      fondo.remove();
    });
  }, 300);
})();
