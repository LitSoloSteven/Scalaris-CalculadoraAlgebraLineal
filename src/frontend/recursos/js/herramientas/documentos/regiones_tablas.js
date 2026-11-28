(function () {
  'use strict';

  const regiones = new Map([
    ['.tabla-resultados .q-table__middle', 'Tabla de iteraciones'],
    ['.inversa-desplazamiento', 'Tabla de matriz'],
    ['.numericos-desplazamiento', 'Tabla del procedimiento'],
    ['.iterativos-desplazamiento', 'Tabla de iteraciones'],
  ]);
  const selector = Array.from(regiones.keys()).join(', ');

  function preparar(region) {
    if (region.closest('[inert]')) return;
    for (const [clase, nombre] of regiones) {
      if (!region.matches(clase)) continue;
      region.tabIndex = 0;
      region.setAttribute('role', 'region');
      if (!region.hasAttribute('aria-label')) region.setAttribute('aria-label', nombre);
      return;
    }
  }

  function prepararContenido(nodo) {
    if (!(nodo instanceof Element)) return;
    if (nodo.matches(selector)) preparar(nodo);
    nodo.querySelectorAll(selector).forEach(preparar);
  }

  function iniciar() {
    prepararContenido(document.body);
    const observador = new MutationObserver(cambios => {
      for (const cambio of cambios) cambio.addedNodes.forEach(prepararContenido);
    });
    observador.observe(document.body, { childList: true, subtree: true });
    window.addEventListener('pagehide', evento => {
      if (!evento.persisted) observador.disconnect();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar, { once: true });
  } else {
    iniciar();
  }
})();
