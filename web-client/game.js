/**
 * Roam Web Client
 * Browser-based game client for Roam
 * 
 * @author Daniel McCoy Stephenson
 */

// Configuration
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8080' 
    : `${window.location.protocol}//${window.location.hostname}:8080`;

const WS_BASE_URL = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://');

// Game state
let gameState = {
    accessToken: null,
    refreshToken: null,
    sessionId: null,
    player: null,
    worldState: null,
    ws: null,
    lastUpdateTime: Date.now(),
    keys: {},
    gathering: false,
    running: false,
    crouching: false
};

// Canvas
let canvas, ctx;
const TILE_SIZE = 32;
const VIEWPORT_WIDTH = 25;
const VIEWPORT_HEIGHT = 19;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    setupAuthUI();
    canvas = document.getElementById('game-canvas');
    ctx = canvas.getContext('2d');
    
    // Check if we have a saved token
    const savedToken = localStorage.getItem('accessToken');
    if (savedToken) {
        gameState.accessToken = savedToken;
        gameState.refreshToken = localStorage.getItem('refreshToken');
        // Try to restore session
        initGame();
    }
});

// === Authentication UI ===

function setupAuthUI() {
    const loginBtn = document.getElementById('login-btn');
    const registerBtn = document.getElementById('register-btn');
    const showRegister = document.getElementById('show-register');
    const showLogin = document.getElementById('show-login');
    const logoutBtn = document.getElementById('logout-btn');

    loginBtn.addEventListener('click', handleLogin);
    registerBtn.addEventListener('click', handleRegister);
    showRegister.addEventListener('click', () => toggleAuthForm(true));
    showLogin.addEventListener('click', () => toggleAuthForm(false));
    logoutBtn.addEventListener('click', handleLogout);

    // Handle Enter key
    ['login-username', 'login-password'].forEach(id => {
        document.getElementById(id).addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleLogin();
        });
    });

    ['register-username', 'register-email', 'register-password'].forEach(id => {
        document.getElementById(id).addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleRegister();
        });
    });
}

function toggleAuthForm(showRegister) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (showRegister) {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
    } else {
        registerForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
    }
    
    // Clear errors
    document.getElementById('login-error').textContent = '';
    document.getElementById('register-error').textContent = '';
    document.getElementById('register-success').textContent = '';
}

async function handleLogin() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');
    
    if (!username || !password) {
        errorEl.textContent = 'Please enter username and password';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Login failed');
        }
        
        const data = await response.json();
        gameState.accessToken = data.accessToken;
        gameState.refreshToken = data.refreshToken;
        
        // Save tokens
        localStorage.setItem('accessToken', data.accessToken);
        localStorage.setItem('refreshToken', data.refreshToken);
        
        // Initialize game
        await initGame();
    } catch (error) {
        errorEl.textContent = error.message;
        console.error('Login error:', error);
    }
}

async function handleRegister() {
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const errorEl = document.getElementById('register-error');
    const successEl = document.getElementById('register-success');
    
    errorEl.textContent = '';
    successEl.textContent = '';
    
    if (!username || !email || !password) {
        errorEl.textContent = 'Please fill in all fields';
        return;
    }
    
    if (password.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Registration failed');
        }
        
        successEl.textContent = 'Registration successful! Please login.';
        setTimeout(() => toggleAuthForm(false), 2000);
    } catch (error) {
        errorEl.textContent = error.message;
        console.error('Registration error:', error);
    }
}

function handleLogout() {
    if (gameState.ws) {
        gameState.ws.close();
    }
    
    // Clear tokens
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    gameState.accessToken = null;
    gameState.refreshToken = null;
    gameState.sessionId = null;
    
    // Show auth screen
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('auth-screen').style.display = 'block';
}

// === Game Initialization ===

