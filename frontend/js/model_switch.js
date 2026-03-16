/**
 * 模型切換管理器
 * 處理 Ollama 和 Gemini 之間的動態切換
 * 配置直接從 backend/.env 讀取，無需前端輸入
 */

class ModelSwitchManager {
    constructor() {
        this.currentProvider = 'ollama';
        this.apiBaseUrl = 'https://anti-fraudx-backend-5gznvtwxga-uc.a.run.app';
        this.init();
    }

    async init() {
        console.log('[ModelSwitch] 初始化模型切換管理器');
        
        // 獲取當前模型狀態
        await this.fetchModelStatus();
        
        // 綁定事件監聽器
        this.bindEvents();
    }

    bindEvents() {
        const switchBtn = document.getElementById('modelSwitchBtn');
        if (switchBtn) {
            switchBtn.addEventListener('click', () => this.handleSwitchClick());
        }
    }

    async fetchModelStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/model/status`);
            const data = await response.json();
            
            if (data.success) {
                this.currentProvider = data.current_provider;
                this.updateUI(data);
                console.log('[ModelSwitch] 當前提供者:', this.currentProvider);
            }
        } catch (error) {
            console.error('[ModelSwitch] 獲取模型狀態失敗:', error);
            this.showError('無法連接到後端服務');
        }
    }

    updateUI(data) {
        const label = document.getElementById('currentModelLabel');
        const indicator = document.getElementById('modelIndicator');
        const switchBtn = document.getElementById('modelSwitchBtn');
        const switchText = document.getElementById('switchText');
        const modelIcon = indicator.querySelector('.model-icon');

        console.log('[ModelSwitch] Updating UI:', data.current_provider);

        if (data.current_provider === 'gemini') {
            // Gemini 模式
            label.textContent = 'Gemini API';
            label.style.color = '#0984E3';
            modelIcon.textContent = '✨';
            switchText.textContent = '切換至 Ollama';
            switchBtn.classList.add('active');
            switchBtn.style.background = 'linear-gradient(135deg, #0984E3 0%, #74B9FF 100%)';
            
            console.log('[ModelSwitch] ✅ UI updated to Gemini mode');
        } else {
            // Ollama 模式
            label.textContent = 'Ollama 本地';
            label.style.color = '#00B894';
            modelIcon.textContent = '🤖';
            switchText.textContent = '切換至 Gemini';
            switchBtn.classList.remove('active');
            switchBtn.style.background = 'linear-gradient(135deg, #6C5CE7 0%, #A29BFE 100%)';
            
            console.log('[ModelSwitch] ✅ UI updated to Ollama mode');
        }
        
        // 添加動畫效果
        switchBtn.style.transform = 'scale(1.05)';
        setTimeout(() => {
            switchBtn.style.transform = 'scale(1)';
        }, 200);
    }

    handleSwitchClick() {
        const targetProvider = this.currentProvider === 'ollama' ? 'gemini' : 'ollama';
        
        if (targetProvider === 'gemini') {
            // 切換到 Gemini，檢查是否已配置
            this.checkGeminiConfig();
        } else {
            // 切換到 Ollama，直接顯示確認對話框
            this.showSwitchModal('ollama');
        }
    }

    async checkGeminiConfig() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/model/status`);
            const data = await response.json();
            
            if (data.gemini_configured) {
                // 已配置，直接切換
                this.showSwitchModal('gemini');
            } else {
                // 未配置，顯示錯誤提示
                this.showError(
                    '未檢測到 Gemini 配置。\n\n' +
                    '請在 backend/.env 文件中設置：\n' +
                    'GEMINI_ENABLED=true\n' +
                    'GEMINI_API_KEY=你的API Key\n' +
                    'GEMINI_MODEL_SCAMMER=gemini-3.1-flash-lite-preview\n' +
                    'GEMINI_MODEL_VICTIM=gemini-3.1-flash-lite-preview\n' +
                    'GEMINI_MODEL_EXPERT=gemini-3.1-flash-lite-preview\n' +
                    'GEMINI_MODEL_RECORDER=gemini-3.1-flash-lite-preview\n\n' +
                    '然後重啟後端服務。'
                );
            }
        } catch (error) {
            console.error('[ModelSwitch] 檢查配置失敗:', error);
            this.showError('無法連接到後端服務，請確認後端已啟動。');
        }
    }

    showSwitchModal(targetProvider) {
        const modal = document.getElementById('switchModal');
        const message = document.getElementById('switchMessage');
        const currentProviderEl = document.getElementById('currentProvider');
        const targetProviderEl = document.getElementById('targetProvider');

        const providerNames = {
            'ollama': 'Ollama 本地模型',
            'gemini': 'Google Gemini API'
        };

        message.textContent = '確定要切換模型提供者嗎？切換後將立即生效。';
        currentProviderEl.textContent = providerNames[this.currentProvider];
        targetProviderEl.textContent = providerNames[targetProvider];

        modal.style.display = 'flex';
        modal.dataset.targetProvider = targetProvider;
    }

    async confirmSwitch() {
        const modal = document.getElementById('switchModal');
        const targetProvider = modal.dataset.targetProvider;
        
        console.log('[ModelSwitch] Confirming switch to:', targetProvider);
        
        try {
            this.showLoading('切換中...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/model/switch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    use_gemini: targetProvider === 'gemini'
                })
            });

            const data = await response.json();
            
            console.log('[ModelSwitch] Switch response:', data);

            if (data.success) {
                this.showSuccess(`已成功切換至 ${targetProvider === 'gemini' ? 'Gemini' : 'Ollama'}`);
                
                // 更新當前提供者
                this.currentProvider = targetProvider;
                
                // 重新獲取狀態並更新 UI
                await this.fetchModelStatus();
                
                this.closeSwitchModal();
            } else {
                throw new Error(data.detail?.message || data.message || '切換失敗');
            }
        } catch (error) {
            console.error('[ModelSwitch] 切換失敗:', error);
            this.showError('切換失敗: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showLoading(message) {
        // 簡單的 loading 提示
        console.log('[ModelSwitch] Loading:', message);
    }

    hideLoading() {
        console.log('[ModelSwitch] Loading complete');
    }

    showSuccess(message) {
        alert('✓ ' + message);
    }

    showError(message) {
        alert('✗ ' + message);
    }

    closeSwitchModal() {
        document.getElementById('switchModal').style.display = 'none';
    }
}

// 全局函數（供 HTML 調用）
function closeSwitchModal() {
    if (window.modelSwitchManager) {
        window.modelSwitchManager.closeSwitchModal();
    }
}

function confirmSwitch() {
    if (window.modelSwitchManager) {
        window.modelSwitchManager.confirmSwitch();
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.modelSwitchManager = new ModelSwitchManager();
});
