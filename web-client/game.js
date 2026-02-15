/**
 * Roam Web Client
 * Browser-based game client for Roam
 * 
 * @author Daniel McCoy Stephenson
 */

// Direction constants for better code readability
const DIRECTION = {
    UP: 0,
    LEFT: 1,
    DOWN: 2,
    RIGHT: 3
};

// Configuration
// When running through docker-compose, the web client is served by nginx which proxies API requests
// Use relative URLs when served through a proxy (ports 80/443/8000), direct connection for standalone development
const usingProxy = window.location.port === '' || window.location.port === '80' || window.location.port === '443' || window.location.port === '8000';

const API_BASE_URL = usingProxy
    // Use relative URLs; nginx will proxy API requests to the backend
    ? ''
    // Standalone: connect directly to backend server
    : 'http://localhost:8080';

const WS_BASE_URL = usingProxy
    // Match WebSocket protocol to page protocol
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
    // Standalone: connect directly to backend WebSocket
    : 'ws://localhost:8080';

// Game state
let gameState = {
    accessToken: null,
    refreshToken: null,
    sessionId: null,
    player: null,
    worldState: null,
    ws: null,
    stompClient: null,
    lastUpdateTime: Date.now(),
    keys: {},
    gathering: false,
    running: false,
    crouching: false,
    movePending: false,
    reconnectAttempts: 0,
    maxReconnectAttempts: 10,
    refreshInProgress: false
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
    
    // Check if we have a saved token (use sessionStorage for better XSS protection)
    const savedToken = sessionStorage.getItem('accessToken');
    if (savedToken) {
        gameState.accessToken = savedToken;
        gameState.refreshToken = sessionStorage.getItem('refreshToken');
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
    
    // Input validation
    if (!username || !password) {
        errorEl.textContent = 'Please enter username and password';
        return;
    }
    
    // Basic input sanitization - server will do comprehensive validation
    // Client-side check is just for UX feedback
    const username_clean = username.replace(/[<>'"]/g, '');
    if (username_clean !== username) {
        errorEl.textContent = 'Username contains invalid characters';
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
        
        // Save tokens to sessionStorage (more secure than localStorage against XSS)
        sessionStorage.setItem('accessToken', data.accessToken);
        sessionStorage.setItem('refreshToken', data.refreshToken);
        
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
    
    // Input validation
    if (!username || !email || !password) {
        errorEl.textContent = 'Please fill in all fields';
        return;
    }
    
    // Basic input sanitization - server will do comprehensive validation
    // Client-side check is just for UX feedback
    const username_clean = username.replace(/[<>'"]/g, '');
    const email_clean = email.replace(/[<>'"]/g, '');
    if (username_clean !== username || email_clean !== email) {
        errorEl.textContent = 'Input contains invalid characters';
        return;
    }
    
    // Basic email format validation (server will do comprehensive validation)
    if (!email.includes('@') || !email.includes('.')) {
        errorEl.textContent = 'Invalid email format';
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
    if (gameState.stompClient) {
        gameState.stompClient.disconnect();
    }
    if (gameState.ws) {
        gameState.ws.close();
    }
    
    // Clear tokens from sessionStorage
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
    gameState.accessToken = null;
    gameState.refreshToken = null;
    gameState.sessionId = null;
    gameState.stompClient = null;
    
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
        const errorMsg = 'Failed to initialize game: ' + error.message;
        updateConnectionStatus(errorMsg);
        // Show error in UI instead of alert
        const loginError = document.getElementById('login-error');
        if (loginError) {
            loginError.textContent = errorMsg;
        }
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
        // Token expired, try to refresh (but prevent infinite loops)
        if (gameState.refreshToken && !gameState.refreshInProgress) {
            try {
                gameState.refreshInProgress = true;
                await refreshToken();
                gameState.refreshInProgress = false;
                // Retry the request once
                return apiRequest(method, endpoint, body);
            } catch (refreshError) {
                gameState.refreshInProgress = false;
                handleLogout();
                throw new Error('Authentication expired');
            }
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
    sessionStorage.setItem('accessToken', data.accessToken);
}

// === WebSocket ===

function connectWebSocket() {
    // Reset reconnection attempts on explicit connect
    if (!gameState.stompClient || !gameState.stompClient.connected) {
        gameState.reconnectAttempts = 0;
    }
    
    updateConnectionStatus('Connecting...');
    
    // Use STOMP over SockJS for WebSocket connection (matches server configuration)
    // SockJS provides fallback mechanisms for browsers that don't support WebSocket
    const wsUrl = `${WS_BASE_URL}/ws`;
    
    // Create STOMP client with SockJS
    gameState.stompClient = new StompJs.Client({
        webSocketFactory: () => new SockJS(wsUrl),
        connectHeaders: {
            // Pass authentication token in STOMP headers
            Authorization: `Bearer ${gameState.accessToken}`
        },
        debug: (str) => {
            // Only log in development (when on non-standard ports)
            if (window.location.port && !['80', '443', '8000'].includes(window.location.port)) {
                console.log('STOMP: ' + str);
            }
        },
        reconnectDelay: 0, // Disable automatic reconnection, we'll handle it manually
        heartbeatIncoming: 4000,
        heartbeatOutgoing: 4000
    });
    
    gameState.stompClient.onConnect = (frame) => {
        console.log('WebSocket connected', frame);
        updateConnectionStatus('Connected');
        gameState.reconnectAttempts = 0; // Reset on successful connection
        
        // Subscribe to session-specific topics
        gameState.stompClient.subscribe(`/topic/session/${gameState.sessionId}/player`, (message) => {
            try {
                const data = JSON.parse(message.body);
                handleWebSocketMessage({ type: 'PLAYER_UPDATE', data });
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        });
        
        gameState.stompClient.subscribe(`/topic/session/${gameState.sessionId}/tick`, (message) => {
            try {
                const data = JSON.parse(message.body);
                handleWebSocketMessage({ type: 'TICK_UPDATE', data });
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        });
    };
    
    gameState.stompClient.onStompError = (frame) => {
        console.error('STOMP error:', frame.headers['message'], frame.body);
        updateConnectionStatus('Error');
    };
    
    gameState.stompClient.onWebSocketError = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('Error');
    };
    
    gameState.stompClient.onDisconnect = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('Disconnected');
        
        // Attempt to reconnect with exponential backoff if we're still logged in
        if (gameState.accessToken && gameState.sessionId) {
            scheduleReconnect();
        }
    };
    
    // Activate the STOMP client
    gameState.stompClient.activate();
}

function scheduleReconnect() {
    if (gameState.reconnectAttempts >= gameState.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        updateConnectionStatus('Connection failed');
        return;
    }
    
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, 60s, 60s...
    const baseDelay = 1000; // 1 second
    const maxDelay = 60000; // 60 seconds
    const delay = Math.min(baseDelay * Math.pow(2, gameState.reconnectAttempts), maxDelay);
    
    gameState.reconnectAttempts++;
    
    console.log(`Reconnecting in ${delay/1000}s (attempt ${gameState.reconnectAttempts}/${gameState.maxReconnectAttempts})`);
    updateConnectionStatus(`Reconnecting in ${delay/1000}s...`);
    
    setTimeout(() => {
        if (gameState.accessToken && gameState.sessionId) {
            connectWebSocket();
        }
    }, delay);
}

function handleWebSocketMessage(message) {
    if (message.type === 'PLAYER_UPDATE') {
        // Update player position from WebSocket
        if (message.data) {
            gameState.player = { ...gameState.player, ...message.data };
            updateUI();
        }
    } else if (message.type === 'TICK_UPDATE') {
        // Handle game tick updates
        if (message.data) {
            // Update any tick-based state
            console.log('Tick update:', message.data);
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
    // Prevent race condition - only one move at a time
    if (gameState.movePending) {
        return;
    }
    
    try {
        gameState.movePending = true;
        await sendAction('move', { direction });
    } catch (error) {
        console.error('Move action failed:', error);
    } finally {
        gameState.movePending = false;
    }
}

// === Game Loop ===

function gameLoop() {
    const now = Date.now();
    const deltaTime = now - gameState.lastUpdateTime;
    
    // Process movement input (throttled to avoid spamming server)
    // Minimum 200ms between moves (maximum rate: 5 moves per second)
    if (deltaTime > 200 && !gameState.movePending) {
        // Process in priority order: only one direction per frame
        if (gameState.keys['w']) {
            sendMoveAction(DIRECTION.UP);
            gameState.lastUpdateTime = now;
        } else if (gameState.keys['s']) {
            sendMoveAction(DIRECTION.DOWN);
            gameState.lastUpdateTime = now;
        } else if (gameState.keys['a']) {
            sendMoveAction(DIRECTION.LEFT);
            gameState.lastUpdateTime = now;
        } else if (gameState.keys['d']) {
            sendMoveAction(DIRECTION.RIGHT);
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
