"use strict";

const afirmar = require("node:assert/strict");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

const ACCESOS = [
    ["seccion-sistemas-lineales", 2], ["seccion-matrices", 2], ["seccion-vectores-geometria", 1],
    ["seccion-metodos-numericos", 2], ["seccion-sistemas-numeracion", 2],
    ["sistemas", 4], ["leontief", 3], ["matrices", 3], ["inversa", 2], ["determinantes", 3],
    ["factorizacion_lu", 2], ["vectores", 2], ["transformaciones", 2], ["vis:rectas-planos", 2],
    ["vis:vectores", 2], ["vis:combinacion", 3], ["metodos_cerrados", 4], ["metodos_abiertos", 4],
    ["bases", 9], ["romanos", 3],
];
const CURVA = "cubic-bezier(0.32, 0.72, 0, 1)";

function simularPieza(indice, llamadas) {
    return {
        animate(fotogramas, opciones) {
            let completar;
            let interrumpir;
            const finished = new Promise((resolver, rechazar) => {
                completar = resolver;
                interrumpir = rechazar;
            });
            const cancelar = () => interrumpir(new Error("Cancelada"));
            const animacion = { finished, cancel: cancelar };
            const llamada = { indice, fotogramas, opciones, cancelaciones: 0, completar, interrumpir };
            animacion.cancel = () => {
                llamada.cancelaciones += 1;
                cancelar();
            };
            llamadas.push(llamada);
            return animacion;
        },
    };
}

function crearControl(clave, cantidad, llamadas) {
    const partes = Array.from({ length: cantidad }, (_, indice) => simularPieza(indice, llamadas));
    const control = {
        partes,
        dataset: { gestoInicio: clave },
        querySelector: selector => selector === ".inicio-simbolo svg" ? { children: partes } : null,
    };
    const descendiente = { closest: selector => selector === "[data-gesto-inicio]" ? control : null };
    return { control, descendiente };
}

function emitir(objetivo, tipo, datos = {}) {
    const evento = new Event(tipo, { cancelable: true });
    for (const [nombre, valor] of Object.entries(datos)) Object.defineProperty(evento, nombre, { value: valor });
    objetivo.dispatchEvent(evento);
    return evento;
}

function crearCliente() {
    const llamadas = [];
    const tokens = new Map([["--dur-state", 350], ["--dur-reduced", 120]]);
    const punteroFino = Object.assign(new EventTarget(), { matches: true });
    const reduccion = Object.assign(new EventTarget(), { matches: false });
    const documento = Object.assign(new EventTarget(), { hidden: false });
    const ventana = Object.assign(new EventTarget(), {
        matchMedia: consulta => consulta.includes("hover") ? punteroFino : reduccion,
        scalaris: { movimiento: { duracion: token => tokens.get(token), curva: () => CURVA } },
    });
    const contexto = maquinaVirtual.createContext({ window: ventana, document: documento, AbortController });
    cargarAssetCliente("inicio/inicio.js", contexto);
    return { llamadas, tokens, punteroFino, reduccion, documento, ventana };
}

function pasarPuntero(cliente, objetivo, otrasPropiedades = {}) {
    return emitir(cliente.documento, "pointerover", { target: objetivo, pointerType: "mouse", ...otrasPropiedades });
}

function tocar(cliente, objetivo, esPrimario = true) {
    return emitir(cliente.documento, "pointerdown", { target: objetivo, pointerType: "touch", isPrimary: esPrimario });
}

function crearEjemplo() {
    const documento = new EventTarget();
    const reduccion = Object.assign(new EventTarget(), { matches: false });
    const lecturas = [];
    const animaciones = [];
    const movimiento = {
        permitido: () => !reduccion.matches,
        duracion: token => { lecturas.push(token); return 900; },
        curva: () => { lecturas.push("--ease-std"); return CURVA; },
    };
    const ventana = Object.assign(new EventTarget(), { matchMedia: () => reduccion, scalaris: { movimiento } });
    const contexto = maquinaVirtual.createContext({ window: ventana, document: documento });
    cargarAssetCliente("inicio/ejemplos_inicio.js", contexto);

    const atributos = new Set();
    const estado = { textContent: "" };
    const nodos = { "[data-ejemplo-fila]": simularPieza(0, animaciones), "[data-ejemplo-estado]": estado };
    const panel = {
        isConnected: true,
        querySelector: selector => nodos[selector],
        setAttribute: nombre => atributos.add(nombre),
        removeAttribute: nombre => atributos.delete(nombre),
    };
    const boton = { closest: selector => selector === "[data-ejemplo-inicio]" ? panel : null };
    const objetivo = { closest: selector => selector === "[data-ejemplo-reproducir]" ? boton : null };
    return { documento, reduccion, lecturas, animaciones, estado, objetivo };
}

