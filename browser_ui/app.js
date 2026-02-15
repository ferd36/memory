// App State
const state = {
    currentView: 'dashboard',
    activeGame: null,
    gameState: 'START', // START, MEMORIZE, RECALL, FEEDBACK, FINISH
    currentRound: 0,
    totalRounds: 10,
    correctCount: 0,
    currentProblem: null,
    results: [],
    sessions: [],
    startTime: null,
    games: []
};

const API_BASE = ''; // Same origin

// UI Elements
const views = document.querySelectorAll('.view');
const navItems = document.querySelectorAll('.nav-item');
const gameGrid = document.getElementById('all-games-list');
const featuredGrid = document.getElementById('featured-games');
const gamePlayer = document.getElementById('game-player');

// Init
document.addEventListener('DOMContentLoaded', async () => {
    initNav();
    await loadGames();
    await loadStats();
    renderDashboard();

    // Game Controls
    document.getElementById('start-game-btn').addEventListener('click', startGame);
    document.getElementById('submit-answer').addEventListener('click', submitAnswer);
    document.getElementById('next-round').addEventListener('click', nextRound);
    document.getElementById('back-to-menu').addEventListener('click', () => switchView('games'));
    document.getElementById('answer-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') submitAnswer();
    });
});

async function loadGames() {
    try {
        const response = await fetch(`${API_BASE}/api/games`);
        if (response.ok) {
            state.games = await response.json();
            initGames();
        }
    } catch (e) {
        console.error("Failed to load games", e);
    }
}

function initNav() {
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const target = item.getAttribute('data-view');
            switchView(target);
        });
    });
}

function switchView(viewId) {
    state.currentView = viewId;
    views.forEach(v => v.classList.remove('active'));
    navItems.forEach(n => n.classList.remove('active'));

    const activeView = document.getElementById(viewId);
    if (activeView) activeView.classList.add('active');

    const activeNav = document.querySelector(`.nav-item[data-view="${viewId}"]`);
    if (activeNav) activeNav.classList.add('active');

    if (viewId === 'dashboard') renderDashboard();
    if (viewId === 'stats') renderStats();
}

function initGames() {
    const icons = {
        'AnagramProblem': '🔠',
        'NumberProblem': '🔢',
        'ArrowDirectionProblem': '🏹',
        'NumberCalculateProblem': '➕',
        'WordListProblem': '📝',
        'GeometryFormsProblem': '📐',
        'FlightInfoProblem': '✈️',
        'TokyoMetroProblem': '🚇',
        'AppointmentsProblem': '📅',
        'MetarProblem': '☁️',
        'AtcProblem': '📻',
        'RoadProblem': '🚗',
        'ChemicalFormulaProblem': '🧪',
        'SequenceRecognitionProblem': '🧩'
    };

    const renderGameCard = (game) => `
        <div class="game-card" onclick="openGame('${game.id}')">
            <div class="icon">${icons[game.class] || '🧠'}</div>
            <h3>${game.name}</h3>
            <p>Test your skills in ${game.name}.</p>
        </div>
    `;

    gameGrid.innerHTML = state.games.map(renderGameCard).join('');
    featuredGrid.innerHTML = state.games.slice(0, 3).map(renderGameCard).join('');
}

function openGame(gameId) {
    state.activeGame = state.games.find(g => g.id === gameId);
    state.gameState = 'START';
    state.currentRound = 0;
    state.correctCount = 0;
    state.results = [];

    switchView('game-player');
    document.getElementById('current-game-name').textContent = state.activeGame.name;
    updateGameStateUI();
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        if (response.ok) {
            const stats = await response.json();
            state.sessions = stats.session_dates.reverse(); // Simplified for chart
            state.lastSession = stats.recent_sessions.length > 0 ? stats.recent_sessions[stats.recent_sessions.length - 1] : null;
            state.totalSessions = stats.total_sessions;
        }
    } catch (e) {
        console.error("Failed to load stats", e);
    }
}

function renderDashboard() {
    if (state.lastSession) {
        document.getElementById('last-score').textContent = `${state.lastSession.score_percentage}%`;
        document.getElementById('total-sessions').textContent = state.totalSessions;
    }
}

function renderStats() {
    const body = document.getElementById('sessions-body');
    body.innerHTML = state.sessions.slice(0, 10).map(s => `
        <tr>
            <td>${s.date}</td>
            <td>Session</td>
            <td>${s.score}%</td>
            <td>--</td>
        </tr>
    `).join('');

    renderChart();
}

