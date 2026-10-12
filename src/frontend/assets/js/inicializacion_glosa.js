/** Estado inicial de Glosa según el espacio disponible y la selección almacenada. */
'use strict';

try {
  if (window.matchMedia('(min-width: 1024px)').matches) {
    const estado = localStorage.getItem('scalaris:glosa');
    if (estado === 'open') {
      document.documentElement.setAttribute('data-glosa', 'open');
    } else {
      document.documentElement.setAttribute('data-glosa', 'closed');
    }
  } else {
    document.documentElement.setAttribute('data-glosa', 'closed');
  }
} catch (error) {}