async function initGame() {
    try {
        updateConnectionStatus('Initializing session...');
        
        // Create a new game session
        const sessionResponse = await apiRequest('POST', '/api/v1/session/init', {});
        gameState.sessionId = sessionResponse.sessionId;
        
        console.log('Session initialized:', gameState.sessionId);
        
        // Get initial player state
        await updatePlayerState();
        
        // Connect WebSocket for real-time updates
        connectWebSocket();
        
        // Show game screen
        document.getElementById('auth-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'flex';
        
        // Setup input handlers
        setupInputHandlers();
        
        // Start game loop
        gameLoop();
        
    } catch (error) {
        console.error('Game initialization error:', error);
        alert('Failed to initialize game: ' + error.message);
        handleLogout();
    }
}

// === API Communication ===

async function apiRequest(method, endpoint, body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (gameState.accessToken) {
        options.headers['Authorization'] = `Bearer ${gameState.accessToken}`;
    }
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (response.status === 401) {
        // Token expired, try to refresh
        if (gameState.refreshToken) {
            await refreshToken();
            // Retry the request
            return apiRequest(method, endpoint, body);
        } else {
            handleLogout();
            throw new Error('Authentication expired');
        }
    }
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || `Request failed with status ${response.status}`);
    }
    
    if (response.status === 204) {
        return {};
    }
    
    return response.json();
}

async function refreshToken() {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: gameState.refreshToken })
    });
    
    if (!response.ok) {
        throw new Error('Token refresh failed');
    }
    
    const data = await response.json();
    gameState.accessToken = data.accessToken;
    localStorage.setItem('accessToken', data.accessToken);
}

// === WebSocket ===

function connectWebSocket() {
    // Note: Token is passed in URL query parameter as required by the server's WebSocket security configuration.
    // In a production environment, consider implementing token-based authentication via Sec-WebSocket-Protocol header
    // to avoid exposing tokens in server logs and browser history.
    const wsUrl = `${WS_BASE_URL}/ws?access_token=${gameState.accessToken}`;
    
    gameState.ws = new WebSocket(wsUrl);
    
    gameState.ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus('Connected');
        
        // Subscribe to session topics
        const subscribeMsg = {
            type: 'SUBSCRIBE',
            destination: `/topic/session/${gameState.sessionId}/player`
        };
        gameState.ws.send(JSON.stringify(subscribeMsg));
    };
    
    gameState.ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        } catch (error) {
            console.error('WebSocket message error:', error);
        }
    };
    
    gameState.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('Error');
    };
    
    gameState.ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('Disconnected');
        
        // Attempt to reconnect after 5 seconds if we're still logged in
        if (gameState.accessToken) {
            setTimeout(() => {
                if (gameState.accessToken && gameState.sessionId) {
                    connectWebSocket();
                }
            }, 5000);
        }
    };
}

function handleWebSocketMessage(message) {
    if (message.type === 'PLAYER_UPDATE') {
        // Update player position from WebSocket
        if (message.data) {
            gameState.player = { ...gameState.player, ...message.data };
            updateUI();
        }
    }
}

// === Player State ===

async function updatePlayerState() {
    try {
        const playerData = await apiRequest('GET', `/api/v1/session/${gameState.sessionId}/player`);
        gameState.player = playerData;
        updateUI();
    } catch (error) {
        console.error('Failed to update player state:', error);
    }
}

// === Input Handling ===

function setupInputHandlers() {
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
}

function handleKeyDown(e) {
    gameState.keys[e.key.toLowerCase()] = true;
    
    // Handle toggle actions
    if (e.key === 'Shift' && !gameState.running) {
        gameState.running = true;
        sendAction('run', { running: true });
    } else if (e.key === 'Control' && !gameState.crouching) {
        gameState.crouching = true;
        sendAction('crouch', { crouching: true });
    } else if (e.key === ' ' && !gameState.gathering) {
        e.preventDefault();
        gameState.gathering = true;
        sendAction('gather', { gathering: true });
    }
}

function handleKeyUp(e) {
    gameState.keys[e.key.toLowerCase()] = false;
    
    // Handle toggle actions
    if (e.key === 'Shift' && gameState.running) {
        gameState.running = false;
        sendAction('run', { running: false });
    } else if (e.key === 'Control' && gameState.crouching) {
        gameState.crouching = false;
        sendAction('crouch', { crouching: false });
    } else if (e.key === ' ' && gameState.gathering) {
        e.preventDefault();
        gameState.gathering = false;
        sendAction('gather', { gathering: false });
    }
}

