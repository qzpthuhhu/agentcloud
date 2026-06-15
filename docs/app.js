// AgentCloud — site animations
// Canvas-based particle network: agents (nodes) drift in the cloud,
// occasionally send "memory packets" (light pulses) along edges.

(() => {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let W = 0, H = 0, dpr = 1;
    let particles = [];
    let pulses = [];
    let mouseX = -9999, mouseY = -9999;

    const COLORS = ['#7C3AED', '#a78bfa', '#ec4899', '#60a5fa', '#34d399'];
    const COUNT_BASE = 60;

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        W = window.innerWidth;
        H = window.innerHeight;
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        // Recompute particle density based on screen area
        const area = (W * H) / (1280 * 800);
        const target = Math.max(40, Math.min(120, Math.round(COUNT_BASE * area)));
        particles = [];
        for (let i = 0; i < target; i++) particles.push(makeParticle());
    }

    function makeParticle() {
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            vx: (Math.random() - 0.5) * 0.25,
            vy: (Math.random() - 0.5) * 0.25,
            r: 1 + Math.random() * 1.8,
            color: COLORS[Math.floor(Math.random() * COLORS.length)],
            phase: Math.random() * Math.PI * 2,
        };
    }

    function makePulse(a, b) {
        return {
            x: a.x, y: a.y,
            tx: b.x, ty: b.y,
            t: 0,
            speed: 0.004 + Math.random() * 0.006,
            color: a.color,
            life: 1.0,
        };
    }

    function step() {
        // Clear with fade for trails
        ctx.fillStyle = 'rgba(10, 11, 16, 0.18)';
        ctx.fillRect(0, 0, W, H);

        // Update + draw particles
        for (const p of particles) {
            p.x += p.vx;
            p.y += p.vy;
            p.phase += 0.02;
            if (p.x < -20) p.x = W + 20;
            if (p.x > W + 20) p.x = -20;
            if (p.y < -20) p.y = H + 20;
            if (p.y > H + 20) p.y = -20;

            // Mouse attraction (subtle)
            const dx = mouseX - p.x;
            const dy = mouseY - p.y;
            const d2 = dx * dx + dy * dy;
            if (d2 < 16000) {
                p.x += dx * 0.0008;
                p.y += dy * 0.0008;
            }

            // Glow
            const pulse = 0.6 + 0.4 * Math.sin(p.phase);
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r * (1 + 0.3 * pulse), 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = 0.5 * pulse + 0.2;
            ctx.shadowBlur = 12;
            ctx.shadowColor = p.color;
            ctx.fill();
            ctx.globalAlpha = 1;
            ctx.shadowBlur = 0;
        }

        // Draw edges between close particles
        ctx.lineWidth = 0.6;
        for (let i = 0; i < particles.length; i++) {
            const a = particles[i];
            for (let j = i + 1; j < particles.length; j++) {
                const b = particles[j];
                const dx = a.x - b.x, dy = a.y - b.y;
                const d2 = dx * dx + dy * dy;
                if (d2 < 14000) {
                    const alpha = (1 - d2 / 14000) * 0.18;
                    ctx.strokeStyle = a.color;
                    ctx.globalAlpha = alpha;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.stroke();
                }
            }
        }
        ctx.globalAlpha = 1;

        // Update + draw pulses (memory packets)
        for (let i = pulses.length - 1; i >= 0; i--) {
            const p = pulses[i];
            p.t += p.speed;
            if (p.t >= 1) { pulses.splice(i, 1); continue; }
            p.life = 1 - p.t;
            const x = p.x + (p.tx - p.x) * p.t;
            const y = p.y + (p.ty - p.y) * p.t;
            ctx.beginPath();
            ctx.arc(x, y, 2.4, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.globalAlpha = p.life;
            ctx.shadowBlur = 16;
            ctx.shadowColor = p.color;
            ctx.fill();
            ctx.globalAlpha = 1;
            ctx.shadowBlur = 0;
        }

        // Occasionally spawn a pulse between two close particles
        if (Math.random() < 0.04 && particles.length > 2) {
            const i = Math.floor(Math.random() * particles.length);
            let best = null, bestD = 14000;
            for (let j = 0; j < particles.length; j++) {
                if (j === i) continue;
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const d2 = dx * dx + dy * dy;
                if (d2 < bestD) { bestD = d2; best = j; }
            }
            if (best !== null) pulses.push(makePulse(particles[i], particles[best]));
        }

        requestAnimationFrame(step);
    }

    // Mouse interaction
    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    window.addEventListener('mouseleave', () => { mouseX = -9999; mouseY = -9999; });

    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(step);
})();


