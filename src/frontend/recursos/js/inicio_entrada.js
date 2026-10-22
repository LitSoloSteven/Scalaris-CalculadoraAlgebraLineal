/** Libera la entrada del inicio después de la presentación y de montar las tarjetas. */
'use strict';
{
  if (location.pathname === '/' && !window.scalaris.entradaInicio) {
    const raiz = document.documentElement;
    let observador = null;
    let fotograma = null;
    let completada = false;
    const temporizador = setTimeout(finalizar, 5000);
    raiz.setAttribute('data-glosa', 'cerrado');
    raiz.setAttribute('data-inicio-pendiente', '');
    window.scalaris.entradaInicio = { finalizar };

    function finalizar() {
      if (completada) return;
      completada = true;
      clearTimeout(temporizador);
      if (fotograma !== null) cancelAnimationFrame(fotograma);
      observador?.disconnect();
      window.removeEventListener('pagehide', finalizar);
      raiz.removeAttribute('data-inicio-pendiente');
    }

    function comprobarContenido() {
      if (completada || !document.querySelector('.inicio-raiz .inicio-fila')) return;
      observador?.disconnect();
      if (document.body) document.body.classList.add('inicio-pagina');
      fotograma = requestAnimationFrame(() => { fotograma = requestAnimationFrame(finalizar); });
    }

    function esperarContenido() {
      if (completada) return;
      observador = new MutationObserver(comprobarContenido);
      observador.observe(raiz, { childList: true, subtree: true });
      comprobarContenido();
    }

    window.addEventListener('pagehide', finalizar);
    const presentacion = window.scalaris.presentacion;
    if (presentacion?.activa) presentacion.terminada.then(esperarContenido);
    else esperarContenido();
  }
}
