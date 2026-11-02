'use strict';
const prueba = require('node:test');
const afirmar = require('node:assert/strict');
const vm = require('node:vm');
const { cargarAssetCliente } = require('./comun_cliente_javascript.js');

/** Carga el listener real con una superficie y una animación observables. */
function crearPulso() {
    const eventos = new Map(), llamadas = [];
    const animacion = { animationName: 'escrituraPulso',
        cancel: () => llamadas.push('cancelar'), play: () => llamadas.push('reproducir') };
    const superficie = { classList: { add: clase => llamadas.push(clase) },
        getAnimations: () => [animacion] };
    const entrada = { matches: () => true,
        closest: () => ({ querySelector: () => superficie }) };
    const ventana = { scalaris: { movimiento: { permitido: () => false } } };
    const documento = { addEventListener: (nombre, funcion) => eventos.set(nombre, funcion),
        removeEventListener: nombre => eventos.delete(nombre) };
    const contexto = vm.createContext({ window: ventana, document: documento });
    cargarAssetCliente('efecto_escritura.js', contexto);
    return { eventos, llamadas, entrada, contexto, superficie,
        insertar: opciones => eventos.get('input')({ target: entrada, isTrusted: true,
            inputType: 'insertText', data: '1', ...opciones }) };
}

prueba('teclado reinicia una sola animación sin consultar el bloqueo general de movimiento', () => {
    const cliente = crearPulso();
    cliente.insertar();
    cliente.insertar();
    afirmar.deepEqual(cliente.llamadas,
        ['escritura-activa', 'cancelar', 'reproducir', 'escritura-activa', 'cancelar', 'reproducir']);
    afirmar.equal(cliente.eventos.size, 1);
    cargarAssetCliente('efecto_escritura.js', cliente.contexto);
    afirmar.equal(cliente.eventos.size, 1);
});

for (const opciones of [{ isTrusted: false }, { inputType: 'insertFromPaste' },
    { inputType: 'insertFromDrop' }, { inputType: 'deleteContentBackward' },
    { inputType: 'insertCompositionText' }, { data: null }]) {
    prueba(`omite entradas ajenas a tecleo: ${JSON.stringify(opciones)}`, () => {
        const cliente = crearPulso();
        cliente.insertar(opciones);
        afirmar.deepEqual(cliente.llamadas, []);
    });
}

prueba('campos de solo lectura, deshabilitados o ajenos no reciben el pulso', () => {
    const cliente = crearPulso();
    cliente.entrada.readOnly = true;
    cliente.insertar();
    cliente.entrada.readOnly = false;
    cliente.entrada.disabled = true;
    cliente.insertar();
    cliente.entrada.disabled = false;
    cliente.entrada.closest = () => null;
    cliente.insertar();
    afirmar.deepEqual(cliente.llamadas, []);
});
