/*:
 * @target MZ
 * @plugindesc AI Bridge Plugin - 連接 RPG Maker 與 AI-Agent 系統
 * @author AI-Agent Team
 * @url https://github.com/yourusername/ai-agent
 * 
 * @help AI_Bridge.js
 * 
 * 這個插件允許 RPG Maker MZ 遊戲與 AI-Agent 後台系統進行通信
 * 
 * 插件命令:
 *   sendToAI role message historyVar responseVar
 *     - role: AI 角色描述
 *     - message: 發送給 AI 的訊息
 *     - historyVar: 存儲歷史對話的變量ID
 *     - responseVar: 存儲 AI 回應的變量ID
 * 
 * 使用範例:
 *   插件命令: sendToAI "一個友善的村民" "你好！" 1 2
 *   這會將訊息發送給 AI，並將回應存儲在變量2中
 * 
 * @command sendToAI
 * @text 發送訊息給 AI
 * @desc 發送訊息給 AI-Agent 系統並獲取回應
 * 
 * @arg role
 * @text AI 角色
 * @desc AI 扮演的角色描述
 * @type string
 * @default 一個友善的村民
 * 
 * @arg message
 * @text 訊息內容
 * @desc 發送給 AI 的訊息
 * @type string
 * @default 你好！
 * 
 * @arg historyVarId
 * @text 歷史記錄變量ID
 * @desc 用於存儲對話歷史的遊戲變量ID
 * @type variable
 * @default 1
 * 
 * @arg responseVarId
 * @text 回應變量ID
 * @desc 用於存儲AI回應的遊戲變量ID
 * @type variable
 * @default 2
 */

(() => {
    'use strict';

    const pluginName = 'AI_Bridge';
    
    // API 設定 - 使用 AI-Agent 系統的端口
    const API_URL = 'http://localhost:8000/chat';
    
    // 註冊插件命令
    PluginManager.registerCommand(pluginName, 'sendToAI', args => {
        const role = String(args.role || '一個友善的村民');
        const message = String(args.message || '你好！');
        const historyVarId = Number(args.historyVarId || 1);
        const responseVarId = Number(args.responseVarId || 2);
        
        // 發送請求到 AI API
        sendMessageToAI(role, message, historyVarId, responseVarId);
    });
    
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