function renderChart() {
    const ctx = document.getElementById('scoresChart').getContext('2d');
    if (window.myChart) window.myChart.destroy();

    const data = state.sessions.slice(-7);

    window.myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(s => s.date.split(' ')[0]),
            datasets: [{
                label: 'Score %',
                data: data.map(s => s.score),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100 }
            }
        }
    });
}

// Game Logic
async function startGame() {
    state.startTime = Date.now();
    state.gameState = 'MEMORIZE';
    await nextRound();
}

async function nextRound() {
    if (state.currentRound >= state.totalRounds) {
        await finishGame();
        return;
    }

    state.currentRound++;

    // Fetch problem from Python backend
    try {
        const response = await fetch(`${API_BASE}/api/problem?id=${state.activeGame.id}`);
        state.currentProblem = await response.json();
    } catch (e) {
        console.error("Failed to fetch problem", e);
        return;
    }

    state.gameState = 'MEMORIZE';
    updateGameStateUI();

    // Timer
    const fill = document.getElementById('timer-fill');
    const exposure = state.currentProblem.exposure_ms;
    fill.style.width = '100%';
    fill.style.transition = 'none';

    setTimeout(() => {
        fill.style.transition = `width ${exposure}ms linear`;
        fill.style.width = '0%';
    }, 50);

    setTimeout(() => {
        if (state.gameState === 'MEMORIZE') {
            state.gameState = 'RECALL';
            state.roundStartTime = Date.now();
            updateGameStateUI();
        }
    }, exposure + 50);
}

function updateGameStateUI() {
    const states = ['start', 'memorize', 'recall', 'feedback', 'finish'];
    states.forEach(s => {
        document.querySelector(`.state-${s}`).style.display =
            state.gameState.toLowerCase() === s ? 'block' : 'none';
    });

    if (state.gameState === 'MEMORIZE') {
        document.getElementById('memorize-content').textContent = state.currentProblem.memorize;
        document.getElementById('current-round').textContent = `Round ${state.currentRound}/${state.totalRounds}`;
    }

    if (state.gameState === 'RECALL') {
        document.getElementById('recall-prompt').textContent = state.currentProblem.prompt;
        const input = document.getElementById('answer-input');
        input.value = '';
        input.focus();
    }
}

async function submitAnswer() {
    if (state.gameState !== 'RECALL') return;

    const input = document.getElementById('answer-input').value.trim();
    const responseTime = Date.now() - state.roundStartTime;

    // Evaluate via Python backend
    let score = 0;
    try {
        const response = await fetch(`${API_BASE}/api/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                problem: state.currentProblem,
                user_input: input
            })
        });
        const result = await response.json();
        score = result.score;
    } catch (e) {
        console.error("Evaluation failed", e);
        // Fallback simple comparison if backend fails
        score = input.toLowerCase() === state.currentProblem.solution.toLowerCase() ? 1.0 : 0.0;
    }

    const isCorrect = score >= 1.0;
    if (isCorrect) state.correctCount++;

    state.results.push({
        problem: state.currentProblem,
        response: input,
        response_ms: responseTime,
        score: score
    });

    state.gameState = 'FEEDBACK';
    updateGameStateUI();

    const icon = document.getElementById('feedback-icon');
    const title = document.getElementById('feedback-text');
    const detail = document.getElementById('correct-solution');

    icon.textContent = isCorrect ? '✅' : '❌';
    icon.style.color = isCorrect ? 'var(--success)' : (score > 0.7 ? 'var(--accent)' : 'var(--error)');
    title.textContent = isCorrect ? 'Correct!' : (score > 0.7 ? 'Almost!' : 'Incorrect');
    detail.textContent = state.currentProblem.solution;
}

async function finishGame() {
    state.gameState = 'FINISH';
    updateGameStateUI();

    const scorePct = Math.round((state.correctCount / state.totalRounds) * 100);
    document.getElementById('final-score-val').textContent = `${scorePct}%`;
    document.getElementById('correct-count').textContent = state.correctCount;
    document.getElementById('total-count').textContent = state.totalRounds;

    // Save to Python backend
    try {
        await fetch(`${API_BASE}/api/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: new Date().toISOString().replace('T', ' ').split('.')[0],
                start_time: state.startTime / 1000,
                total_questions: state.totalRounds,
                correct_answers: state.correctCount,
                records: state.results
            })
        });
    } catch (e) {
        console.error("Failed to save session", e);
    }
}
