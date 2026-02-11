/*:
 * @plugindesc AI Bridge Plugin - 連接 RPG Maker MV 與 AI-Agent 系統
 * @author AI-Agent Team
 * @help 
 * ============================================================================
 * 簡介
 * ============================================================================
 * 
 * 這個插件允許 RPG Maker MV 遊戲與 AI-Agent 後台系統進行通信
 * 
 * ============================================================================
 * 插件命令
 * ============================================================================
 * 
 * sendToAI role message historyVarId responseVarId
 *   - role: AI 角色描述（用引號包圍，如 "一個友善的村民"）
 *   - message: 發送給 AI 的訊息（用引號包圍，如 "你好"）
 *   - historyVarId: 存儲歷史對話的變量ID（數字）
 *   - responseVarId: 存儲 AI 回應的變量ID（數字）
 * 
 * 使用範例:
 *   sendToAI "一個友善的村民" "你好！" 1 2
 *   sendToAI "商店老闆" "有什麼商品？" 1 2
 *   sendToAI "防詐騙助手" "這個看起來是詐騙嗎？" 3 4
 * 
 * ============================================================================
 * 變更日誌
 * ============================================================================
 * 
 * Version 1.0:
 * - 初始版本
 * - 支援 RPG Maker MV
 */

(function() {
    'use strict';

    // API 設定 - 使用 AI-Agent 系統的端口
    // 本地測試使用 localhost，遠程測試使用 Codespace URL
    const API_URL = window.API_BASE_URL 
        ? window.API_BASE_URL + '/chat'
        : 'https://crispy-space-goggles-r4rjqj6vpvr5fggq-8000.app.github.dev/chat';
    
    // 攔截插件命令
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'sendToAI') {
            // 解析參數
            let role = '';
            let message = '';
            let historyVarId = 1;
            let responseVarId = 2;
            
            // 處理帶引號的參數
            const fullArgs = args.join(' ');
            const matches = fullArgs.match(/"([^"]*)"/g);
            
            if (matches && matches.length >= 2) {
                role = matches[0].replace(/"/g, '');
                message = matches[1].replace(/"/g, '');
                
                // 取得剩餘的數字參數
                const afterQuotes = fullArgs.split(matches[1])[1].trim();
                const numbers = afterQuotes.match(/\d+/g);
                if (numbers) {
                    historyVarId = parseInt(numbers[0]) || 1;
                    responseVarId = parseInt(numbers[1]) || 2;
                }
            } else {
                // 沒有引號的簡單情況
                role = args[0] || '一個友善的村民';
                message = args[1] || '你好！';
                historyVarId = parseInt(args[2]) || 1;
                responseVarId = parseInt(args[3]) || 2;
            }
            
            // 發送請求到 AI API
            sendMessageToAI(role, message, historyVarId, responseVarId);
        }
    };
    
    // 發送訊息到 AI
    function sendMessageToAI(role, message, historyVarId, responseVarId) {
        // 獲取對話歷史
        let history = $gameVariables.value(historyVarId);
        if (!Array.isArray(history)) {
            history = [];
        }
        
        // 構建請求數據
        const requestData = {
            role: role,
            message: message,
            history: history
        };
        
        // 發送 HTTP 請求
        const xhr = new XMLHttpRequest();
        xhr.open('POST', API_URL, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const aiReply = response.reply || '抱歉，我無法回應。';
                    
                    // 存儲 AI 回應到變量
                    $gameVariables.setValue(responseVarId, aiReply);
                    
                    // 更新對話歷史
                    history.push({
                        role: 'user',
                        content: message
                    });
                    history.push({
                        role: 'assistant',
                        content: aiReply
                    });
                    $gameVariables.setValue(historyVarId, history);
                    
                    console.log('AI 回應:', aiReply);
                } catch (e) {
                    console.error('解析 AI 回應時發生錯誤:', e);
                    $gameVariables.setValue(responseVarId, '發生錯誤，請重試。');
                }
            } else {
                console.error('AI API 請求失敗:', xhr.status);
                $gameVariables.setValue(responseVarId, '無法連接到 AI 服務。');
            }
        };
        
        xhr.onerror = function() {
            console.error('AI API 連接錯誤');
            $gameVariables.setValue(responseVarId, '網路連接失敗。');
        };
        
        xhr.send(JSON.stringify(requestData));
    }
})();


