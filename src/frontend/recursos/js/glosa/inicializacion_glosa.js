/** Estado inicial de Glosa según el espacio disponible y la selección almacenada. */
'use strict';

try {
  const enInicio = typeof location !== 'undefined' && location.pathname === '/' &&
    !/(?:^|[?&])glosa=1(?:&|$)/.test(location.search || '');
  if (!enInicio && window.matchMedia('(min-width: 1024px)').matches) {
    const estado = localStorage.getItem('scalaris:glosa');
    document.documentElement.setAttribute('data-glosa', estado === 'abierto' ? 'abierto' : 'cerrado');
  } else {
    document.documentElement.setAttribute('data-glosa', 'cerrado');
  }
} catch (error) {}
