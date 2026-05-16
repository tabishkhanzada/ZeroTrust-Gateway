const API_BASE = 'http://127.0.0.1:8000/api/v1';
let authMode = 'login';
let ttlInterval;

// Elements
const authForm = document.getElementById('auth-form');
const authView = document.getElementById('auth-view');
const dashboardView = document.getElementById('dashboard-view');
const authError = document.getElementById('auth-error');
const userDisplay = document.getElementById('user-display');
const auditFeed = document.getElementById('audit-feed');
const jwtPayloadDisplay = document.getElementById('jwt-payload');
const ttlProgress = document.getElementById('ttl-progress');
const ttlSeconds = document.getElementById('ttl-seconds');

// Switch between Login and Register
function switchAuthMode(mode) {
    authMode = mode;
    document.getElementById('tab-login').style.background = mode === 'login' ? 'var(--accent)' : 'transparent';
    document.getElementById('tab-register').style.background = mode === 'register' ? 'var(--accent)' : 'transparent';
    document.getElementById('auth-subtitle').textContent = mode === 'login' ? 'Secure Asynchronous Portal' : 'Create Enterprise Account';
    document.getElementById('submit-btn').textContent = mode === 'login' ? 'AUTHENTICATE' : 'CREATE ACCOUNT';
    authError.classList.add('hidden');
}

// Parse JWT Helper
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return null;
    }
}

// Add Audit Entry
function addAudit(msg) {
    const item = document.createElement('div');
    item.className = 'audit-item';
    item.innerHTML = `
        <p class="audit-time">${new Date().toLocaleTimeString()}</p>
        <p>${msg}</p>
    `;
    auditFeed.prepend(item);
}

// Update System Health
async function updateHealth() {
    try {
        const res = await fetch(`${API_BASE}/system/status`);
        const data = await res.json();
        const dbEl = document.getElementById('db-status');
        const redisEl = document.getElementById('redis-status');
        
        dbEl.textContent = data.database.toUpperCase();
        dbEl.style.color = data.database === 'connected' ? 'var(--success)' : 'var(--warning)';
        
        redisEl.textContent = data.redis.toUpperCase();
        redisEl.style.color = data.redis === 'connected' ? 'var(--success)' : 'var(--error)';
        
        document.getElementById('sys-pulse').style.background = data.status === 'operational' ? 'var(--success)' : 'var(--warning)';
    } catch (e) {}
}

// Handle Auth Submission
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
    const payload = { email, password };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Authentication failed');

        if (authMode === 'register') {
            showToast('Registration successful! Please login.');
            switchAuthMode('login');
        } else {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            showDashboard();
            addAudit('Authentication successful');
        }
    } catch (err) {
        authError.textContent = err.message;
        authError.classList.remove('hidden');
    }
});

// Show Dashboard
async function showDashboard() {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const payload = parseJwt(token);
    if (!payload) {
        handleLogout();
        return;
    }

    authView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
    
    userDisplay.textContent = payload.sub || 'Identity Unknown';
    jwtPayloadDisplay.textContent = JSON.stringify(payload, null, 2);

    // Start TTL Countdown
    if (ttlInterval) clearInterval(ttlInterval);
    const updateTTL = () => {
        const now = Math.floor(Date.now() / 1000);
        const remaining = payload.exp - now;
        if (remaining <= 0) {
            handleRefresh();
            return;
        }
        ttlSeconds.textContent = `${remaining}s`;
        const percent = (remaining / 900) * 100; // 15 mins = 900s
        ttlProgress.style.width = `${percent}%`;
        ttlProgress.style.background = remaining < 60 ? 'var(--error)' : (remaining < 300 ? 'var(--warning)' : 'var(--accent)');
    };
    updateTTL();
    ttlInterval = setInterval(updateTTL, 1000);

    updateHealth();
    setInterval(updateHealth, 10000); // Check health every 10s
}

// Handle Refresh
async function handleRefresh() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        handleLogout();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(refreshToken) // Sending raw string for refresh endpoint
        });

        const data = await response.json();
        if (!response.ok) throw new Error('Refresh failed');

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        showToast('Token Rotated Successfully');
        addAudit('Cryptographic key rotation successful');
        showDashboard();
    } catch (err) {
        showToast('Session Expired', true);
        handleLogout();
    }
}

// Handle Logout
async function handleLogout() {
    const token = localStorage.getItem('access_token');
    if (token) {
        try {
            await fetch(`${API_BASE}/auth/logout`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
        } catch (e) {}
    }

    if (ttlInterval) clearInterval(ttlInterval);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    dashboardView.classList.add('hidden');
    authView.classList.remove('hidden');
    showToast('Session Revoked');
}

// Utilities
function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.background = isError ? 'var(--error)' : 'var(--success)';
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

// Auto-login check
if (localStorage.getItem('access_token')) {
    showDashboard();
}
