'use strict';
const fs = require('node:fs'), os = require('node:os'), rutas = require('node:path');
const afirmar = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_CORE || 'C:/Users/stive/AppData/Local/npm-cache/_npx/e41f203b7505f1fb/node_modules/playwright-core');
const ejecutable = process.env.CHROMIUM || 'C:/Users/stive/AppData/Local/ms-playwright/chromium-1248/chrome-win64/chrome.exe';
const base = 'http://127.0.0.1:8080';
const directorio = __dirname;

async function crearNavegador() { return chromium.launch({ executablePath: ejecutable, headless: true }); }

async function crearContexto(navegador, opciones = {}) {
    const contexto = await navegador.newContext({ viewport: { width: opciones.ancho || 1440, height: 1000 },
        reducedMotion: opciones.reducido ? 'reduce' : 'no-preference' });
    await prepararContexto(contexto, opciones);
    return contexto;
}

async function crearZoom(opciones = {}) {
    const perfil = fs.mkdtempSync(rutas.join(os.tmpdir(), 'scalaris-zoom-'));
    const extension = rutas.join(perfil, 'extension'); fs.mkdirSync(extension);
    fs.writeFileSync(rutas.join(extension, 'manifest.json'), JSON.stringify({ manifest_version: 3,
        name: 'Verificar zoom', version: '1.0', permissions: ['tabs'], background: { service_worker: 'zoom.js' } }));
    fs.writeFileSync(rutas.join(extension, 'zoom.js'), 'chrome.runtime.onInstalled.addListener(()=>{});');
    const contexto = await chromium.launchPersistentContext(perfil, { executablePath: ejecutable, headless: true,
        viewport: null, args: ['--window-size=1440,1000', `--disable-extensions-except=${extension}`, `--load-extension=${extension}`] });
    await prepararContexto(contexto, opciones);
    contexto.aplicarZoom = async () => {
        const trabajador = contexto.serviceWorkers()[0] || await contexto.waitForEvent('serviceworker');
        return trabajador.evaluate(async () => {
            const pestanas = await chrome.tabs.query({});
            const objetivo = pestanas.find(p => p.url?.startsWith('http://127.0.0.1:8080/'));
            await chrome.tabs.setZoom(objetivo.id, 2);
            return chrome.tabs.getZoom(objetivo.id);
        });
    };
    return contexto;
}

async function prepararContexto(contexto, opciones) {
    contexto.setDefaultTimeout(12000);
    await contexto.addInitScript(({ tema, presentacion }) => {
        if (location.protocol !== 'http:') return;
        if (tema && !localStorage.getItem('tema')) localStorage.setItem('tema', tema);
        if (!presentacion) sessionStorage.setItem('presentacion-mostrada', '1');
        window.rechazos = [];
        addEventListener('unhandledrejection', e => window.rechazos.push(String(e.reason)));
        window.animacionesVerificadas = [];
        const animar = Element.prototype.animate;
        Element.prototype.animate = function (fotogramas, configuracion) {
            const animacion = animar.call(this, fotogramas, configuracion);
            const registro = { elemento: this.id || this.className, fotogramas, configuracion, inicio: performance.now() };
            window.animacionesVerificadas.push(registro);
            animacion.finished.then(() => { registro.fin = performance.now(); }, () => { registro.cancelada = performance.now(); });
            return animacion;
        };
    }, { tema: opciones.tema, presentacion: opciones.presentacion });
}

function observarErrores(pagina) {
    const errores = [];
    pagina.on('pageerror', e => errores.push(e.message));
    pagina.on('console', mensaje => { if (mensaje.type() === 'error') errores.push(mensaje.text()); });
    return errores;
}

async function estable(pagina) {
    await pagina.locator('main').first().waitFor();
    await pagina.waitForFunction(() => !document.documentElement.hasAttribute('data-navegacion-circular') &&
        !document.documentElement.hasAttribute('data-tema-circular') && !window.scalaris?.presentacion?.activa);
    await pagina.waitForTimeout(100);
}

async function comprobarPagina(pagina) {
    await estable(pagina);
    afirmar.deepEqual(await pagina.evaluate(() => window.rechazos), []);
    afirmar.equal(await pagina.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, 'Desbordamiento horizontal de la página');
    afirmar.equal(await pagina.getByRole('button', { name: /Más álgebra/i }).count(), 0);
    afirmar.equal(await pagina.getByRole('link', { name: /Más álgebra/i }).count(), 0);
    if (!await pagina.locator('.navegacion-cabecera').count()) return;
    for (const control of [pagina.locator('.navegacion-inicio'), pagina.getByRole('button', { name: 'Seleccionar Tema', exact: true })]) {
        const caja = await control.boundingBox(); const ancho = await pagina.evaluate(() => innerWidth);
        afirmar.ok(caja && caja.x >= 0 && caja.x + caja.width <= ancho + 1, 'Inicio o tema fuera de la ventana');
    }
}

async function captura(pagina, nombre) {
    if (!nombre.startsWith('presentacion-')) await pagina.waitForTimeout(350);
    if (await pagina.evaluate(() => devicePixelRatio === 2 && outerWidth / innerWidth > 1.9)) {
        const sesion = await pagina.context().newCDPSession(pagina);
        const resultado = await sesion.send('Page.captureScreenshot', { format:'png', fromSurface:true, captureBeyondViewport:false });
        fs.writeFileSync(rutas.join(directorio, nombre + '.png'), Buffer.from(resultado.data, 'base64'));
        await sesion.detach();
    } else await pagina.screenshot({ path:rutas.join(directorio, nombre + '.png'), fullPage:true });
}
function guardar(nombre, datos) { fs.writeFileSync(rutas.join(directorio, nombre), JSON.stringify(datos, null, 2)); }
module.exports = { afirmar, base, directorio, crearNavegador, crearContexto, crearZoom, observarErrores, estable, comprobarPagina, captura, guardar };