// ========== Scroll reveal ==========
(() => {
    const targets = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window) || targets.length === 0) {
        targets.forEach(t => t.classList.add('reveal--in'));
        return;
    }
    const io = new IntersectionObserver((entries) => {
        for (const e of entries) {
            if (e.isIntersecting) {
                e.target.classList.add('reveal--in');
                io.unobserve(e.target);
            }
        }
    }, { threshold: 0.12, rootMargin: '0px 0px -10% 0px' });
    targets.forEach(t => io.observe(t));
})();


// ========== Copy to clipboard ==========
function copyToClipboard(text, btn) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => flashCopy(btn));
    } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed'; ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); flashCopy(btn); } catch (e) {}
        ta.remove();
    }
}
function flashCopy(btn) {
    if (!btn) return;
    const orig = btn.textContent;
    btn.textContent = '✓ copied';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1600);
}
window.copyToClipboard = copyToClipboard;


// ========== Key request form (app.html) ==========
// v1: collects request + shows a generated demo key. Real issuance
// happens via a webhook to the maintainer in the background.

const DEMO_KEY_PREFIX = 'AC';

function genDemoKey() {
    // Looks like a real AgentCloud master key (base58, ~44 chars).
    // Note: not derived from server — purely client-side demo.
    const alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    let s = DEMO_KEY_PREFIX;
    for (let i = 0; i < 42; i++) s += alphabet[Math.floor(Math.random() * alphabet.length)];
    return s;
}

function genRecoveryCode() {
    const alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    let s = '';
    for (let i = 0; i < 32; i++) s += alphabet[Math.floor(Math.random() * alphabet.length)];
    return s;
}

async function submitRequest(form) {
    const data = new FormData(form);
    const payload = {
        email: data.get('email') || '',
        name: data.get('name') || '',
        use_case: data.get('use_case') || '',
        agent_platform: data.get('agent_platform') || '',
        created_at: new Date().toISOString(),
    };

    // Generate demo key locally (will be replaced by real issuance once
    // /v1/auth/register is wired up to this form via API)
    const key = genDemoKey();
    const recovery = genRecoveryCode();
    const keyId = key.slice(2, 18);

    // Show the key panel
    const result = document.getElementById('key-result');
    result.style.display = 'block';
    document.getElementById('key-id').textContent = keyId;
    document.getElementById('key-value').textContent = key;
    document.getElementById('key-recovery').textContent = recovery;
    document.getElementById('key-result').scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Persist locally so the user can come back and see it
    const existing = JSON.parse(localStorage.getItem('agentcloud.keys') || '[]');
    existing.unshift({
        key_id: keyId,
        key,
        recovery,
        label: payload.name || payload.email,
        created_at: payload.created_at,
    });
    localStorage.setItem('agentcloud.keys', JSON.stringify(existing.slice(0, 5)));
    renderKeyList();

    // Optional: send request payload to a webhook (Formspree / Google Forms)
    // Left as a plug-in point. To enable, set window.AGENTCLOUD_WEBHOOK.
    if (window.AGENTCLOUD_WEBHOOK) {
        try {
            await fetch(window.AGENTCLOUD_WEBHOOK, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...payload, key, recovery, key_id: keyId }),
            });
        } catch (e) {
            console.warn('webhook delivery failed', e);
        }
    }
}

function renderKeyList() {
    const list = document.getElementById('key-list');
    if (!list) return;
    const keys = JSON.parse(localStorage.getItem('agentcloud.keys') || '[]');
    if (keys.length === 0) {
        list.innerHTML = '<li style="color:var(--text-faint);font-style:italic">No keys yet. Request one above.</li>';
        return;
    }
    list.innerHTML = keys.map(k => `
        <li>
            <div>
                <div class="key-list__label">${escapeHtml(k.label || '(unlabeled)')}</div>
                <div class="key-list__id">${k.key_id}…</div>
            </div>
            <div style="display:flex;gap:8px;align-items:center">
                <span class="key-list__date">${new Date(k.created_at).toLocaleDateString()}</span>
                <button class="btn btn--ghost" style="padding:4px 10px;font-size:12px" data-key="${escapeHtml(k.key)}" onclick="copyToClipboard(this.dataset.key, this)">Copy key</button>
            </div>
        </li>
    `).join('');
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

document.addEventListener('DOMContentLoaded', () => {
    renderKeyList();
    const form = document.getElementById('request-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            submitRequest(form);
        });
    }
});
