/*:
 * @target MZ
 * @plugindesc 防詐騙教育遊戲插件 - 整合 AI-Agent 系統
 * @author AI-Agent Team
 * @url https://github.com/yourusername/ai-agent
 * 
 * @help AntiFraudGame.js
 * 
 * 這個插件提供完整的防詐騙教育遊戲功能，整合 AI-Agent 後台系統
 * 
 * 插件命令:
 * 
 * 1. startGame personaType
 *    開始新遊戲
 * 
 * 2. startAutoDialogue
 *    開始自動對話（被騙人 vs 騙子 + 助手）
 * 
 * 3. getScore
 *    獲取評分分析
 * 
 * 4. endGame
 *    結束遊戲
 * 
 * @command startGame
 * @text 開始遊戲
 * @desc 開始新的防詐騙教育遊戲
 * 
 * @arg personaType
 * @text 角色類型
 * @desc 選擇被騙人角色類型
 * @type select
 * @option Persona A - 長者（高風險）
 * @value A
 * @option Persona B - 一般市民
 * @value B
 * @option Persona C - 過度自信者
 * @value C
 * @option Persona D - 自訂角色
 * @value D
 * @default A
 * 
 * @arg sessionVarId
 * @text 會話ID變量
 * @desc 用於存儲會話ID的遊戲變量ID
 * @type variable
 * @default 10
 * 
 * @command startAutoDialogue
 * @text 開始自動對話
 * @desc 開始被騙人、騙子、助手的自動對話
 * 
 * @arg sessionVarId
 * @text 會話ID變量
 * @desc 存儲會話ID的遊戲變量ID
 * @type variable
 * @default 10
 * 
 * @arg dialogueVarId
 * @text 對話記錄變量
 * @desc 用於存儲對話記錄的遊戲變量ID
 * @type variable
 * @default 11
 * 
 * @arg roundCount
 * @text 對話輪數
 * @desc 自動對話的輪數
 * @type number
 * @default 5
 * 
 * @command getScore
 * @text 獲取評分
 * @desc 讓評分AI分析對話並給出評分
 * 
 * @arg sessionVarId
 * @text 會話ID變量
 * @desc 存儲會話ID的遊戲變量ID
 * @type variable
 * @default 10
 * 
 * @arg scoreVarId
 * @text 評分結果變量
 * @desc 用於存儲評分結果的遊戲變量ID
 * @type variable
 * @default 12
 * 
 * @command endGame
 * @text 結束遊戲
 * @desc 結束當前遊戲會話
 * 
 * @arg sessionVarId
 * @text 會話ID變量
 * @desc 存儲會話ID的遊戲變量ID
 * @type variable
 * @default 10
 */

(() => {
    'use strict';

    const pluginName = 'AntiFraudGame';
    
    // API 設定 - 使用 AI-Agent 系統的端口
    const API_BASE_URL = 'http://localhost:8000';
    
    // 註冊插件命令
    
    // 1. 開始遊戲
    PluginManager.registerCommand(pluginName, 'startGame', args => {
        const personaType = String(args.personaType || 'A');
        const sessionVarId = Number(args.sessionVarId || 10);
        
        startNewGame(personaType, sessionVarId);
    });
    
    // 2. 開始自動對話
    PluginManager.registerCommand(pluginName, 'startAutoDialogue', args => {
        const sessionVarId = Number(args.sessionVarId || 10);
        const dialogueVarId = Number(args.dialogueVarId || 11);
        const roundCount = Number(args.roundCount || 5);
        
        startAutoDialogue(sessionVarId, dialogueVarId, roundCount);
    });
    
    // 3. 獲取評分
    PluginManager.registerCommand(pluginName, 'getScore', args => {
        const sessionVarId = Number(args.sessionVarId || 10);
        const scoreVarId = Number(args.scoreVarId || 12);
        
        getGameScore(sessionVarId, scoreVarId);
    });
    
    // 4. 結束遊戲
    PluginManager.registerCommand(pluginName, 'endGame', args => {
        const sessionVarId = Number(args.sessionVarId || 10);
        
        endCurrentGame(sessionVarId);
    });
    
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


