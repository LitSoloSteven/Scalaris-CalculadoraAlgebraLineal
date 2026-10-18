/** Escritura progresiva con texto seguro y finalización por clic. */
(function registrarEscrituraProgresiva() {
    'use strict';
    window.scalaris.efectoMaquinaEscribir = function (identificadorElemento, texto, velocidad) {
        velocidad = velocidad || 18;
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            var destino = document.getElementById(identificadorElemento);
            if (destino) destino.textContent = texto;
            return;
        }
        var elemento = document.getElementById(identificadorElemento);
        if (!elemento) return;
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
                temporizador = setTimeout(escribir, velocidad);
            } else {
                cursor.style.display = 'none';
                elemento.removeEventListener('click', saltar);
            }
        }
        escribir();
    };
})();
