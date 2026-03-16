// RPGv2 遊戲模式 JavaScript

const API_BASE_URL = 'https://anti-fraudx-backend-5gznvtwxga-uc.a.run.app/api/rpgv2';

// 全局狀態
let currentSessionId = null;
let currentMode = null;
let gameSettings = {
    mode: null,
    scamType: '假冒銀行',
    victimPersona: 'average',
    difficulty: 'normal'
};

// DOM 元素
const views = {
    modeSelect: document.getElementById('mode-select'),
    gamePlay: document.getElementById('game-play'),
    gameResult: document.getElementById('game-result')
};

const navTabs = document.querySelectorAll('.nav-tab');
const modeCards = document.querySelectorAll('.mode-card');
const gameSettingsDiv = document.getElementById('game-settings');
const loadingOverlay = document.getElementById('loading-overlay');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadGameModes();
});

// 初始化事件監聽器
function initEventListeners() {
    // 模式選擇
    document.querySelectorAll('.mode-select-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const mode = e.target.dataset.mode;
            selectMode(mode);
        });
    });

    // 開始遊戲
    document.getElementById('start-game-btn').addEventListener('click', startGame);
    document.getElementById('cancel-settings-btn').addEventListener('click', () => {
        gameSettingsDiv.style.display = 'none';
        modeCards.forEach(card => card.classList.remove('selected'));
    });

    // 遊戲操作
    document.getElementById('send-message-btn').addEventListener('click', sendMessage);
    document.getElementById('auto-play-btn').addEventListener('click', autoPlay);
    document.getElementById('end-game-btn').addEventListener('click', endGame);

    // 結果操作
    document.getElementById('play-again-btn').addEventListener('click', playAgain);
    document.getElementById('back-to-menu-btn').addEventListener('click', backToMenu);

    // 輸入框回車發送
    document.getElementById('player-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 導航標籤
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const viewName = tab.dataset.view;
            if (!tab.disabled) {
                switchView(viewName);
            }
        });
    });
}

// 載入遊戲模式
async function loadGameModes() {
    try {
        const response = await fetch(`${API_BASE_URL}/game/modes`);
        const data = await response.json();
        
        if (data.success) {
            console.log('遊戲模式載入成功:', data.modes);
        }
    } catch (error) {
        console.error('載入遊戲模式失敗:', error);
        showNotification('無法連接到服務器', 'error');
    }
}

// 選擇模式
function selectMode(mode) {
    gameSettings.mode = mode;
    currentMode = mode;
    
    // 更新UI
    modeCards.forEach(card => {
        if (card.dataset.mode === mode) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
    
    // 顯示設置
    gameSettingsDiv.style.display = 'block';
    gameSettingsDiv.scrollIntoView({ behavior: 'smooth' });
}

// 開始遊戲
async function startGame() {
    // 獲取設置
    gameSettings.scamType = document.getElementById('scam-type').value;
    gameSettings.victimPersona = document.getElementById('victim-persona').value;
    gameSettings.difficulty = document.getElementById('difficulty').value;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: gameSettings.mode,
                scam_type: gameSettings.scamType,
                victim_persona: gameSettings.victimPersona,
                difficulty: gameSettings.difficulty
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = data.session_id;
            
            // 初始化遊戲界面
            initGameUI(data);
            
            // 顯示開場消息
            data.opening_messages.forEach(msg => {
                addMessage(msg.role, msg.content);
            });
            
            // 切換到遊戲界面
            switchView('game-play');
            enableNavTab('game-play');
            
            showNotification('遊戲開始！', 'success');
        } else {
            showNotification('開始遊戲失敗', 'error');
        }
    } catch (error) {
        console.error('開始遊戲錯誤:', error);
        showNotification('無法開始遊戲', 'error');
    } finally {
        showLoading(false);
    }
}