prueba("el ejemplo prepara su duración antes del clic y cancela al repetir", async () => {
    const ejemplo = crearEjemplo();
    afirmar.deepEqual(ejemplo.lecturas, ["--dur-didactic", "--ease-std"]);
    emitir(ejemplo.documento, "click", { target: ejemplo.objetivo, detail: 1 });
    emitir(ejemplo.documento, "click", { target: ejemplo.objetivo, detail: 1 });
    afirmar.equal(ejemplo.lecturas.length, 2);
    afirmar.equal(ejemplo.animaciones[0].cancelaciones, 1);
    afirmar.equal(ejemplo.animaciones[1].opciones.duration, 900);
    ejemplo.animaciones[1].completar();
    await new Promise(setImmediate);
    afirmar.match(ejemplo.estado.textContent, /Se eliminó x/);
});

prueba("teclado y movimiento reducido muestran de inmediato el resultado del ejemplo", () => {
    const ejemplo = crearEjemplo();
    emitir(ejemplo.documento, "click", { target: ejemplo.objetivo, detail: 0 });
    afirmar.match(ejemplo.estado.textContent, /Se eliminó x/);
    ejemplo.reduccion.matches = true;
    emitir(ejemplo.documento, "click", { target: ejemplo.objetivo, detail: 1 });
    afirmar.equal(ejemplo.animaciones.length, 0);
    afirmar.match(ejemplo.estado.textContent, /Se eliminó x/);
});

prueba("los veinte gestos del directorio son distintos y animan solo piezas SVG", () => {
    const cliente = crearCliente();
    const recorridos = new Set();
    for (const [clave, cantidad] of ACCESOS) {
        const { descendiente } = crearControl(clave, cantidad, cliente.llamadas);
        const comienzo = cliente.llamadas.length;
        pasarPuntero(cliente, descendiente);
        const nuevas = cliente.llamadas.slice(comienzo);
        afirmar.ok(nuevas.length, clave);
        recorridos.add(JSON.stringify(nuevas.map(({ indice, fotogramas }) => [indice, fotogramas])));
        for (const { fotogramas, opciones } of nuevas) {
            afirmar.ok(fotogramas.every(fotograma => Object.keys(fotograma).join() === "transform"), clave);
            afirmar.equal(opciones.duration, 350);
            afirmar.equal(opciones.easing, CURVA);
            afirmar.equal(opciones.delay, undefined);
        }
    }
    afirmar.equal(recorridos.size, ACCESOS.length);
});

prueba("solo el puntero fino inicia el gesto de hover y se conserva al pasar entre hijos", () => {
    const cliente = crearCliente();
    const { descendiente } = crearControl("vectores", 2, cliente.llamadas);
    pasarPuntero(cliente, descendiente, { pointerType: "touch" });
    pasarPuntero(cliente, descendiente, { buttons: 1 });
    cliente.punteroFino.matches = false;
    pasarPuntero(cliente, descendiente);
    afirmar.equal(cliente.llamadas.length, 0);
    cliente.punteroFino.matches = true;
    pasarPuntero(cliente, descendiente);
    pasarPuntero(cliente, descendiente, { relatedTarget: descendiente });
    afirmar.equal(cliente.llamadas.length, 1);
    afirmar.equal(cliente.llamadas[0].cancelaciones, 0);
});

