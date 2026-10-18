/** Preparación del tema almacenado antes de cargar la hoja de estilos. */
'use strict';

{
  window.scalaris = window.scalaris || {};
  const configuracion = document.getElementById('scalaris-configuracion-graficos');
  window.scalaris.graficos = JSON.parse(configuracion.textContent);
  window.scalaris.tema = {
    preparar: function prepararTemaAlmacenado() {
      let tema = 'papel';
      try { tema = localStorage.getItem('tema') || tema; } catch (_) { /* Tema base si se bloquea el almacenamiento. */ }
      const raiz = document.documentElement;
      raiz.setAttribute('data-tema', tema);
      raiz.style.colorScheme = tema === 'medianoche' ? 'dark' : 'light';
    }
  };
  window.scalaris.tema.preparar();
}
