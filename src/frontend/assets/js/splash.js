/**
 * Scalaris - Animación de inicio de aplicación
 */
(function () {
  'use strict';

  if (location.pathname !== '/' || (location.search && location.search !== '')) {
    sessionStorage.setItem('splash-shown', '1');
    return;
  }
  if (sessionStorage.getItem('splash-shown')) return;
  sessionStorage.setItem('splash-shown', '1');

  var tema = document.documentElement.getAttribute('data-theme');
  var logo = (tema === 'medianoche') ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';

  var overlay = document.createElement('div');
  overlay.id = 'agy-splash-overlay';
  overlay.style.cssText = 'position: fixed; inset: 0; z-index: 99999; background: var(--bg-page); display: flex; flex-direction: column; align-items: center; justify-content: center; view-transition-name: none; transform-origin: center;';

  overlay.innerHTML =
    '<div style="position: relative; display: flex; align-items: center; justify-content: center; width: 120px; height: 120px;">' +
      '<img id="splash-logo" src="' + logo + '" style="width: 80px; height: 80px; object-fit: contain; opacity: 1; transform: scale(1);" alt="Scalaris Logo">' +
    '</div>' +
    '<div style="margin-top: 16px; font-family: \'Space Grotesk\', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;">' +
      '<span id="splash-t1" style="font-size: 28px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-main); display: inline-block;">Scalaris</span>' +
      '<span id="splash-t2" style="font-size: 11px; font-weight: 700; letter-spacing: 0.25em; text-transform: uppercase; color: var(--accent); margin-top: 2px;">UAM</span>' +
    '</div>';

  document.documentElement.appendChild(overlay);

  setTimeout(function () {
    var anim = overlay.animate(
      [{ opacity: 1 }, { opacity: 0 }],
      { duration: 240, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'forwards' }
    );
    anim.finished.then(function () {
      overlay.remove();
    }).catch(function () {
      overlay.remove();
    });
  }, 300);
})();
