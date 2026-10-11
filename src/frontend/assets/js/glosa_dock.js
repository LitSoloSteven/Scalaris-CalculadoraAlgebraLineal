(function() {
    window.scalaris = window.scalaris || {};
    window.scalaris.glosa = {
        modo: () => getComputedStyle(document.documentElement).getPropertyValue('--glosa-mode').trim() || 'push',
        estaAbierto: () => document.documentElement.getAttribute('data-glosa') === 'open',
        abrir: (opts = {}) => establecerEstadoGlosa('open', opts),
        cerrar: (opts = {}) => establecerEstadoGlosa('closed', opts),
        alternar: (opts = {}) => establecerEstadoGlosa(window.scalaris.glosa.estaAbierto() ? 'closed' : 'open', opts)
    };

    function animarFlip(objetos, antes, instantaneo, modo, anchoAntes, anchoDespues) {
        if (!instantaneo && anchoAntes === anchoDespues && modo === 'push') {
            const html = document.documentElement;
            const dur = parseFloat(getComputedStyle(html).getPropertyValue('--dur-med')) || 240;
            const ease = getComputedStyle(html).getPropertyValue('--ease-std') || 'cubic-bezier(0.32, 0.72, 0, 1)';
            objetos.forEach(el => {
                const previo = antes.get(el);
                const actual = el.getBoundingClientRect();
                const dx = previo.left - actual.left;
                if (dx !== 0) {
                    el.animate([
                        { transform: `translateX(${dx}px)` },
                        { transform: 'translateX(0)' }
                    ], { duration: dur, easing: ease });
                }
            });
        } else if (modo === 'push' && anchoAntes !== anchoDespues && window.scalaris && window.scalaris.diseno) {
            window.scalaris.diseno.emitir('dock');
        }
    }

    function actualizarAtributosDock(nuevoEstado, modo) {
        const dock = document.getElementById('glosa-dock');
        if (dock) {
            dock.inert = nuevoEstado === 'closed';
            dock.removeAttribute('aria-expanded');
            if (modo !== 'push') {
                dock.setAttribute('role', 'dialog');
                dock.setAttribute('aria-modal', 'true');
            } else {
                dock.setAttribute('role', 'complementary');
                dock.removeAttribute('aria-modal');
            }
            if (nuevoEstado === 'closed') {
                dock.style.setProperty('--glosa-kb', '0px');
            }
        }
        const fab = document.querySelector('.glosa-fab');
        if (fab) {
            fab.setAttribute('aria-expanded', nuevoEstado === 'open' ? 'true' : 'false');
        }
    }

    function gestionarTrampasFoco(nuevoEstado, modo, opts) {
        const dock = document.getElementById('glosa-dock');
        if (modo !== 'push') {
            nuevoEstado === 'open' ? inertOthers(dock) : restoreInert();
        } else {
            restoreInert();
        }

        if (nuevoEstado === 'open') {
            if (modo === 'sheet') history.pushState({ glosa: true }, '');
            const input = dock ? dock.querySelector('.glosa-input textarea') : null;
            const usarInput = window.matchMedia('(pointer: fine)').matches || opts.trigger === 'keyboard';
            setTimeout(() => {
                if (usarInput && input) input.focus();
                else if (dock) dock.focus();
            }, 50);
        } else {
            const fab = document.querySelector('.glosa-fab');
            const elDisparador = opts.triggerEl && (!dock || !dock.contains(opts.triggerEl)) ? opts.triggerEl : fab;
            if (elDisparador) setTimeout(() => elDisparador.focus(), 50);
        }
    }

    function establecerEstadoGlosa(nuevoEstado, opts = {}) {
        if (nuevoEstado === (window.scalaris.glosa.estaAbierto() ? 'open' : 'closed')) return;

        const html = document.documentElement;
        const modo = window.scalaris.glosa.modo();
        const prefiereMovimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const instant = opts.instant || prefiereMovimientoReducido || html.hasAttribute('data-glosa-instant');

        performance.mark('glosa:toggle:start');

        const viewRoot = document.querySelector('.view-root');
        const anchoAntes = viewRoot ? viewRoot.getBoundingClientRect().width : 0;
        const objetosFlip = document.querySelectorAll('.view-root, .crumbs, .q-header .panel-card');
        const mapaAntes = new Map();
        objetosFlip.forEach(el => mapaAntes.set(el, el.getBoundingClientRect()));

        if (instant) html.setAttribute('data-glosa-instant', '');
        html.setAttribute('data-glosa', nuevoEstado);

        if (modo === 'push') {
            try { localStorage.setItem('scalaris:glosa', nuevoEstado); } catch(e) {}
        }

        const anchoDespues = viewRoot ? viewRoot.getBoundingClientRect().width : 0;
        animarFlip(objetosFlip, mapaAntes, instant, modo, anchoAntes, anchoDespues);
        actualizarAtributosDock(nuevoEstado, modo);
        gestionarTrampasFoco(nuevoEstado, modo, opts);

        if (instant) {
            void document.body.offsetHeight;
            requestAnimationFrame(() => html.removeAttribute('data-glosa-instant'));
        }

        performance.mark('glosa:toggle:end');
        performance.measure('glosa:toggle', 'glosa:toggle:start', 'glosa:toggle:end');
        document.dispatchEvent(new CustomEvent('scalaris:glosa', { detail: { open: nuevoEstado === 'open', modo } }));
    }

    document.addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('[data-glosa-toggle]');
        if (toggleBtn) {
            const triggerType = e.detail === 0 ? 'keyboard' : 'mouse';
            window.scalaris.glosa.alternar({ trigger: triggerType, instant: e.detail === 0, triggerEl: toggleBtn });
            return;
        }
        
        const closeBtn = e.target.closest('[data-glosa-close]');
        if (closeBtn) {
            const triggerType = e.detail === 0 ? 'keyboard' : 'mouse';
            window.scalaris.glosa.cerrar({ trigger: triggerType, instant: e.detail === 0, triggerEl: closeBtn });
            if (window.scalaris.glosa.modo() === 'sheet' && history.state && history.state.glosa) {
                history.back();
            }
            return;
        }
        
        if (e.target.closest('.glosa-scrim')) {
            window.scalaris.glosa.cerrar();
            if (window.scalaris.glosa.modo() === 'sheet' && history.state && history.state.glosa) {
                history.back();
            }
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !e.defaultPrevented) {
            const dock = document.getElementById('glosa-dock');
            const inDock = dock && dock.contains(e.target);
            if (inDock || window.scalaris.glosa.modo() !== 'push') {
                window.scalaris.glosa.cerrar({ instant: true, trigger: 'keyboard' });
                if (window.scalaris.glosa.modo() === 'sheet' && history.state && history.state.glosa) {
                    history.back();
                }
            }
        }
    });

    window.addEventListener('popstate', (e) => {
        if (window.scalaris.glosa.modo() === 'sheet' && window.scalaris.glosa.estaAbierto()) {
            if (!e.state || !e.state.glosa) {
                window.scalaris.glosa.cerrar();
            }
        }
    });

    function inertOthers(elTarget) {
        if (!elTarget) return;
        let curr = elTarget;
        while (curr && curr !== document.body && curr !== document.documentElement) {
            const parent = curr.parentElement;
            if (!parent) break;
            Array.from(parent.children).forEach(sibling => {
                if (sibling === curr) return;
                if (sibling.hasAttribute('data-glosa-keep')) return;
                if (sibling.classList.contains('glosa-scrim') || sibling.classList.contains('glosa-dock')) return;
                const tag = sibling.tagName;
                if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'LINK') return;
                if (!sibling.inert) {
                    sibling.setAttribute('data-glosa-inert', '');
                    sibling.inert = true;
                }
            });
            curr = parent;
        }
    }

    function restoreInert() {
        document.querySelectorAll('[data-glosa-inert]').forEach(el => {
            el.removeAttribute('data-glosa-inert');
            el.inert = false;
        });
    }

    if (window.visualViewport) {
        const updateKb = () => {
            if (window.scalaris.glosa.estaAbierto() && window.scalaris.glosa.modo() === 'sheet') {
                const kbHeight = window.innerHeight - window.visualViewport.height;
                const dock = document.getElementById('glosa-dock');
                if (dock) {
                    dock.style.setProperty('--glosa-kb', Math.max(0, kbHeight) + 'px');
                }
            }
        };
        window.visualViewport.addEventListener('resize', updateKb);
        window.visualViewport.addEventListener('scroll', updateKb);
    }
    
    let lastMode = window.scalaris.glosa.modo();
    window.addEventListener('resize', () => {
        const newMode = window.scalaris.glosa.modo();
        if (newMode !== lastMode) {
            if (window.scalaris.glosa.estaAbierto()) {
                if (newMode !== 'push') {
                    window.scalaris.glosa.cerrar({ instant: true });
                } else {
                    restoreInert();
                    const dock = document.getElementById('glosa-dock');
                    if (dock) {
                        dock.setAttribute('role', 'complementary');
                        dock.removeAttribute('aria-modal');
                        dock.style.removeProperty('--glosa-kb');
                    }
                    document.documentElement.style.removeProperty('--glosa-kb');
                }
            }
            lastMode = newMode;
        }
    });

    function initDock() {
        const dock = document.getElementById('glosa-dock');
        const fab = document.querySelector('.glosa-fab');
        if (dock) {
            document.documentElement.setAttribute('data-glosa-ready', '');
            dock.inert = !window.scalaris.glosa.estaAbierto();
            dock.removeAttribute('aria-expanded');
            if (fab) {
                fab.setAttribute('aria-expanded', window.scalaris.glosa.estaAbierto() ? 'true' : 'false');
            }
            return true;
        }
        return false;
    }

    if (!initDock()) {
        const observer = new MutationObserver((mutations, obs) => {
            if (initDock()) {
                obs.disconnect();
            }
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });
    }
})();
