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
        velocidad = Math.min(velocidad || duracionMaxima / 50, duracionMaxima / Math.max(texto.length, 1));
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
            if (indice < texto.length) {
                fragmentoTexto.textContent += texto.charAt(indice);
                indice++;
                if (indice < texto.length) {
                    temporizador = setTimeout(escribir, velocidad);
                    return;
                }
            }
            cursor.style.display = 'none';
            elemento.removeEventListener('click', saltar);
        }
        escribir();
    };
})();
