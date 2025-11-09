/*:
 * @plugindesc 防詐騙教育遊戲插件 - 整合 AI-Agent 系統 (RPG Maker MV)
 * @author AI-Agent Team
 * @help 
 * ============================================================================
 * 簡介
 * ============================================================================
 * 
 * 這個插件提供完整的防詐騙教育遊戲功能，整合 AI-Agent 後台系統
 * 支援 RPG Maker MV
 * 
 * ============================================================================
 * 插件命令
 * ============================================================================
 * 
 * 1. startGame personaType sessionVarId
 *    開始新遊戲
 *    personaType: A (長者), B (一般市民), C (過度自信者), D (自訂)
 *    sessionVarId: 存儲會話ID的變量ID (預設: 10)
 *    範例: startGame A 10
 * 
 * 2. startAutoDialogue sessionVarId dialogueVarId roundCount
 *    開始自動對話（被騙人 vs 騙子 + 助手）
 *    sessionVarId: 會話ID變量ID (預設: 10)
 *    dialogueVarId: 對話記錄變量ID (預設: 11)
 *    roundCount: 對話輪數 (預設: 5)
 *    範例: startAutoDialogue 10 11 5
 * 
 * 3. getScore sessionVarId scoreVarId
 *    獲取評分分析
 *    sessionVarId: 會話ID變量ID (預設: 10)
 *    scoreVarId: 評分結果變量ID (預設: 12)
 *    範例: getScore 10 12
 * 
 * 4. endGame sessionVarId
 *    結束遊戲
 *    sessionVarId: 會話ID變量ID (預設: 10)
 *    範例: endGame 10
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
    const API_BASE_URL = 'http://localhost:8000';
    
    // 攔截插件命令
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'startGame') {
            const personaType = String(args[0] || 'A');
            const sessionVarId = Number(args[1]) || 10;
            startNewGame(personaType, sessionVarId);
        }
        else if (command === 'startAutoDialogue') {
            const sessionVarId = Number(args[0]) || 10;
            const dialogueVarId = Number(args[1]) || 11;
            const roundCount = Number(args[2]) || 5;
            startAutoDialogue(sessionVarId, dialogueVarId, roundCount);
        }
        else if (command === 'getScore') {
            const sessionVarId = Number(args[0]) || 10;
            const scoreVarId = Number(args[1]) || 12;
            getGameScore(sessionVarId, scoreVarId);
        }
        else if (command === 'endGame') {
            const sessionVarId = Number(args[0]) || 10;
            endCurrentGame(sessionVarId);
        }
    };
    
    // ========== 函數實現 ==========
    
    // 開始新遊戲
    function startNewGame(personaType, sessionVarId) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/api/game/start`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const sessionId = response.session_id;
                    
                    // 存儲會話ID
                    $gameVariables.setValue(sessionVarId, sessionId);
                    
                    console.log('遊戲開始！會話ID:', sessionId);
                    console.log('角色:', response.persona.name);
                    
                    // 顯示訊息
                    $gameMessage.add('遊戲開始！');
                    $gameMessage.add('角色：' + response.persona.name);
                    
                } catch (e) {
                    console.error('解析遊戲啟動回應時發生錯誤:', e);
                }
            } else {
                console.error('遊戲啟動失敗:', xhr.status);
            }
        };
        
        xhr.send(JSON.stringify({ persona_type: personaType }));
    }
    
    // 開始自動對話
    function startAutoDialogue(sessionVarId, dialogueVarId, roundCount) {
        const sessionId = $gameVariables.value(sessionVarId);
        
        if (!sessionId) {
            console.error('請先開始遊戲！');
            $gameMessage.add('請先開始遊戲！');
            return;
        }
        
        let dialogueLog = [];
        let currentRound = 0;
        
        // 執行自動對話
        function performRound() {
            if (currentRound >= roundCount) {
                // 對話完成
                $gameVariables.setValue(dialogueVarId, dialogueLog);
                $gameMessage.add('自動對話完成！');
                console.log('對話記錄:', dialogueLog);
                return;
            }
            
            currentRound++;
            
            // 獲取被騙人訊息
            const personaMessage = getPersonaMessage(currentRound);
            dialogueLog.push({ speaker: '被騙人', message: personaMessage });
            
            // 發送給騙子
            sendToScammer(sessionId, personaMessage, (scammerReply) => {
                dialogueLog.push({ speaker: '騙子', message: scammerReply });
                
                // 獲取助手建議
                getAssistantAdvice(sessionId, personaMessage, scammerReply, (assistantAdvice) => {
                    dialogueLog.push({ speaker: '助手', message: assistantAdvice });
                    
                    // 顯示對話
                    $gameMessage.add('被騙人：' + personaMessage);
                    $gameMessage.add('騙子：' + scammerReply);
                    $gameMessage.add('助手：' + assistantAdvice);
                    
                    // 繼續下一輪
                    setTimeout(() => performRound(), 1000);
                });
            });
        }
        
        // 開始第一輪
        performRound();
    }
    
    // 獲取被騙人訊息
    function getPersonaMessage(round) {
        const messages = [
            '你好，我是村裡的長者',
            '有什麼需要幫助的嗎？',
            '我對這些不太了解',
            '真的嗎？聽起來很吸引人',
            '我需要考慮一下',
            '這個投資安全嗎？',
            '我沒有太多錢',
            '你能保證收益嗎？',
            '我需要和家人商量',
            '這個機會很難得嗎？'
        ];
        return messages[(round - 1) % messages.length];
    }
    
    // 發送給騙子
    function sendToScammer(sessionId, message, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/api/game/message`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    callback(response.reply);
                } catch (e) {
                    console.error('解析騙子回應時發生錯誤:', e);
                    callback('無法獲取回應');
                }
            }
        };
        
        xhr.send(JSON.stringify({
            session_id: sessionId,
            message: message,
            target_ai: 'AI-D',
            persona_type: 'A'
        }));
    }
    
    // 獲取助手建議
    function getAssistantAdvice(sessionId, personaMessage, scammerReply, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/chat`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    callback(response.reply);
                } catch (e) {
                    console.error('解析助手回應時發生錯誤:', e);
                    callback('無法獲取建議');
                }
            }
        };
        
        xhr.send(JSON.stringify({
            role: '防騙助手，提供防詐騙建議',
            message: `被騙人說：「${personaMessage}」，詐騙者回應：「${scammerReply}」`,
            history: []
        }));
    }
    
    // 獲取評分
    function getGameScore(sessionVarId, scoreVarId) {
        const sessionId = $gameVariables.value(sessionVarId);
        
        if (!sessionId) {
            console.error('請先開始遊戲！');
            $gameMessage.add('請先開始遊戲！');
            return;
        }
        
        $gameMessage.add('正在分析對話並評分...');
        
        // 調用評分 API
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `${API_BASE_URL}/api/game/session/${sessionId}`, true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const conversations = response.conversations || [];
                    
                    // 請求評分
                    const dialogueText = conversations.map(c => 
                        `${c.role}: ${c.message}`
                    ).join('\n');
                    
                    const scoreXhr = new XMLHttpRequest();
                    scoreXhr.open('POST', `${API_BASE_URL}/chat`, true);
                    scoreXhr.setRequestHeader('Content-Type', 'application/json');
                    
                    scoreXhr.onload = function() {
                        if (scoreXhr.status === 200) {
                            const scoreResponse = JSON.parse(scoreXhr.responseText);
                            $gameVariables.setValue(scoreVarId, scoreResponse.reply);
                            $gameMessage.add('評分完成！');
                            $gameMessage.add(scoreResponse.reply);
                        }
                    };
                    
                    scoreXhr.send(JSON.stringify({
                        role: '評分AI，分析防詐騙表現並給出評分和建議',
                        message: `請分析以下對話，評估被騙人的防詐騙表現：\n\n${dialogueText}`,
                        history: []
                    }));
                    
                } catch (e) {
                    console.error('評分錯誤:', e);
                }
            }
        };
        
        xhr.send();
    }
    
    // 結束遊戲
    function endCurrentGame(sessionVarId) {
        const sessionId = $gameVariables.value(sessionVarId);
        
        if (sessionId) {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE_URL}/api/game/end?session_id=${sessionId}`, true);
            xhr.send();
            
            $gameVariables.setValue(sessionVarId, null);
            $gameMessage.add('遊戲已結束');
        }
    }
    
})();


