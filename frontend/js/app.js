// 打開指定模式
function openMode(mode) {
    const routes = {
        'rpg': '/RPG_Project/rpg_game.html',
        'simulation': '/app',
        'chat': '/personal_chat.html',
        'test': '/test'
    };
    
    if (routes[mode]) {
        window.location.href = routes[mode];
    }
}

// 檢查後端服務狀態
async function checkBackendStatus() {
    try {
        const response = await fetch('http://localhost:8000/');
        if (response.ok) {
            console.log('✅ 後端服務運行正常');
            return true;
        }
    } catch (error) {
        console.warn('⚠️ 後端服務未運行，部分功能可能無法使用');
        console.log('請執行: python backend/main.py');
        
        // 顯示警告提示
        const warning = document.createElement('div');
        warning.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff9800;
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            z-index: 9999;
            font-weight: bold;
        `;
        warning.textContent = '⚠️ 後端服務未運行，請先啟動: python backend/main.py';
        document.body.appendChild(warning);
        
        setTimeout(() => warning.remove(), 5000);
        return false;
    }
}

// 頁面加載時檢查
window.addEventListener('load', () => {
    checkBackendStatus();
});

// 添加鍵盤快捷鍵
document.addEventListener('keydown', function(e) {
    if (e.key === '1') openMode('rpg');
    if (e.key === '2') openMode('simulation');
    if (e.key === '3') openMode('chat');
    if (e.key === '4') openMode('test');
    
    // ESC 鍵返回首頁（如果在子頁面）
    if (e.key === 'Escape') {
        if (window.location.pathname !== '/') {
            window.location.href = '/';
        }
    }
});

// 添加工具提示
console.log(`
╔════════════════════════════════════════╗
║   🛡️  AI 防詐騙訓練系統 v2.0          ║
╠════════════════════════════════════════╣
║  快捷鍵：                               ║
║  1 - RPG 遊戲模式                      ║
║  2 - 自動模擬模式                      ║
║  3 - 個人對話模式 (新)                 ║
║  4 - API 測試模式                      ║
║  ESC - 返回首頁                        ║
╚════════════════════════════════════════╝
`);
