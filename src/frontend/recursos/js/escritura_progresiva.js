/** Escritura progresiva con texto seguro y finalización por clic. */
(function registrarEscrituraProgresiva() {
    'use strict';
    window.scalaris.efectoMaquinaEscribir = function (identificadorElemento, texto, velocidad) {
        if (!window.scalaris.movimiento.permitido()) {
            var destino = document.getElementById(identificadorElemento);
            if (destino) destino.textContent = texto;
            return;
        }
        var elemento = document.getElementById(identificadorElemento);
        if (!elemento) return;
        var duracionMaxima = window.scalaris.movimiento.duracion('--dur-didactic');
        var duracionTotal = velocidad > 0 ? Math.min(velocidad * texto.length, duracionMaxima) : duracionMaxima;
        var intervalo = window.scalaris.movimiento.duracion('--stagger-step');
        var inicio = Date.now();
        elemento.innerHTML = '<span class="escritura-texto"></span><span class="escritura-cursor">▌</span>';
        var fragmentoTexto = elemento.querySelector('.escritura-texto');
        var cursor = elemento.querySelector('.escritura-cursor');
        var indice = 0, temporizador = null;
        var saltar = function () {
            indice = texto.length;
            clearTimeout(temporizador);
            fragmentoTexto.textContent = texto;
            cursor.style.display = 'none';
            elemento.removeEventListener('click', saltar);
        };
        elemento.addEventListener('click', saltar);
        function escribir() {
            var transcurrido = Date.now() - inicio;
            indice = duracionTotal > 0 ? Math.max(1, Math.ceil(texto.length * transcurrido / duracionTotal)) : texto.length;
            fragmentoTexto.textContent = texto.slice(0, indice);
            if (indice < texto.length) {
                temporizador = setTimeout(escribir, Math.min(intervalo, duracionTotal - transcurrido));
                return;
            }
            cursor.style.display = 'none';
            elemento.removeEventListener('click', saltar);
        }
        escribir();
    };
})();