// 初始化遊戲UI
function initGameUI(data) {
    // 設置模式信息
    const modeNames = {
        'scammer': '騙徒模式',
        'expert': '專家模式',
        'auto': '自動模式'
    };
    document.getElementById('current-mode').textContent = modeNames[data.mode];
    
    // 重置數據
    updateGameState(data.game_state);
    
    // 清空消息
    document.getElementById('messages-container').innerHTML = '';
    
    // 顯示/隱藏自動播放按鈕
    const autoPlayBtn = document.getElementById('auto-play-btn');
    const playerInput = document.getElementById('player-input');
    const sendBtn = document.getElementById('send-message-btn');
    
    if (data.mode === 'auto') {
        autoPlayBtn.style.display = 'block';
        playerInput.disabled = true;
        sendBtn.disabled = true;
    } else {
        autoPlayBtn.style.display = 'none';
        playerInput.disabled = false;
        sendBtn.disabled = false;
    }
    
    // 騙徒模式：顯示提示，讓玩家先開始對話
    if (data.mode === 'scammer') {
        const container = document.getElementById('messages-container');
        const hintDiv = document.createElement('div');
        hintDiv.className = 'system-hint';
        hintDiv.innerHTML = `
            <div class="hint-icon">💡</div>
            <div class="hint-content">
                <strong>遊戲開始！</strong><br>
                你是騙徒，請發送第一條消息開始詐騙對話。<br>
                <em>提示：可以使用權威身份、製造緊急情況或利用情感策略。</em>
            </div>
        `;
        container.appendChild(hintDiv);
    }
}

// 發送消息
async function sendMessage() {
    const input = document.getElementById('player-input');
    const message = input.value.trim();
    
    if (!message) {
        showNotification('請輸入消息', 'warning');
        return;
    }
    
    // 添加玩家消息到界面
    addMessage('player', message);
    input.value = '';
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message,
                action_type: 'message'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 添加AI回應
            data.ai_responses.forEach(response => {
                addMessage(response.role, response.content);
            });
            
            // 更新遊戲狀態
            updateGameState(data.game_state);
            
            // 顯示分數變化
            if (data.score_update.player > 0) {
                showScoreChange(data.score_update.player);
            }
            
            // 檢查遊戲是否結束
            if (data.game_status.game_over) {
                setTimeout(() => {
                    showGameResult(data.game_status);
                }, 1000);
            }
        } else {
            showNotification('發送消息失敗', 'error');
        }
    } catch (error) {
        console.error('發送消息錯誤:', error);
        showNotification('無法發送消息', 'error');
    } finally {
        showLoading(false);
    }
}

// 自動播放
async function autoPlay() {
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/auto-play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                rounds: 3
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 逐條顯示消息
            for (const msg of data.messages) {
                addMessage(msg.role, msg.content);
                await sleep(500);
            }
            
            // 更新遊戲狀態
            updateGameState(data.game_state);
            
            // 檢查遊戲是否結束
            if (data.game_status.game_over) {
                setTimeout(() => {
                    showGameResult(data.game_status);
                }, 1000);
            }
        } else {
            showNotification('自動播放失敗', 'error');
        }
    } catch (error) {
        console.error('自動播放錯誤:', error);
        showNotification('無法自動播放', 'error');
    } finally {
        showLoading(false);
    }
}

