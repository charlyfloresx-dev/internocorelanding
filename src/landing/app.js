/* ═══════════════════════════════════════════════
   InternoCore Landing — app.js v2
   Animaciones: Motion (vanilla framer-motion engine)
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

    // ── Motion API (CDN expone window.Motion) ──────────────────────────
    const M = window.Motion || {};
    const animate = M.animate;
    const inView  = M.inView;
    const stagger = M.stagger;
    const hasMotion = !!(animate && inView && stagger);

    // ── Scroll Progress Bar ────────────────────────────────────────────
    const progressBar = document.getElementById('scroll-progress');
    if (progressBar) {
        const updateProgress = () => {
            const scrollTop = document.documentElement.scrollTop;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            progressBar.style.width = docHeight > 0
                ? Math.min((scrollTop / docHeight) * 100, 100) + '%'
                : '0%';
        };
        window.addEventListener('scroll', updateProgress, { passive: true });
    }

    // ── Navbar shrink on scroll ────────────────────────────────────────
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            navbar.classList.toggle('scrolled', window.scrollY > 60);
        }, { passive: true });
    }

    // ── Mobile Menu ────────────────────────────────────────────────────
    const menuToggle = document.getElementById('menuToggle');
    const navLinks   = document.getElementById('navLinks');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            const isOpen = navLinks.classList.toggle('open');
            menuToggle.classList.toggle('active', isOpen);
            document.body.style.overflow = isOpen ? 'hidden' : '';
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('open');
                menuToggle.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }

    // ── Motion: Staggered scroll reveals ──────────────────────────────
    if (hasMotion) {

        // Feature cards — stagger in from below
        inView('.feature-grid', () => {
            animate(
                '.feature-card',
                { opacity: [0, 1], y: [32, 0] },
                { delay: stagger(0.08), duration: 0.5, easing: 'ease-out' }
            );
        }, { amount: 0.05 });

        // Pricing cards
        inView('.pricing-grid', () => {
            animate(
                '.price-card',
                { opacity: [0, 1], y: [24, 0] },
                { delay: stagger(0.12), duration: 0.5, easing: 'ease-out' }
            );
        }, { amount: 0.05 });

        // Security — slide from sides
        inView('.security-text', ({ target }) => {
            animate(target, { opacity: [0, 1], x: [-28, 0] }, { duration: 0.6, easing: 'ease-out' });
        }, { amount: 0.2 });

        inView('.security-visual', ({ target }) => {
            animate(target, { opacity: [0, 1], x: [28, 0] }, { duration: 0.6, easing: 'ease-out' });
        }, { amount: 0.2 });

        // Architect — slide from sides
        inView('.architect-info', ({ target }) => {
            animate(target, { opacity: [0, 1], x: [-28, 0] }, { duration: 0.6, easing: 'ease-out' });
        }, { amount: 0.2 });

        inView('.architect-skills', ({ target }) => {
            animate(target, { opacity: [0, 1], x: [28, 0] }, { duration: 0.6, easing: 'ease-out' });
        }, { amount: 0.2 });

        // Skill list items cascade
        inView('.skill-list', () => {
            animate(
                '.skill-list li',
                { opacity: [0, 1], x: [-16, 0] },
                { delay: stagger(0.1), duration: 0.4, easing: 'ease-out' }
            );
        }, { amount: 0.3 });

        // Tech bar items
        inView('.tech-logos', () => {
            animate(
                '.tech-item',
                { opacity: [0, 1], y: [10, 0] },
                { delay: stagger(0.07), duration: 0.35, easing: 'ease-out' }
            );
        }, { amount: 0.5 });

        // Section headers
        inView('.section-header', ({ target }) => {
            animate(target, { opacity: [0, 1], y: [20, 0] }, { duration: 0.5, easing: 'ease-out' });
        }, { amount: 0.3 });

        // Hero badge — spring bounce
        inView('.hero-content .badge', ({ target }) => {
            animate(target,
                { opacity: [0, 1], scale: [0.75, 1] },
                { duration: 0.45, easing: [0.34, 1.56, 0.64, 1] }
            );
        });

        // Hero content stagger
        inView('.hero-content', () => {
            animate('.hero-content h1',
                { opacity: [0, 1], y: [20, 0] },
                { delay: 0.1, duration: 0.55, easing: 'ease-out' }
            );
            animate('.hero-content .lead',
                { opacity: [0, 1], y: [16, 0] },
                { delay: 0.22, duration: 0.5, easing: 'ease-out' }
            );
            animate('.hero-btns',
                { opacity: [0, 1], y: [12, 0] },
                { delay: 0.34, duration: 0.45, easing: 'ease-out' }
            );
            animate('.hero-stats',
                { opacity: [0, 1], y: [12, 0] },
                { delay: 0.46, duration: 0.45, easing: 'ease-out' }
            );
        }, { amount: 0.3 });

        // Dashboard mockup
        inView('.hero-visual', ({ target }) => {
            animate(target,
                { opacity: [0, 1], x: [40, 0] },
                { delay: 0.2, duration: 0.65, easing: 'ease-out' }
            );
        }, { amount: 0.3 });

        // Milestone cards
        inView('.milestones', () => {
            animate('.milestone',
                { opacity: [0, 1], x: [-12, 0] },
                { delay: stagger(0.1), duration: 0.4, easing: 'ease-out' }
            );
        }, { amount: 0.2 });

    } else {
        // Fallback: make all animated elements visible immediately
        document.querySelectorAll('.feature-card, .price-card').forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'none';
        });
    }

    // ── Animated Number Counters ───────────────────────────────────────
    const easeOutCubic = t => 1 - Math.pow(1 - t, 3);

    const animateCounter = (el, from, to, prefix, suffix, decimals, duration = 1800) => {
        const start = performance.now();
        const tick = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const value = from + (to - from) * easeOutCubic(progress);
            const formatted = decimals > 0
                ? value.toFixed(decimals)
                : Math.round(value).toLocaleString('en-US');
            el.textContent = (prefix || '') + formatted + (suffix || '');
            if (progress < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    };

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;
            const to       = parseFloat(el.dataset.to || '0');
            const from     = parseFloat(el.dataset.from || '0');
            const prefix   = el.dataset.prefix  || '';
            const suffix   = el.dataset.suffix  || '';
            const decimals = String(el.dataset.to || '').includes('.') ? 2 : 0;
            animateCounter(el, from, to, prefix, suffix, decimals);
            counterObserver.unobserve(el);
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.counter').forEach(el => counterObserver.observe(el));

    // ── Live Audit Stream Typewriter ───────────────────────────────────
    const auditLogs = [
        { time: '12:45:01', tag: 'ROUTING_VALID',     ref: 'STEP_WELDING',     type: 'ok'    },
        { time: '12:47:03', tag: 'AUTH_REJECTED',     ref: 'BAD_TRAINING',     type: 'alert' },
        { time: '12:50:18', tag: 'INVENTORY_MUTATED', ref: 'SKU_450',          type: 'ok'    },
        { time: '12:52:44', tag: 'WO_COMPLETED',      ref: 'WO-2026-1891',     type: 'ok'    },
        { time: '12:55:07', tag: 'RFID_SCAN',         ref: 'LINEA_4_A',        type: 'ok'    },
        { time: '12:57:33', tag: 'ANDON_TRIGGERED',   ref: 'TIEMPO_MUERTO',    type: 'alert' },
        { time: '13:00:11', tag: 'WO_STARTED',        ref: 'WO-2026-1895',     type: 'ok'    },
        { time: '13:02:45', tag: 'SCOPE_DENIED',      ref: 'USER_READONLY',    type: 'alert' },
        { time: '13:05:22', tag: 'KARDEX_UPDATED',    ref: 'SKU_TURBO-001',    type: 'ok'    },
    ];

    const auditStream = document.getElementById('auditStream');
    if (auditStream) {
        let logIdx = auditLogs.length;

        const addLine = () => {
            const log  = auditLogs[logIdx % auditLogs.length];
            logIdx++;

            const line = document.createElement('div');
            line.className = 'audit-line';
            line.style.cssText = 'opacity:0; transition: opacity 0.35s ease;';
            line.innerHTML = `
                <span class="audit-time">${log.time}</span>
                <span class="audit-tag ${log.type === 'alert' ? 'alert-tag' : 'ok'}">${log.tag}</span>
                <span class="audit-ref">${log.ref}</span>
            `;
            auditStream.appendChild(line);
            requestAnimationFrame(() => { line.style.opacity = '1'; });

            // Keep only last 5 lines visible
            while (auditStream.children.length > 5) {
                const first = auditStream.firstElementChild;
                if (!first) break;
                first.style.opacity = '0';
                setTimeout(() => first.remove(), 350);
                break;
            }
        };

        setInterval(addLine, 2800);
    }

    // ── Hero Dashboard — live KPI tick ─────────────────────────────────
    const kpiOee = document.getElementById('kpi-oee');
    const kpiWip = document.getElementById('kpi-wip');
    if (kpiOee && kpiWip) {
        const kpiTick = () => {
            const oee = (85 + Math.random() * 5).toFixed(1);
            const wip = Math.round(1220 + Math.random() * 60).toLocaleString('en-US');
            kpiOee.textContent = oee + '%';
            kpiWip.textContent = wip;
        };
        setTimeout(() => {
            kpiTick();
            setInterval(kpiTick, 4000);
        }, 3000);
    }

    // ── i18n ───────────────────────────────────────────────────────────
    let currentLang = localStorage.getItem('ic_lang') || 'es';
    let translations = {};

    const getNestedValue = (obj, path) =>
        path.split('.').reduce((acc, part) => acc && acc[part], obj);

    const applyTranslations = () => {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const val = getNestedValue(translations, key);
            if (!val) return;
            if (Array.isArray(val)) {
                el.innerHTML = val.map(item => `<li><i class="fas fa-check"></i> ${item}</li>`).join('');
            } else {
                el.innerHTML = val;
            }
        });
    };

    const updateLangSwitcher = (lang) => {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
        });
    };

    const loadTranslations = async (lang) => {
        try {
            const res = await fetch(`./locales/${lang}.json`);
            translations = await res.json();
            applyTranslations();
            updateLangSwitcher(lang);
        } catch (err) {
            console.error('[i18n] Failed to load:', lang, err);
        }
    };

    window.switchLanguage = (lang) => {
        currentLang = lang;
        localStorage.setItem('ic_lang', lang);
        loadTranslations(lang);
    };

    loadTranslations(currentLang);
});
