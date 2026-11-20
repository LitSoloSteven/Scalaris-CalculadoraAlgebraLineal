/** Detecta el directorio listo y prepara la portada en paralelo a la presentación. */
'use strict';
{
  if (location.pathname === '/' && !window.scalaris.entradaInicio) {
    const raiz = document.documentElement;
    const presentacionActiva = window.scalaris.presentacion?.activa;
    let observador = null;
    let fotograma = null;
    let completada = false;
    let resolver;
    const directorioListo = new Promise(respuesta => { resolver = respuesta; });
    const temporizador = presentacionActiva ? null : setTimeout(finalizar, 5000);
    raiz.setAttribute('data-glosa', 'cerrado');
    if (!presentacionActiva) raiz.setAttribute('data-inicio-pendiente', '');
    window.scalaris.entradaInicio = { directorioListo, finalizar };

    function finalizar() {
      if (completada) return;
      completada = true;
      clearTimeout(temporizador);
      if (fotograma !== null) cancelAnimationFrame(fotograma);
      observador?.disconnect();
      window.removeEventListener('pagehide', finalizar);
      raiz.removeAttribute('data-inicio-pendiente');
      resolver(false);
    }

    function confirmarMontaje() {
      resolver(true);
      finalizar();
    }

    function comprobarContenido() {
      if (completada || !document.querySelector('.inicio-directorio[data-directorio-listo] .inicio-enlace[href]')) return;
      observador?.disconnect();
      if (document.body) document.body.classList.add('inicio-pagina');
      fotograma = requestAnimationFrame(() => { fotograma = requestAnimationFrame(confirmarMontaje); });
    }

    window.addEventListener('pagehide', finalizar);
    observador = new MutationObserver(comprobarContenido);
    observador.observe(raiz, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-directorio-listo'] });
    comprobarContenido();
  }
}
