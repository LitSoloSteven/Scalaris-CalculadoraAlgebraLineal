/* La limpieza espera que terminen los desplazamientos antes de retirar las celdas. */
'use strict';
{

  window.scalaris = window.scalaris || {};

  function crearClon(entrada, rectangulo) {
    var clon = document.createElement('div');
    clon.textContent = entrada.value;
    clon.style.position = 'fixed';
    clon.style.left = rectangulo.left + 'px';
    clon.style.top = rectangulo.top + 'px';
    clon.style.width = rectangulo.width + 'px';
    clon.style.height = rectangulo.height + 'px';
    clon.style.margin = '0';
    clon.style.zIndex = 'var(--z-modal)';
    clon.style.display = 'flex';
    clon.style.alignItems = 'center';
    clon.style.justifyContent = 'center';

    var contenedor = entrada.closest('.q-field__control');
    if (contenedor) {
      var estiloContenedor = window.getComputedStyle(contenedor);
      clon.style.background = estiloContenedor.background;
      clon.style.borderRadius = estiloContenedor.borderRadius;
      clon.style.boxShadow = estiloContenedor.boxShadow;
    }

    var estiloEntrada = window.getComputedStyle(entrada);
    clon.style.fontFamily = estiloEntrada.fontFamily;
    clon.style.fontSize = estiloEntrada.fontSize;
    clon.style.color = estiloEntrada.color;
    clon.style.transition = 'transform 160ms cubic-bezier(0.32, 0.72, 0, 1), opacity 160ms cubic-bezier(0.32, 0.72, 0, 1)';
    clon.style.pointerEvents = 'none';
    clon.style.overflow = 'hidden';
    return clon;
  }

  function animarTrayectoria(clon, entrada, rectangulo, rectanguloBoton, retraso) {
    entrada.style.color = 'transparent';
    document.body.appendChild(clon);

    setTimeout(function () {
      entrada.value = '';
      var destinoHorizontal = rectanguloBoton.left + rectanguloBoton.width / 2 - rectangulo.width / 2;
      var destinoVertical = rectanguloBoton.top + rectanguloBoton.height / 2 - rectangulo.height / 2;
      clon.style.transform = 'translate(' + (destinoHorizontal - rectangulo.left) + 'px, ' + (destinoVertical - rectangulo.top) + 'px) scale(0.1)';
      clon.style.opacity = '0';
    }, retraso);

    setTimeout(function () {
      clon.remove();
    }, retraso + 160);
  }

  function filtrar_entradas_visibles() {
    var entradasCompletas = document.querySelectorAll('.matriz-entrada input');
    return Array.from(entradasCompletas).filter(function (i) {
      var r = i.getBoundingClientRect();
      return i.value && i.value !== '0' && i.value.trim() !== '' &&
        r.bottom > 0 && r.top < window.innerHeight && r.right > 0 && r.left < window.innerWidth;
    }).slice(0, 40);
  }

  function ejecutarRecoleccion(boton, elementoIcono, destinos, resolver) {
    var rectanguloBoton = boton.getBoundingClientRect();
    var paso = Math.max(1, Math.floor(90 / destinos.length));
    var retrasoAcumulado = 0;

    destinos.forEach(function (entrada) {
      var rectangulo = entrada.getBoundingClientRect();
      var clon = crearClon(entrada, rectangulo);
      animarTrayectoria(clon, entrada, rectangulo, rectanguloBoton, retrasoAcumulado);
      retrasoAcumulado += paso;
    });

    var duracionMedia = (window.scalaris.movimiento && window.scalaris.movimiento.medio) || 240;
    setTimeout(function () {
      boton.classList.add('movimiento-compresion');
      setTimeout(function () {
        boton.classList.remove('movimiento-compresion');
        if (elementoIcono) {
          elementoIcono.textContent = 'delete';
        }
        document.querySelectorAll('.matriz-entrada input').forEach(function (i) {
          i.style.color = '';
        });
        resolver();
      }, duracionMedia);
    }, retrasoAcumulado + 160);
  }

  function animarRecoleccionBasura() {
    return new Promise(function (resolver) {
      var permitido = window.scalaris.movimiento && window.scalaris.movimiento.permitido ?
        window.scalaris.movimiento.permitido() : false;
      if (!permitido) {
        resolver();
        return;
      }
      var boton = document.getElementById('boton-limpiar-principal');
      if (!boton) {
        resolver();
        return;
      }
      var elementoIcono = boton.querySelector('.q-icon');
      if (elementoIcono) {
        elementoIcono.textContent = 'delete_sweep';
      }
      var destinos = filtrar_entradas_visibles();
      if (destinos.length === 0) {
        if (elementoIcono) {
          elementoIcono.textContent = 'delete';
        }
        resolver();
        return;
      }
      ejecutarRecoleccion(boton, elementoIcono, destinos, resolver);
    });
  }


  window.scalaris.animarRecoleccionBasura = animarRecoleccionBasura;
}
