/** Preparación del tema almacenado antes de cargar la hoja de estilos. */
'use strict';

{
  window.scalaris = window.scalaris || {};
  const configuracion = document.getElementById('scalaris-configuracion-graficos');
  window.scalaris.graficos = JSON.parse(configuracion.textContent);
  window.scalaris.tema = {
    preparar: function prepararTemaAlmacenado() {
      const equivalencias = { claro: 'papel', aqua: 'marea', oscuro: 'medianoche' };
      let tema = localStorage.getItem('theme') || 'papel';
      if (equivalencias[tema]) {
        tema = equivalencias[tema];
        localStorage.setItem('theme', tema);
      }
      const raiz = document.documentElement;
      raiz.setAttribute('data-theme', tema);
      raiz.style.colorScheme = tema === 'medianoche' ? 'dark' : 'light';
    }
  };
  window.scalaris.tema.preparar();
}
