const API_BASE = 'http://127.0.0.1:8000/api/v1';
let authMode = 'login';

// Elements
const authForm = document.getElementById('auth-form');
const authView = document.getElementById('auth-view');
const dashboardView = document.getElementById('dashboard-view');
const authError = document.getElementById('auth-error');
const userDisplay = document.getElementById('user-display');
const accessPreview = document.getElementById('access-preview');
const profileData = document.getElementById('profile-data');

// Switch between Login and Register
function switchAuthMode(mode) {
    authMode = mode;
    document.getElementById('tab-login').classList.toggle('active', mode === 'login');
    document.getElementById('tab-register').classList.toggle('active', mode === 'register');
    document.getElementById('auth-subtitle').textContent = mode === 'login' ? 'Secure Asynchronous Portal' : 'Create Enterprise Account';
    document.getElementById('submit-btn').textContent = mode === 'login' ? 'Authenticate' : 'Create Account';
    authError.classList.add('hidden');
}

// Handle Auth Submission
authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    const endpoint = authMode === 'login' ? '/auth/login' : '/auth/register';
    const body = authMode === 'login' 
        ? JSON.stringify({ email, password })
        : JSON.stringify({ email, password });

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }

        if (authMode === 'register') {
            showToast('Registration successful! Please login.');
            switchAuthMode('login');
        } else {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            showDashboard();
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

    authView.classList.add('hidden');
    dashboardView.classList.remove('hidden');
    accessPreview.textContent = token.substring(0, 15) + '...';

    try {
        const response = await fetch(`${API_BASE}/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Session expired');

        const user = await response.json();
        userDisplay.textContent = user.email;
        profileData.innerHTML = `
            <div class="detail">
                <span class="label">User ID</span>
                <code>#${user.id}</code>
            </div>
            <div class="detail">
                <span class="label">Created At</span>
                <code>${new Date(user.created_at).toLocaleString()}</code>
            </div>
            <div class="detail">
                <span class="label">Privileges</span>
                <code>${user.is_superuser ? 'Superuser' : 'Standard User'}</code>
            </div>
        `;
    } catch (err) {
        handleLogout();
    }
}

// Handle Refresh
async function handleRefresh() {
    const refreshToken = localStorage.getItem('refresh_token');
    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        const data = await response.json();
        if (!response.ok) throw new Error('Refresh failed');

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        showToast('Token Rotated Successfully');
        showDashboard();
    } catch (err) {
        showToast('Session Expired', true);
        handleLogout();
    }
}

// Handle Logout (Stateful Revocation)
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
    toast.style.background = isError ? 'var(--error)' : 'var(--primary)';
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

// Auto-login check
if (localStorage.getItem('access_token')) {
    showDashboard();
}
