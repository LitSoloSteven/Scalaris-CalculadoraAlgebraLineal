"use strict";

const afirmar = require("node:assert/strict");
const archivos = require("node:fs");
const ruta = require("node:path");
const prueba = require("node:test");
const maquinaVirtual = require("node:vm");
const { cargarAssetCliente } = require("./comun_cliente_javascript.js");

const CURVA = "cubic-bezier(0.32, 0.72, 0, 1)";
const PLANTILLAS = [
    "ejemplos_inicio_algebra.html",
    "ejemplos_inicio_geometria.html",
    "ejemplos_inicio_numericos.html",
];
const CLAVES = [
    "sistemas", "leontief", "matrices", "inversa", "factorizacion_lu",
    "determinantes", "vectores", "transformaciones",
    "vis:rectas-planos", "vis:vectores", "vis:combinacion",
    "metodos_cerrados", "metodos_abiertos", "bases", "romanos",
];

function leerPlantillas() {
    const base = ruta.join(__dirname, "..", "src", "frontend", "recursos", "plantillas");
    const bloques = new Map();
    for (const nombre of PLANTILLAS) {
        const texto = archivos.readFileSync(ruta.join(base, nombre), "utf8");
        for (const coincidencia of texto.matchAll(/<template\s+data-ejemplo="([^"]+)">([\s\S]*?)<\/template>/g)) {
            bloques.set(coincidencia[1], coincidencia[2]);
        }
    }
    return bloques;
}

function crearMarca(preset, animaciones, falla = false) {
    return {
        dataset: preset ? { ejemploMarca: preset } : {},
        style: { willChange: "" },
        animate(fotogramas, opciones) {
            if (falla) throw new Error("WAAPI no disponible");
            let completar;
            let rechazar;
            const finished = new Promise((res, rej) => { completar = res; rechazar = rej; });
            const entrada = { preset, fotogramas, opciones, cancelaciones: 0, completar, rechazar };
            animaciones.push(entrada);
            return {
                finished,
                cancel() {
                    entrada.cancelaciones += 1;
                    rechazar(new Error("Cancelada"));
                },
            };
        },
    };
}

function crearPanel(marcas, mensaje = "Resultado listo.") {
    const atributos = new Set();
    const estado = { textContent: "" };
    const boton = { closest: selector => selector === "[data-ejemplo-inicio]" ? panel : null };
    const objetivo = { closest: selector => selector === "[data-ejemplo-reproducir]" ? boton : null };
    const panel = {
        isConnected: true,
        dataset: { ejemploMensaje: mensaje },
        querySelectorAll: selector => selector.includes("data-ejemplo-marca") ? marcas : [],
        querySelector: selector => selector === "[data-ejemplo-estado]" ? estado : marcas[0] || null,
        setAttribute: nombre => atributos.add(nombre),
        removeAttribute: nombre => atributos.delete(nombre),
    };
    return { panel, estado, atributos, objetivo };
}

function crearEntorno(opciones = {}) {
    const documento = Object.assign(new EventTarget(), {
        hidden: false,
        querySelector: selector => opciones.nodos?.[selector] || null,
    });
    const reduccion = Object.assign(new EventTarget(), { matches: false });
    const lecturas = [];
    const recargas = [];
    const movimiento = {
        permitido: () => !reduccion.matches,
        duracion: token => { lecturas.push(token); return 900; },
        curva: () => { lecturas.push("--ease-std"); return CURVA; },
    };
    const ventana = Object.assign(new EventTarget(), {
        matchMedia: () => reduccion,
        location: { reload: () => recargas.push(true) },
        scalaris: { movimiento, recientes: opciones.recientes },
    });
    const contexto = maquinaVirtual.createContext({ window: ventana, document: documento });
    cargarAssetCliente("ejemplos_inicio.js", contexto);
    return { documento, ventana, reduccion, lecturas, recargas };
}

function emitir(objetivo, tipo, propiedades = {}) {
    const evento = new Event(tipo, { cancelable: true });
    for (const [nombre, valor] of Object.entries(propiedades)) Object.defineProperty(evento, nombre, { value: valor });
    objetivo.dispatchEvent(evento);
    return evento;
}

prueba("las quince plantillas conservan dos etapas, marca animable y accesibilidad sin estilos inline", () => {
    const bloques = leerPlantillas();
    afirmar.deepEqual(Array.from(bloques.keys()), CLAVES);
    for (const [clave, html] of bloques) {
        afirmar.equal((html.match(/class="inicio-ejemplo-etapa"/g) || []).length, 2, clave);
        afirmar.ok(html.includes('class="inicio-ejemplo-flecha"'), clave);
        afirmar.ok(html.includes("data-ejemplo-marca=") || html.includes("data-ejemplo-fila"), clave);
        afirmar.equal(html.includes("style="), false, clave);
        for (const svg of html.match(/<svg\b[^>]*>/g) || []) {
            afirmar.match(svg, /role="img"/, clave);
            afirmar.match(svg, /aria-label="[^"]+"/, clave);
        }
    }
});