// 結束遊戲
async function endGame() {
    if (!confirm('確定要結束遊戲嗎？')) {
        return;
    }
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE_URL}/game/state/${currentSessionId}`);
        const data = await response.json();
        
        if (data.success) {
            // 構建遊戲狀態
            const gameStatus = {
                game_over: true,
                winner: 'none',
                reason: '玩家主動結束遊戲',
                final_scores: {
                    player: data.player_score,
                    ai: data.ai_score
                },
                final_trust: data.trust_data
            };
            
            showGameResult(gameStatus);
        }
        
        // 刪除會話
        await fetch(`${API_BASE_URL}/game/session/${currentSessionId}`, {
            method: 'DELETE'
        });
    } catch (error) {
        console.error('結束遊戲錯誤:', error);
    } finally {
        showLoading(false);
    }
}

// 添加消息到界面
function addMessage(role, content) {
    const container = document.getElementById('messages-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const roleIcons = {
        'player': '👤',
        'scammer': '🎭',
        'victim': '👨',
        'expert': '🛡️'
    };
    
    const roleNames = {
        'player': '玩家',
        'scammer': '騙徒',
        'victim': '受害者',
        'expert': '防詐專家'
    };
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role-icon">${roleIcons[role]}</span>
            <span>${roleNames[role]}</span>
        </div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// 更新遊戲狀態
function updateGameState(state) {
    document.getElementById('round-count').textContent = state.round_count;
    document.getElementById('player-score').textContent = state.player_score;
    document.getElementById('ai-score').textContent = state.ai_score;
    
    updateTrustMeter('trust-scammer', state.trust_in_scammer);
    updateTrustMeter('trust-expert', state.trust_in_expert);
    updateTrustMeter('alertness', state.alertness);
}

// 更新信任度儀表
function updateTrustMeter(id, value) {
    const bar = document.getElementById(`${id}-bar`);
    const valueSpan = document.getElementById(`${id}-value`);
    
    bar.style.width = `${value}%`;
    valueSpan.textContent = Math.round(value);
}

// 顯示分數變化
function showScoreChange(points) {
    const scoreElement = document.getElementById('player-score');
    const changeDiv = document.createElement('div');
    changeDiv.textContent = `+${points}`;
    changeDiv.style.cssText = `
        position: absolute;
        color: #10b981;
        font-weight: bold;
        animation: scoreFloat 1s ease-out;
    `;
    scoreElement.parentElement.style.position = 'relative';
    scoreElement.parentElement.appendChild(changeDiv);
    
    setTimeout(() => changeDiv.remove(), 1000);
}

// 顯示遊戲結果
function showGameResult(gameStatus) {
    const resultIcon = document.getElementById('result-icon');
    const resultTitle = document.getElementById('result-title');
    const resultSubtitle = document.getElementById('result-subtitle');
    
    // 設置結果圖標和標題
    if (gameStatus.winner === 'player') {
        resultIcon.textContent = '🎉';
        resultTitle.textContent = '勝利！';
        resultSubtitle.textContent = gameStatus.reason;
    } else if (gameStatus.winner === 'ai') {
        resultIcon.textContent = '😔';
        resultTitle.textContent = '失敗';
        resultSubtitle.textContent = gameStatus.reason;
    } else {
        resultIcon.textContent = '🤝';
        resultTitle.textContent = '遊戲結束';
        resultSubtitle.textContent = gameStatus.reason;
    }
    
    // 設置分數
    document.getElementById('final-player-score').textContent = gameStatus.final_scores.player;
    document.getElementById('final-ai-score').textContent = gameStatus.final_scores.ai;
    document.getElementById('final-rounds').textContent = document.getElementById('round-count').textContent;
    
    // 設置信任度數據
    const trustData = gameStatus.final_trust;
    setFinalTrustBar('final-trust-scammer', trustData.trust_in_scammer);
    setFinalTrustBar('final-trust-expert', trustData.trust_in_expert);
    setFinalTrustBar('final-alertness', trustData.alertness);
    
    // 切換到結果界面
    switchView('game-result');
    enableNavTab('game-result');
}

// 設置最終信任度條
function setFinalTrustBar(id, value) {
    const bar = document.getElementById(id);
    const valueSpan = document.getElementById(`${id}-value`);
    
    bar.style.width = `${value}%`;
    valueSpan.textContent = Math.round(value);
}

// 再玩一次
function playAgain() {
    // 重置狀態
    currentSessionId = null;
    
    // 返回模式選擇
    switchView('mode-select');
    disableNavTab('game-play');
    disableNavTab('game-result');
    
    // 重新選擇相同模式
    if (currentMode) {
        selectMode(currentMode);
    }
}

// 返回主菜單
function backToMenu() {
    // 重置所有狀態
    currentSessionId = null;
    currentMode = null;
    gameSettings.mode = null;
    
    // 返回模式選擇
    switchView('mode-select');
    disableNavTab('game-play');
    disableNavTab('game-result');
    
    // 隱藏設置
    gameSettingsDiv.style.display = 'none';
    modeCards.forEach(card => card.classList.remove('selected'));
}

// 切換視圖
function switchView(viewName) {
    Object.values(views).forEach(view => view.classList.remove('active'));
    views[viewName].classList.add('active');
    
    navTabs.forEach(tab => {
        if (tab.dataset.view === viewName) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
}

// 啟用導航標籤
function enableNavTab(viewName) {
    navTabs.forEach(tab => {
        if (tab.dataset.view === viewName) {
            tab.disabled = false;
        }
    });
}

// 禁用導航標籤
function disableNavTab(viewName) {
    navTabs.forEach(tab => {
        if (tab.dataset.view === viewName) {
            tab.disabled = true;
        }
    });
}

// 顯示/隱藏載入提示
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 顯示通知
function showNotification(message, type = 'info') {
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#6366f1'
    };
    
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 2000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 工具函數
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 添加CSS動畫
const style = document.createElement('style');
style.textContent = `
    @keyframes scoreFloat {
        0% { transform: translateY(0); opacity: 1; }
        100% { transform: translateY(-30px); opacity: 0; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