// === Game Actions ===

async function sendAction(action, params = {}) {
    try {
        const actionData = { action, ...params };
        const response = await apiRequest('POST', `/api/v1/session/${gameState.sessionId}/player/action`, actionData);
        gameState.player = response;
        updateUI();
    } catch (error) {
        console.error(`Failed to send ${action} action:`, error);
    }
}

async function sendMoveAction(direction) {
    try {
        await sendAction('move', { direction });
    } catch (error) {
        console.error('Move action failed:', error);
    }
}

// === Game Loop ===

function gameLoop() {
    const now = Date.now();
    const deltaTime = now - gameState.lastUpdateTime;
    
    // Process movement input (throttled to avoid spamming server)
    if (deltaTime > 200) { // Minimum 200ms between moves (maximum rate: 5 moves per second)
        if (gameState.keys['w']) {
            sendMoveAction(0); // UP
        } else if (gameState.keys['s']) {
            sendMoveAction(2); // DOWN
        } else if (gameState.keys['a']) {
            sendMoveAction(1); // LEFT
        } else if (gameState.keys['d']) {
            sendMoveAction(3); // RIGHT
        }
        
        if (gameState.keys['w'] || gameState.keys['s'] || gameState.keys['a'] || gameState.keys['d']) {
            gameState.lastUpdateTime = now;
        }
    }
    
    // Render the game
    render();
    
    // Continue loop
    requestAnimationFrame(gameLoop);
}

// === Rendering ===

function render() {
    // Clear canvas
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    if (!gameState.player) {
        return;
    }
    
    // Draw grid background
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 1;
    for (let x = 0; x < VIEWPORT_WIDTH; x++) {
        for (let y = 0; y < VIEWPORT_HEIGHT; y++) {
            ctx.strokeRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }
    }
    
    // Draw player at center
    const centerX = Math.floor(VIEWPORT_WIDTH / 2);
    const centerY = Math.floor(VIEWPORT_HEIGHT / 2);
    
    // Player tile
    ctx.fillStyle = '#4ecca3';
    ctx.fillRect(centerX * TILE_SIZE, centerY * TILE_SIZE, TILE_SIZE, TILE_SIZE);
    
    // Player indicator (circle)
    ctx.fillStyle = gameState.running ? '#ff6b6b' : (gameState.crouching ? '#ffd93d' : '#1a1a2e');
    ctx.beginPath();
    ctx.arc(
        centerX * TILE_SIZE + TILE_SIZE / 2,
        centerY * TILE_SIZE + TILE_SIZE / 2,
        TILE_SIZE / 3,
        0,
        Math.PI * 2
    );
    ctx.fill();
    
    // Draw status text on canvas
    ctx.fillStyle = '#4ecca3';
    ctx.font = '12px Arial';
    ctx.fillText(`Pos: (${gameState.player.x}, ${gameState.player.y})`, 10, 20);
    
    if (gameState.gathering) {
        ctx.fillStyle = '#ffd93d';
        ctx.fillText('GATHERING', canvas.width - 90, 20);
    }
}

// === UI Updates ===

function updateUI() {
    if (!gameState.player) return;
    
    document.getElementById('player-pos').textContent = `(${gameState.player.x}, ${gameState.player.y})`;
    document.getElementById('player-energy').textContent = `${Math.round(gameState.player.energy || 0)}%`;
    
    const statusParts = [];
    if (gameState.running) statusParts.push('Running');
    if (gameState.crouching) statusParts.push('Crouching');
    if (gameState.gathering) statusParts.push('Gathering');
    
    document.getElementById('player-status').textContent = statusParts.length > 0 ? statusParts.join(', ') : 'Idle';
}

function updateConnectionStatus(status) {
    const statusEl = document.getElementById('connection-status');
    statusEl.textContent = status;
    
    const colors = {
        'Connected': '#4ecca3',
        'Connecting...': '#ffd93d',
        'Disconnected': '#ff6b6b',
        'Error': '#ff6b6b'
    };
    
    statusEl.style.color = colors[status] || '#b0b0b0';
}