prueba("el toque primario responde en pointerdown y conserva el enlace nativo", () => {
    const cliente = crearCliente();
    cliente.punteroFino.matches = false;
    const { descendiente } = crearControl("vectores", 2, cliente.llamadas);
    tocar(cliente, descendiente, false);
    afirmar.equal(cliente.llamadas.length, 0);
    afirmar.equal(tocar(cliente, descendiente).defaultPrevented, false);
    afirmar.equal(cliente.llamadas.length, 1);
    afirmar.equal(emitir(cliente.documento, "click", { target: descendiente, detail: 1 }).defaultPrevented, false);
    emitir(cliente.documento, "pointercancel");
    afirmar.equal(cliente.llamadas[0].cancelaciones, 1);
});

prueba("el foco y la activación con teclado son inmediatos y cancelan el gesto anterior", () => {
    const cliente = crearCliente();
    const { descendiente } = crearControl("vectores", 2, cliente.llamadas);
    pasarPuntero(cliente, descendiente);
    emitir(cliente.documento, "focusin", { target: descendiente });
    afirmar.equal(emitir(cliente.documento, "keydown", { key: "Enter" }).defaultPrevented, false);
    afirmar.equal(emitir(cliente.documento, "click", { target: descendiente, detail: 0 }).defaultPrevented, false);
    afirmar.equal(cliente.llamadas.length, 1);
    afirmar.equal(cliente.llamadas[0].cancelaciones, 1);
});

prueba("la preferencia de movimiento cancela la animación y limita la opacidad a 120 ms", () => {
    const cliente = crearCliente();
    const { descendiente } = crearControl("vectores", 2, cliente.llamadas);
    pasarPuntero(cliente, descendiente);
    cliente.reduccion.matches = true;
    emitir(cliente.reduccion, "change");
    pasarPuntero(cliente, descendiente);
    afirmar.equal(cliente.llamadas[0].cancelaciones, 1);
    const { opciones, fotogramas } = cliente.llamadas[1];
    afirmar.equal(opciones.duration, cliente.tokens.get("--dur-reduced"));
    afirmar.ok(opciones.duration <= 120);
    afirmar.ok(fotogramas.every(fotograma => Object.keys(fotograma).join() === "opacity"));
    afirmar.equal(fotogramas[0].opacity, fotogramas.at(-1).opacity);
});

prueba("al interrumpir un gesto solo conserva las piezas del nuevo y retira las terminadas", async () => {
    const cliente = crearCliente();
    const primero = crearControl("vectores", 2, cliente.llamadas);
    const segundo = crearControl("determinantes", 3, cliente.llamadas);
    pasarPuntero(cliente, primero.descendiente);
    pasarPuntero(cliente, segundo.descendiente);
    const [anterior, terminada, ...pendientes] = cliente.llamadas;
    afirmar.equal(anterior.cancelaciones, 1);
    terminada.completar();
    await Promise.resolve();
    cliente.documento.hidden = true;
    emitir(cliente.documento, "visibilitychange");
    afirmar.equal(terminada.cancelaciones, 0);
    afirmar.ok(pendientes.every(llamada => llamada.cancelaciones === 1));
});

prueba("pagehide retira listeners y un regreso con pageshow restaura una sola sesión", () => {
    const cliente = crearCliente();
    const { descendiente } = crearControl("vectores", 2, cliente.llamadas);
    pasarPuntero(cliente, descendiente);
    emitir(cliente.ventana, "pagehide");
    pasarPuntero(cliente, descendiente);
    afirmar.equal(cliente.llamadas.length, 1);
    afirmar.equal(cliente.llamadas[0].cancelaciones, 1);
    emitir(cliente.ventana, "pageshow");
    emitir(cliente.ventana, "pageshow");
    pasarPuntero(cliente, descendiente);
    afirmar.equal(cliente.llamadas.length, 2);
});

prueba("una clave desconocida o un fallo de WAAPI deja el control operable", async () => {
    const cliente = crearCliente();
    const desconocido = crearControl("constructor", 2, cliente.llamadas);
    pasarPuntero(cliente, desconocido.descendiente);
    afirmar.equal(cliente.llamadas.length, 0);

    const parcial = crearControl("inversa", 2, cliente.llamadas);
    parcial.control.partes[1].animate = () => { throw new Error("Animación no disponible"); };
    afirmar.equal(pasarPuntero(cliente, parcial.descendiente).defaultPrevented, false);
    afirmar.equal(cliente.llamadas.length, 1);
    afirmar.equal(cliente.llamadas[0].cancelaciones, 1);
    await Promise.resolve();
});
