/** Preparación del tema almacenado antes de cargar la hoja de estilos. */
'use strict';

{
  window.scalaris = window.scalaris || {};
  const configuracion = document.getElementById('scalaris-configuracion-graficos');
  window.scalaris.graficos = JSON.parse(configuracion.textContent);
  window.scalaris.tema = {
    preparar: function prepararTemaAlmacenado() {
      const tema = localStorage.getItem('tema') || 'papel';
      const raiz = document.documentElement;
      raiz.setAttribute('data-tema', tema);
      raiz.style.colorScheme = tema === 'medianoche' ? 'dark' : 'light';
    }
  };
  window.scalaris.tema.preparar();
}