prueba("cada preset de marca anima solo transform y opacity sin scale cero y limpia willChange", async () => {
    const presets = ["fila", "crecer-x", "deslizar-derecha", "deslizar-izquierda", "expandir", "cizalla", "punta-cola", "punto"];
    const entorno = crearEntorno();
    afirmar.deepEqual(entorno.lecturas, ["--dur-didactic", "--ease-std"]);
    for (const preset of presets) {
        const animaciones = [];
        const marca = crearMarca(preset, animaciones);
        const { objetivo, estado, atributos } = crearPanel([marca], `Mensaje de ${preset}`);
        emitir(entorno.documento, "click", { target: objetivo, detail: 1 });
        afirmar.equal(marca.style.willChange, "transform, opacity", preset);
        for (const fotograma of animaciones[0].fotogramas) {
            afirmar.ok(
                Object.keys(fotograma).every(prop => prop === "transform" || prop === "opacity" || prop === "offset"),
                preset,
            );
            afirmar.equal(/scale\(\s*0\s*\)/.test(fotograma.transform || ""), false, preset);
        }
        animaciones[0].completar();
        await new Promise(setImmediate);
        afirmar.equal(marca.style.willChange, "", preset);
        afirmar.equal(estado.textContent, `Mensaje de ${preset}`);
        afirmar.ok(atributos.has("data-ejemplo-completado"));
    }
    afirmar.equal(entorno.lecturas.length, 2);
});

prueba("preparar, teclado, reducido, visibilidad, pagehide y fallos WAAPI dejan el panel limpio", async () => {
    const entorno = crearEntorno();
    const animaciones = [];
    const marcas = [crearMarca("deslizar-izquierda", animaciones), crearMarca("deslizar-derecha", animaciones)];
    const { panel, estado, objetivo } = crearPanel(marcas, "Factores L y U listos.");

    emitir(entorno.documento, "click", { target: objetivo, detail: 1 });
    afirmar.equal(animaciones.length, 2);
    entorno.ventana.scalaris.ejemplosInicio.preparar(panel);
    afirmar.ok(animaciones.every(entrada => entrada.cancelaciones === 1));
    afirmar.ok(marcas.every(marca => marca.style.willChange === ""));

    emitir(entorno.documento, "click", { target: objetivo, detail: 0 });
    afirmar.equal(animaciones.length, 2);
    afirmar.equal(estado.textContent, "Factores L y U listos.");

    const falla = crearPanel([crearMarca("punto", animaciones, true)], "Fallo controlado.");
    emitir(entorno.documento, "click", { target: falla.objetivo, detail: 1 });
    afirmar.equal(falla.estado.textContent, "Fallo controlado.");

    emitir(entorno.documento, "click", { target: objetivo, detail: 1 });
    entorno.documento.hidden = true;
    emitir(entorno.documento, "visibilitychange");
    afirmar.ok(marcas.every(marca => marca.style.willChange === ""));
    afirmar.equal(estado.textContent, "Factores L y U listos.");
    await Promise.resolve();
});

prueba("pageshow recarga solo cuando el historial cambió desde bfcache", () => {
    const recientes = { leer: () => ({ valido: true, identificadores: ["vis:combinacion"] }) };
    const entorno = crearEntorno({
        recientes,
        nodos: { ".inicio-destacado": { dataset: { accesoReciente: "bases" } } },
    });
    emitir(entorno.ventana, "pageshow", { persisted: false });
    afirmar.equal(entorno.recargas.length, 0);
    emitir(entorno.ventana, "pageshow", { persisted: true });
    afirmar.equal(entorno.recargas.length, 1);

    const sinCambio = crearEntorno({
        recientes,
        nodos: { ".inicio-destacado": { dataset: { accesoReciente: "vis:combinacion" } } },
    });
    emitir(sinCambio.ventana, "pageshow", { persisted: true });
    afirmar.equal(sinCambio.recargas.length, 0);
});

prueba("inicio_recientes conserva escenas, rechaza blancos o exceso y resiste bloqueo", () => {
    const almacen = new Map();
    const contexto = maquinaVirtual.createContext({
        window: {},
        localStorage: {
            getItem: clave => almacen.get(clave) ?? null,
            setItem: (clave, valor) => almacen.set(clave, valor),
        },
    });
    cargarAssetCliente("inicio_recientes.js", contexto);
    const recientes = contexto.window.scalaris.recientes;
    recientes.registrar("vis:rectas-planos");
    recientes.registrar("vis:vectores");
    recientes.registrar("   ");
    recientes.registrar("x".repeat(65));
    afirmar.deepEqual(Array.from(recientes.leer().identificadores), ["vis:vectores", "vis:rectas-planos"]);

    almacen.set("scalaris:recientes", "a".repeat(2049));
    afirmar.equal(recientes.leer().valido, false);

    const bloqueado = maquinaVirtual.createContext({
        window: {},
        localStorage: {
            getItem: () => { throw new Error("Bloqueado"); },
            setItem: () => { throw new Error("Bloqueado"); },
        },
    });
    cargarAssetCliente("inicio_recientes.js", bloqueado);
    afirmar.equal(bloqueado.window.scalaris.recientes.leer().valido, false);
    afirmar.doesNotThrow(() => bloqueado.window.scalaris.recientes.registrar("vis:combinacion"));
});
