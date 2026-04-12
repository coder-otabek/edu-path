/* ============================================
   EDUPATH — Main JavaScript
   No external dependencies
   ============================================ */

'use strict';

// ---- Gender Theme ----
(function applyGenderTheme() {
    // Gender ni FAQAT data-gender ga qo'yamiz
    // data-theme ni gender bilan ifloslantirmaymiz — u faqat light/dark uchun!
    const gender = document.body.dataset.gender || localStorage.getItem('edupath_gender') || 'male';
    document.body.setAttribute('data-gender', gender);
    document.documentElement.setAttribute('data-gender', gender);
    localStorage.setItem('edupath_gender', gender);
})();


// ---- Drawer (Sidebar) ----
const drawer = document.getElementById('drawer');
const drawerOverlay = document.getElementById('drawerOverlay');
const hamburger = document.getElementById('hamburger');

function openDrawer() {
    drawer?.classList.add('open');
    drawerOverlay?.classList.add('open');
    hamburger?.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeDrawer() {
    drawer?.classList.remove('open');
    drawerOverlay?.classList.remove('open');
    hamburger?.classList.remove('active');
    document.body.style.overflow = '';
}

hamburger?.addEventListener('click', () => {
    drawer?.classList.contains('open') ? closeDrawer() : openDrawer();
});
drawerOverlay?.addEventListener('click', closeDrawer);

// Close drawer on nav link click (mobile)
drawer?.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', closeDrawer);
});

// ---- Active Bottom Nav ----
// Active nav: Django template orqali boshqariladi

// ---- Floating AI Button — Drag & Drop ----
(function initFAB() {
    const fab = document.getElementById('aiFab');
    if (!fab) return;

    let dragging = false, startX, startY, initX, initY;
    let posX = parseFloat(localStorage.getItem('fab_x') || window.innerWidth - 70);
    let posY = parseFloat(localStorage.getItem('fab_y') || window.innerHeight - 140);

    function setPos(x, y) {
        const r = fab.getBoundingClientRect();
        x = Math.max(0, Math.min(window.innerWidth - r.width, x));
        y = Math.max(72, Math.min(window.innerHeight - r.height - 80, y));
        fab.style.left = x + 'px';
        fab.style.top = y + 'px';
        fab.style.right = 'auto';
        fab.style.bottom = 'auto';
        localStorage.setItem('fab_x', x);
        localStorage.setItem('fab_y', y);
    }

    setPos(posX, posY);

    // Pointer events (works for both mouse and touch)
    fab.addEventListener('pointerdown', e => {
        dragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = fab.getBoundingClientRect();
        initX = rect.left;
        initY = rect.top;
        fab.setPointerCapture(e.pointerId);
        fab.style.transition = 'none';
    });

    fab.addEventListener('pointermove', e => {
        if (!dragging) return;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        setPos(initX + dx, initY + dy);
    });

    fab.addEventListener('pointerup', e => {
        if (!dragging) return;
        dragging = false;
        fab.style.transition = '';
        const dx = Math.abs(e.clientX - startX);
        const dy = Math.abs(e.clientY - startY);
        // If barely moved — treat as click
        if (dx < 6 && dy < 6) {
            window.location.href = fab.dataset.href || '/ai/chat/';
        }
    });
})();

// ---- Progress Bar Animation ----
document.querySelectorAll('.progress-bar-fill').forEach(bar => {
    const target = bar.dataset.value || '0';
    setTimeout(() => {
        bar.style.width = target + '%';
    }, 300);
});

// ---- Password Toggle ----
document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const wrap = btn.closest('.input-toggle');
        const input = wrap?.querySelector('input');
        if (!input) return;
        const isPass = input.type === 'password';
        input.type = isPass ? 'text' : 'password';
        btn.querySelector('.eye-icon')?.classList.toggle('hidden', !isPass);
        btn.querySelector('.eye-off-icon')?.classList.toggle('hidden', isPass);
    });
});

// ---- Auto-dismiss Django Messages ----
document.querySelectorAll('.alert[data-autohide]').forEach(alert => {
    setTimeout(() => {
        alert.style.transition = 'opacity .4s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 400);
    }, 4000);
});

// ---- Simple Toast ----
window.showToast = function (msg, type = 'default') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity .3s';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
};

// ---- PWA Install Prompt ----
let deferredPrompt;
window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    deferredPrompt = e;
    const installBtn = document.getElementById('installPwaBtn');
    if (installBtn) {
        installBtn.style.display = 'flex';
        installBtn.addEventListener('click', async () => {
            deferredPrompt.prompt();
            const {outcome} = await deferredPrompt.userChoice;
            if (outcome === 'accepted') installBtn.remove();
            deferredPrompt = null;
        });
    }
});

// ---- Ripple Effect on Buttons ----
document.querySelectorAll('.btn').forEach(btn => {
    btn.addEventListener('click', function (e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        ripple.style.cssText = `
      position:absolute; border-radius:50%;
      background:rgba(255,255,255,.3);
      width:${size}px; height:${size}px;
      left:${e.clientX - rect.left - size / 2}px;
      top:${e.clientY - rect.top - size / 2}px;
      transform:scale(0); animation:ripple .5s linear;
      pointer-events:none;
    `;
        this.style.position = 'relative';
        this.style.overflow = 'hidden';
        this.appendChild(ripple);
        setTimeout(() => ripple.remove(), 500);
    });
});

// Ripple keyframe
const style = document.createElement('style');
style.textContent = `@keyframes ripple { to { transform:scale(2.5); opacity:0; } }`;
document.head.appendChild(style);

// ---- Tabs ----
document.querySelectorAll('.tabs').forEach(tabGroup => {
    tabGroup.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // Hide/show tab panels
            const panelGroup = tabGroup.dataset.panels;
            if (panelGroup) {
                document.querySelectorAll(`[data-panel="${panelGroup}"]`).forEach(p => {
                    p.style.display = p.dataset.panelId === target ? 'block' : 'none';
                });
            }
        });
    });
});

// ---- Textarea Auto-resize ----
document.querySelectorAll('textarea.auto-resize').forEach(ta => {
    function resize() {
        ta.style.height = 'auto';
        ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
    }

    ta.addEventListener('input', resize);
    resize();
});

// ---- Service Worker (PWA) ----
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .catch(err => console.log('SW registration failed:', err));
    });
}