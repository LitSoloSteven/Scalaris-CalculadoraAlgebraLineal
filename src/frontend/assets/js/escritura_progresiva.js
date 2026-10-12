/** Escritura progresiva con texto seguro y finalización por clic. */
(function registrarEscrituraProgresiva() {
    'use strict';
    window.scalaris.efectoMaquinaEscribir = function (idElemento, texto, velocidad) {
        velocidad = velocidad || 18;
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            var destino = document.getElementById(idElemento);
            if (destino) destino.textContent = texto;
            return;
        }
        var elemento = document.getElementById(idElemento);
        if (!elemento) return;
        elemento.innerHTML = '<span class="tw-text"></span><span class="tw-cursor">▌</span>';
        var fragmentoTexto = elemento.querySelector('.tw-text');
        var cursor = elemento.querySelector('.tw-cursor');
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
                temporizador = setTimeout(escribir, velocidad);
            } else {
                cursor.style.display = 'none';
                elemento.removeEventListener('click', saltar);
            }
        }
        escribir();
    };
})();
