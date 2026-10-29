/* La limpieza espera que terminen los desplazamientos antes de retirar las celdas. */
'use strict';
{

  window.scalaris = window.scalaris || {};
  var recoleccionActiva = null;

  function programar(estado, tarea, espera) {
    var temporizador = setTimeout(tarea, espera);
    estado.temporizadores.push(temporizador);
  }

  function restaurarRecoleccion(estado) {
    if (!estado || estado.restaurada) return;
    estado.restaurada = true;
    estado.temporizadores.forEach(temporizador => clearTimeout(temporizador));
    estado.clones.forEach(clon => clon.remove());
    estado.entradas.forEach((entrada, indice) => {
      var anterior = estado.visibilidades[indice];
      if (anterior.valor) entrada.style.setProperty('visibility', anterior.valor, anterior.prioridad);
      else entrada.style.removeProperty('visibility');
    });
    estado.boton.classList.remove('movimiento-compresion');
    if (estado.icono) estado.icono.textContent = 'delete';
    if (recoleccionActiva === estado) recoleccionActiva = null;
    estado.resolver();
  }

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
    var movimiento = window.scalaris.movimiento;
    var transicion = movimiento.duracion('--dur-panel') + 'ms ' + movimiento.curva();
    clon.style.transition = 'transform ' + transicion + ', opacity ' + transicion;
    clon.style.pointerEvents = 'none';
    clon.style.overflow = 'hidden';
    return clon;
  }

  function animarTrayectoria(estado, clon, rectangulo, rectanguloBoton, retraso) {
    document.body.appendChild(clon);

    programar(estado, function () {
      var destinoHorizontal = rectanguloBoton.left + rectanguloBoton.width / 2 - rectangulo.width / 2;
      var destinoVertical = rectanguloBoton.top + rectanguloBoton.height / 2 - rectangulo.height / 2;
      clon.style.transform = 'translate(' + (destinoHorizontal - rectangulo.left) + 'px, ' + (destinoVertical - rectangulo.top) + 'px) scale(0.1)';
      clon.style.opacity = '0';
    }, retraso);

    programar(estado, function () {
      clon.remove();
    }, retraso + window.scalaris.movimiento.duracion('--dur-panel'));
  }

  function filtrar_entradas_visibles(identificadores) {
    var entradasCompletas = identificadores.flatMap(function (identificador) {
      var elemento = document.getElementById(identificador);
      if (!elemento) return [];
      return elemento.matches?.('input') ? [elemento] : Array.from(elemento.querySelectorAll('input'));
    });
    return Array.from(new Set(entradasCompletas)).filter(function (i) {
      var r = i.getBoundingClientRect();
      return i.value && i.value.trim() !== '' &&
        r.bottom > 0 && r.top < window.innerHeight && r.right > 0 && r.left < window.innerWidth;
    });
  }

  function ejecutarRecoleccion(boton, elementoIcono, entradas, resolver, rechazar) {
    var rectanguloBoton = boton.getBoundingClientRect();
    var movimiento = window.scalaris.movimiento;
    var paso = movimiento.duracion('--stagger-step');
    var limite = movimiento.duracion('--stagger-max');
    var vuelo = movimiento.duracion('--dur-panel');
    var destinos = entradas.slice(0, 8);
    var estado = { boton, icono: elementoIcono, entradas, resolver, temporizadores: [], clones: [],
      visibilidades: entradas.map(entrada => ({ valor: entrada.style.getPropertyValue('visibility'),
        prioridad: entrada.style.getPropertyPriority('visibility') })) };
    recoleccionActiva = estado;

    try {
      destinos.forEach(function (entrada, indice) {
        var rectangulo = entrada.getBoundingClientRect();
        var clon = crearClon(entrada, rectangulo);
        estado.clones.push(clon);
        animarTrayectoria(estado, clon, rectangulo, rectanguloBoton, Math.min(indice * paso, limite));
      });
      entradas.forEach(entrada => { entrada.style.setProperty('visibility', 'hidden'); });
    } catch (error) {
      estado.resolver = function () {};
      restaurarRecoleccion(estado);
      rechazar(error);
      return;
    }

    var ultimoRetraso = Math.min((destinos.length - 1) * paso, limite);
    programar(estado, function () {
      boton.classList.add('movimiento-compresion');
      programar(estado, function () {
        boton.classList.remove('movimiento-compresion');
        if (elementoIcono) {
          elementoIcono.textContent = 'delete';
        }
        resolver();
        programar(estado, () => restaurarRecoleccion(estado), vuelo);
      }, vuelo);
    }, ultimoRetraso + vuelo);
  }

  function animarRecoleccionBasura(identificadores) {
    return new Promise(function (resolver, rechazar) {
      var permitido = window.scalaris.movimiento && window.scalaris.movimiento.permitido ?
        window.scalaris.movimiento.permitido() : false;
      if (!permitido) {
        resolver();
        return;
      }
      if (recoleccionActiva) restaurarRecoleccion(recoleccionActiva);
      var boton = document.getElementById('boton-limpiar-principal');
      if (!boton || !Array.isArray(identificadores) || !identificadores.length) {
        resolver();
        return;
      }
      var elementoIcono = boton.querySelector('.q-icon');
      if (elementoIcono) {
        elementoIcono.textContent = 'delete_sweep';
      }
      var destinos = filtrar_entradas_visibles(identificadores);
      if (destinos.length === 0) {
        if (elementoIcono) {
          elementoIcono.textContent = 'delete';
        }
        resolver();
        return;
      }
      ejecutarRecoleccion(boton, elementoIcono, destinos, resolver, rechazar);
    });
  }


  window.scalaris.animarRecoleccionBasura = animarRecoleccionBasura;
  window.scalaris.terminarRecoleccionBasura = function () { restaurarRecoleccion(recoleccionActiva); };
}
