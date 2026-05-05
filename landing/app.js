document.addEventListener('DOMContentLoaded', () => {
    // Scroll Reveal Logic
    const observerOptions = { threshold: 0.1 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal-visible');
            }
        });
    }, observerOptions);

    const revealElements = document.querySelectorAll('.feature-card, .price-card, .security-text, .security-visual');
    revealElements.forEach(el => {
        el.classList.add('reveal-hidden');
        observer.observe(el);
    });

    // i18n Logic
    let currentLang = localStorage.getItem('ic_lang') || 'es';
    let translations = {};

    const loadTranslations = async (lang) => {
        try {
            const response = await fetch(`./locales/${lang}.json`);
            translations = await response.json();
            applyTranslations();
            updateLangSwitcher(lang);
        } catch (error) {
            console.error('Error loading translations:', error);
        }
    };

    const applyTranslations = () => {
        const elements = document.querySelectorAll('[data-i18n]');
        elements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translation = getNestedValue(translations, key);
            if (translation) {
                if (Array.isArray(translation)) {
                    el.innerHTML = translation.map(item => `<li><i class="fas fa-check"></i> ${item}</li>`).join('');
                } else {
                    el.innerHTML = translation;
                }
            }
        });
    };

    const getNestedValue = (obj, path) => {
        return path.split('.').reduce((acc, part) => acc && acc[part], obj);
    };

    const updateLangSwitcher = (lang) => {
        const buttons = document.querySelectorAll('.lang-btn');
        buttons.forEach(btn => {
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    };

    window.switchLanguage = (lang) => {
        currentLang = lang;
        localStorage.setItem('ic_lang', lang);
        loadTranslations(lang);
    };

    // Initialize
    loadTranslations(currentLang);
});

// CSS Injection for animations
const style = document.createElement('style');
style.textContent = `
    .reveal-hidden {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.8s ease-out;
    }
    .reveal-visible {
        opacity: 1;
        transform: translateY(0);
    }
    .lang-btn.active {
        color: var(--ic-cyan) !important;
        border-bottom: 2px solid var(--ic-cyan);
    }
`;
document.head.appendChild(style);
