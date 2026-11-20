/** Secuencia de marca al entrar por la raíz una vez por sesión de pestaña. */
'use strict';
{
  window.scalaris = window.scalaris || {};
  if (!window.scalaris.presentacion) {
    const raiz = document.documentElement;
    const revelado = window.scalaris.reveladoCircular;
    const animaciones = new Set();
    const preferencia = window.matchMedia('(prefers-reduced-motion: reduce)');
    const posicionElevada = 'translateY(-18px) scale(1.2)';
    let fondo = null;
    let completada = false;
    let temporizador;
    let plazo;
    let tramos;
    let resolver;
    const estado = { activa: false, terminada: new Promise(respuesta => { resolver = respuesta; }), finalizar };
    window.scalaris.presentacion = estado;

    function finalizar() {
      if (completada) return;
      completada = true;
      clearTimeout(temporizador);
      if (estado.activa) window.scalaris.entradaInicio?.finalizar();
      animaciones.forEach(animacion => animacion.cancel());
      animaciones.clear();
      fondo?.remove();
      raiz.removeAttribute('data-presentacion-activa');
      window.removeEventListener('pagehide', finalizar);
      document.removeEventListener('keydown', finalizarPorGesto, true);
      document.removeEventListener('pointerdown', finalizarPorGesto, true);
      document.removeEventListener('visibilitychange', alOcultar);
      preferencia.removeEventListener('change', alReducir);
      estado.activa = false;
      resolver();
    }

    function alOcultar() { if (document.hidden) finalizar(); }
    function alReducir(evento) { if (evento.matches) finalizar(); }

    function finalizarPorGesto(evento) {
      if (evento?.isTrusted) window.scalaris.sonido?.reproducir('entrada');
      finalizar();
    }

    function debeReproducirse() {
      if (raiz.getAttribute('data-entrada') === 'teclado') return false;
      try {
        const mostrada = sessionStorage.getItem('presentacion-mostrada');
        sessionStorage.setItem('presentacion-mostrada', '1');
        return location.pathname === '/' && !location.search && !mostrada;
      } catch (_) { return false; }
    }

    function animar(elemento, fotogramas, opciones) {
      const animacion = elemento.animate(fotogramas, { fill: 'both', ...opciones });
      animaciones.add(animacion);
      animacion.finished.catch(finalizar);
      return animacion.finished;
    }

    function definirTramos(reducido) {
      if (reducido) {
        const fundido = revelado.tiempos('--dur-reduced');
        return { fundido, limite: fundido.duration };
      }
      const anillo = revelado.tiempos('--dur-didactic');
      const elevacion = revelado.tiempos('--dur-panel');
      const impacto = revelado.tiempos('--dur-panel-exit');
      const onda = revelado.tiempos();
      const resto = elevacion.duration + impacto.duration + onda.duration;
      return { anillo, elevacion, impacto, onda, resto, limite: anillo.duration + resto + onda.duration };
    }

    function animarCarga(imagen) {
      return Promise.all([
        animar(imagen,
          [{ opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1)' }], tramos.onda),
        animar(fondo.querySelector('#presentacion-anillo circle'),
          [{ strokeDashoffset: 365 }, { strokeDashoffset: 0 }], tramos.anillo),
        animar(fondo.querySelector('#presentacion-nombre'),
          [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)' }], tramos.onda),
        animar(fondo.querySelector('#presentacion-organizacion'),
          [{ opacity: 0, transform: 'scale(0.95) translateY(16px)' }, { opacity: 1, transform: 'scale(1) translateY(0)' }], tramos.elevacion),
      ]);
    }

    function prepararAbertura(imagen) {
      const abertura = fondo.querySelector('#presentacion-abertura');
      const { x, y, radio } = revelado.medir(revelado.centroDe(imagen));
      abertura.setAttribute('cx', x);
      abertura.setAttribute('cy', y);
      abertura.setAttribute('r', radio);
      return abertura;
    }

    function elevarLogotipo(imagen) {
      return Promise.all([
        animar(imagen, [{ transform: 'scale(1)' }, { transform: posicionElevada }], tramos.elevacion),
        animar(fondo.querySelector('#presentacion-barra'),
          [{ opacity: 0, transform: 'scaleX(0.95)' }, { opacity: 1, transform: 'scaleX(1)' }], tramos.elevacion),
      ]);
    }

    async function reproducirSecuencia(imagen) {
      await animarCarga(imagen);
      const directorioListo = await window.scalaris.entradaInicio?.directorioListo;
      if (!directorioListo || completada || performance.now() + tramos.resto >= plazo) return;
      const abertura = prepararAbertura(imagen);
      await elevarLogotipo(imagen);
      if (completada) return;
      await animar(imagen, [{ transform: posicionElevada }, { transform: 'translateY(0) scale(0.95)' }], tramos.impacto);
      if (completada) return;
      const onda = animar(abertura, [{ transform: 'scale(0)' }, { transform: 'scale(1)' }], tramos.onda);
      fondo.setAttribute('data-revelando', '');
      await onda;
    }

    function reproducir(imagen) {
      if (completada) return;
      window.scalaris.sonido?.reproducir('entrada');
      if (tramos.fundido) return animar(fondo, [{ opacity: 1 }, { opacity: 0 }], tramos.fundido);
      return reproducirSecuencia(imagen);
    }

    function escucharInterrupciones() {
      window.addEventListener('pagehide', finalizar);
      document.addEventListener('keydown', finalizarPorGesto, true);
      document.addEventListener('pointerdown', finalizarPorGesto, true);
      document.addEventListener('visibilitychange', alOcultar);
      preferencia.addEventListener('change', alReducir);
    }

    function montarPresentacion() {
      const reducido = preferencia.matches;
      if (document.hidden || (!reducido && !window.CSS?.supports('mask-image', "url('#presentacion-mascara')"))) {
        finalizar();
        return;
      }
      const plantilla = document.getElementById('presentacion-plantilla');
      fondo = plantilla.content.firstElementChild.cloneNode(true);
      const imagen = fondo.querySelector('#presentacion-logotipo');
      if (typeof imagen.animate !== 'function') { finalizar(); return; }
      tramos = definirTramos(reducido);
      imagen.src = raiz.getAttribute('data-tema') === 'medianoche' ? '/assets/LogoClaro.png' : '/assets/LogoOscuro.png';
      fondo.toggleAttribute('data-movimiento-reducido', reducido);
      estado.activa = true;
      raiz.setAttribute('data-presentacion-activa', '');
      raiz.setAttribute('data-vista-revelada', '');
      raiz.appendChild(fondo);
      escucharInterrupciones();
      plazo = performance.now() + tramos.limite;
      temporizador = setTimeout(finalizar, tramos.limite);
      imagen.decode().then(() => reproducir(imagen)).then(finalizar, finalizar);
    }

    try {
      if (debeReproducirse()) montarPresentacion();
      else finalizar();
    } catch (_) { finalizar(); }
  }
}
