const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function leer(rel) {
    return fs.readFileSync(rel, 'utf8');
}

// 1. inicializacion_glosa.js en / sin ?glosa=1 nunca abre desde localStorage
{
    const attrs = new Map();
    const ctx = vm.createContext({
        location: { pathname: '/', search: '' },
        localStorage: { getItem: () => 'abierto' },
        window: { matchMedia: () => ({ matches: true }) },
        document: { documentElement: { setAttribute: (k, v) => attrs.set(k, v) } },
    });
    vm.runInContext(leer('src/frontend/recursos/js/glosa/inicializacion_glosa.js'), ctx);
    assert.equal(attrs.get('data-glosa'), 'cerrado');
}

// 2. glosa_panel_lateral.js expone destruir() y escucha click en fase de captura
{
    const clicks = [];
    const doc = {
        documentElement: {
            setAttribute() {}, removeAttribute() {}, hasAttribute: () => false,
            getAttribute: () => 'cerrado', style: { removeProperty() {} },
        },
        addEventListener: (ev, fn, cap) => { if (ev === 'click') clicks.push({ fn, cap }); },
        removeEventListener: (ev, fn, cap) => {
            if (ev === 'click') {
                const idx = clicks.findIndex(c => c.fn === fn && c.cap === cap);
                if (idx >= 0) clicks.splice(idx, 1);
            }
        },
        getElementById: () => ({ inert: false, setAttribute() {}, removeAttribute() {}, style: { setProperty() {}, removeProperty() {} } }),
        querySelector: () => null,
        querySelectorAll: () => [],
        dispatchEvent() {},
    };
    const ctx = vm.createContext({
        window: { matchMedia: () => ({ matches: false }), addEventListener() {}, removeEventListener() {} },
        document: doc,
        getComputedStyle: () => ({ getPropertyValue: () => 'desplazar' }),
        CustomEvent: function() {},
    });
    vm.runInContext(leer('src/frontend/recursos/js/glosa/glosa_panel_lateral.js'), ctx);
    assert.equal(clicks.length, 1);
    assert.equal(clicks[0].cap, true);
    assert.equal(typeof ctx.window.scalaris.glosa.destruir, 'function');
    ctx.window.scalaris.glosa.destruir();
    assert.equal(clicks.length, 0);
}

// 3. preferencia_sonido.js sincroniza aria-label y [data-sonido-estado]
{
    const attrs = new Map([['aria-pressed', 'false']]);
    const estado = { textContent: 'Activados' };
    const boton = {
        setAttribute: (k, v) => attrs.set(k, v),
        getAttribute: k => attrs.get(k) ?? null,
        querySelectorAll: () => [],
        querySelector: s => (s === '[data-sonido-estado]' ? estado : null),
        closest: s => (s === '[data-sonido-control]' ? boton : null),
    };
    let onClick;
    const ctx = vm.createContext({
        window: { scalaris: { catalogoSonidos: { claveSilencio: 'k' }, sonido: { silenciar() {} } }, addEventListener() {} },
        document: {
            documentElement: {},
            querySelectorAll: () => [boton],
            addEventListener: (ev, fn) => { if (ev === 'click') onClick = fn; },
        },
        localStorage: { getItem: () => 'false', setItem() {} },
        MutationObserver: class { observe() {} disconnect() {} },
    });
    vm.runInContext(leer('src/frontend/recursos/js/sonido/eventos/preferencia_sonido.js'), ctx);
    assert.equal(attrs.get('aria-label'), 'Silenciar sonidos');
    onClick({ isTrusted: true, defaultPrevented: false, button: 0, target: boton });
    assert.equal(attrs.get('aria-label'), 'Activar sonidos');
    assert.equal(estado.textContent, 'Silenciados');
}

// 4. rechazo_entrada_numerica.js asigna aria-invalid y aria-describedby y limpia al cambiar pestaña
{
    const attrs = new Map();
    const aviso = { id: 'captura-aviso-numerico', setAttribute() {}, replaceChildren(n) { this.textContent = n.textContent; }, textContent: '' };
    const entrada = {
        setAttribute: (k, v) => attrs.set(k, v),
        getAttribute: k => attrs.get(k) ?? null,
        removeAttribute: k => attrs.delete(k),
        closest: () => null,
    };
    let onClick;
    const ctx = vm.createContext({
        window: { scalaris: {} },
        document: {
            body: { appendChild() {} },
            getElementById: id => (id === 'captura-aviso-numerico' ? aviso : null),
            createElement: () => aviso,
            createTextNode: t => ({ textContent: t }),
            addEventListener: (ev, fn) => { if (ev === 'click') onClick = fn; },
        },
    });
    vm.runInContext(leer('src/frontend/recursos/js/captura/entrada/rechazo_entrada_numerica.js'), ctx);
    ctx.window.scalaris.rechazoNumerico.rechazar(entrada, 'Solo números', false);
    assert.equal(attrs.get('aria-invalid'), 'true');
    assert.ok(attrs.get('aria-describedby').includes('captura-aviso-numerico'));
    onClick({ target: { closest: s => (s === '[role="tab"]' ? {} : null) } });
    assert.equal(attrs.has('aria-invalid'), false);
    assert.equal(attrs.has('aria-describedby'), false);
    assert.equal(aviso.textContent, '');
}
