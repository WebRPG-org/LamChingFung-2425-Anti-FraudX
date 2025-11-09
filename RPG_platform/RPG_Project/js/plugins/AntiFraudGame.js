/*:
 * @plugindesc 防詐騙教育遊戲插件 - 整合 AI-Agent 系統 v2.5 (RPG Maker MV)
 * @author AI-Agent Team
 * @help 
 * ============================================================================
 * 簡介
 * ============================================================================
 * 
 * 這個插件提供完整的防詐騙教育遊戲功能，整合 AI-Agent v2.5 後台系統
 * 包含：詐騙者 Agent、受害者 Agent、專家 Agent、記錄者 Agent
 * 支援 RPG Maker MV
 * 
 * ============================================================================
 * 插件命令
 * ============================================================================
 * 
 * 1. startSimulation victimPersona scamTactic mode simulationIdVar
 *    開始 AI 模擬對話（詐騙者 vs 受害者 + 專家）
 *    victimPersona: elderly (長者), average (一般市民), overconfident (過度自信者)
 *    scamTactic: 詐騙手法（如 "WhatsApp 對話詐騙"）
 *    mode: fast (快速) 或 demo (演示)
 *    simulationIdVar: 存儲模擬ID的變量ID (預設: 20)
 *    範例: startSimulation elderly "WhatsApp 對話詐騙" fast 20
 * 
 * 2. getSimulationDialogue simulationIdVar dialogueVar
 *    獲取模擬對話記錄（即時更新）
 *    simulationIdVar: 模擬ID變量ID
 *    dialogueVar: 對話記錄變量ID (預設: 21)
 *    範例: getSimulationDialogue 20 21
 * 
 * 3. stopSimulation simulationIdVar
 *    停止當前模擬
 *    simulationIdVar: 模擬ID變量ID
 *    範例: stopSimulation 20
 * 
 * 4. getSimulationResult simulationIdVar resultVar
 *    獲取模擬結果和分析
 *    simulationIdVar: 模擬ID變量ID
 *    resultVar: 結果變量ID (預設: 22)
 *    範例: getSimulationResult 20 22
 * 
 * 5. sendToAI role message historyVar responseVar
 *    向 AI 發送訊息（通用聊天）
 *    role: AI 角色描述
 *    message: 訊息內容
 *    historyVar: 歷史變量ID (預設: 30)
 *    responseVar: 回應變量ID (預設: 31)
 *    範例: sendToAI "防詐騙助手" "這個是詐騙嗎？" 30 31
 * 
 * ============================================================================
 * 變更日誌
 * ============================================================================
 * 
 * Version 2.5:
 * - 整合完整 AI-Agent 系統
 * - 支援 WebSocket 即時模擬
 * - 支援多 Agent 互動（詐騙者、受害者、專家、記錄者）
 * - 支援自動訓練和進化系統
 * 
 * Version 1.0:
 * - 初始版本
 */

(function() {
    'use strict';

    // API 設定 - 使用 AI-Agent v2.5 系統
    const API_BASE_URL = window.API_BASE_URL 
        || 'https://crispy-space-goggles-r4rjqj6vpvr5fggq-8000.app.github.dev';
    
    // WebSocket 連接管理
    let activeWebSocket = null;
    let currentSimulationId = null;
    let simulationDialogue = [];
    let simulationResult = null;
    
    // 攔截插件命令
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        // === 新版 AI-Agent 系統命令 ===
        if (command === 'startSimulation') {
            // 解析參數：victimPersona scamTactic mode simulationIdVar
            const fullArgs = args.join(' ');
            const parts = fullArgs.split('"');
            
            const victimPersona = args[0] || 'elderly';
            const scamTactic = parts[1] || 'WhatsApp 對話詐騙';
            const mode = parts.length > 2 ? parts[2].trim().split(' ')[0] : 'fast';
            const simulationIdVar = Number(args[args.length - 1]) || 20;
            
            startAISimulation(victimPersona, scamTactic, mode, simulationIdVar);
        }
        else if (command === 'getSimulationDialogue') {
            const simulationIdVar = Number(args[0]) || 20;
            const dialogueVar = Number(args[1]) || 21;
            getSimulationDialogue(simulationIdVar, dialogueVar);
        }
        else if (command === 'stopSimulation') {
            const simulationIdVar = Number(args[0]) || 20;
            stopAISimulation(simulationIdVar);
        }
        else if (command === 'getSimulationResult') {
            const simulationIdVar = Number(args[0]) || 20;
            const resultVar = Number(args[1]) || 22;
            getSimulationResult(simulationIdVar, resultVar);
        }
        else if (command === 'sendToAI') {
            // 解析參數：role message historyVar responseVar
            const fullArgs = args.join(' ');
            const matches = fullArgs.match(/"([^"]*)"/g);
            
            let role = '防詐騙助手';
            let message = '你好';
            let historyVar = 30;
            let responseVar = 31;
            
            if (matches && matches.length >= 2) {
                role = matches[0].replace(/"/g, '');
                message = matches[1].replace(/"/g, '');
                const afterQuotes = fullArgs.split(matches[1])[1].trim();
                const numbers = afterQuotes.match(/\d+/g);
                if (numbers) {
                    historyVar = parseInt(numbers[0]) || 30;
                    responseVar = parseInt(numbers[1]) || 31;
                }
            }
            
            sendMessageToAI(role, message, historyVar, responseVar);
        }
        
        // === 舊版命令（向後兼容）===
        else if (command === 'startGame') {
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
    
    // ========== 新版 AI-Agent v2.5 系統函數 ==========
    
    /**
     * 開始 AI 模擬（詐騙者 vs 受害者 + 專家）
     * @param {string} victimPersona - elderly, average, overconfident
     * @param {string} scamTactic - 詐騙手法
     * @param {string} mode - fast 或 demo
     * @param {number} simulationIdVar - 存儲模擬ID的變量
     */
    function startAISimulation(victimPersona, scamTactic, mode, simulationIdVar) {
        console.log(`[AI模擬] 開始 - 受害者: ${victimPersona}, 手法: ${scamTactic}, 模式: ${mode}`);
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/simulation/start`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    currentSimulationId = response.simulation_id;
                    
                    // 存儲模擬ID
                    $gameVariables.setValue(simulationIdVar, currentSimulationId);
                    
                    console.log('[AI模擬] 模擬ID:', currentSimulationId);
                    $gameMessage.add('AI 模擬已開始！');
                    
                    // 建立 WebSocket 連接
                    connectToSimulationWebSocket(currentSimulationId);
                    
                } catch (e) {
                    console.error('[AI模擬] 解析回應錯誤:', e);
                    $gameMessage.add('啟動模擬失敗！');
                }
            } else {
                console.error('[AI模擬] 啟動失敗:', xhr.status);
                $gameMessage.add('啟動模擬失敗！');
            }
        };
        
        xhr.onerror = function() {
            console.error('[AI模擬] 網絡錯誤');
            $gameMessage.add('網絡連接失敗！');
        };
        
        xhr.send(JSON.stringify({
            victim_persona: victimPersona,
            scam_tactic: scamTactic,
            mode: mode,
            auto_train: true
        }));
    }
    
    /**
     * 連接 WebSocket 接收即時對話
     */
    function connectToSimulationWebSocket(simulationId) {
        // 關閉舊連接
        if (activeWebSocket) {
            activeWebSocket.close();
        }
        
        // 清空對話記錄
        simulationDialogue = [];
        simulationResult = null;
        
        // 建立新連接
        const wsUrl = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');
        const ws = new WebSocket(`${wsUrl}/ws/simulation/${simulationId}`);
        
        ws.onopen = function() {
            console.log('[WebSocket] 已連接到模擬:', simulationId);
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleSimulationEvent(data);
            } catch (e) {
                console.error('[WebSocket] 解析訊息錯誤:', e);
            }
        };
        
        ws.onerror = function(error) {
            console.error('[WebSocket] 錯誤:', error);
        };
        
        ws.onclose = function() {
            console.log('[WebSocket] 連接已關閉');
            activeWebSocket = null;
        };
        
        activeWebSocket = ws;
    }
    
    /**
     * 處理 WebSocket 事件
     */
    function handleSimulationEvent(data) {
        const eventType = data.event;
        
        switch(eventType) {
            case 'dialogue':
                // 新對話
                const speaker = data.data.speaker;
                const message = data.data.message;
                const role = data.data.role || speaker;
                
                simulationDialogue.push({
                    speaker: speaker,
                    role: role,
                    message: message,
                    timestamp: new Date().toISOString()
                });
                
                console.log(`[${role}] ${speaker}: ${message}`);
                break;
                
            case 'status':
                // 狀態更新
                console.log('[狀態]', data.data.message);
                break;
                
            case 'completed':
                // 模擬完成
                console.log('[模擬完成]', data.data);
                simulationResult = data.data;
                $gameMessage.add('AI 模擬已完成！');
                $gameMessage.add('10秒後自動關閉連接...');
                
                // 10秒後關閉 WebSocket
                setTimeout(function() {
                    if (activeWebSocket) {
                        console.log('[WebSocket] 10秒後自動關閉連接');
                        activeWebSocket.close();
                    }
                }, 10000); // 10秒 = 10000毫秒
                break;
                
            case 'error':
                // 錯誤
                console.error('[模擬錯誤]', data.data.message);
                $gameMessage.add('模擬發生錯誤：' + data.data.message);
                break;
        }
    }
    
    /**
     * 獲取模擬對話記錄
     */
    function getSimulationDialogue(simulationIdVar, dialogueVar) {
        const simulationId = $gameVariables.value(simulationIdVar);
        
        if (!simulationId) {
            console.error('[獲取對話] 沒有活動的模擬');
            $gameVariables.setValue(dialogueVar, []);
            return;
        }
        
        // 將對話記錄存入變量
        $gameVariables.setValue(dialogueVar, simulationDialogue);
        console.log('[獲取對話] 共', simulationDialogue.length, '條對話');
    }
    
    /**
     * 停止模擬
     */
    function stopAISimulation(simulationIdVar) {
        const simulationId = $gameVariables.value(simulationIdVar);
        
        if (!simulationId) {
            console.error('[停止模擬] 沒有活動的模擬');
            return;
        }
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/simulation/stop/${simulationId}`, true);
        
        xhr.onload = function() {
            console.log('[停止模擬] 已停止');
            $gameMessage.add('模擬已停止');
            
            if (activeWebSocket) {
                activeWebSocket.close();
            }
        };
        
        xhr.send();
    }
    
    /**
     * 獲取模擬結果
     */
    function getSimulationResult(simulationIdVar, resultVar) {
        const simulationId = $gameVariables.value(simulationIdVar);
        
        if (!simulationId) {
            console.error('[獲取結果] 沒有活動的模擬');
            $gameVariables.setValue(resultVar, null);
            return;
        }
        
        if (simulationResult) {
            // 如果已經有結果（從 WebSocket 接收）
            $gameVariables.setValue(resultVar, simulationResult);
            console.log('[獲取結果] 結果:', simulationResult);
        } else {
            // 從 API 獲取
            const xhr = new XMLHttpRequest();
            xhr.open('GET', `${API_BASE_URL}/simulation/result/${simulationId}`, true);
            
            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        simulationResult = response;
                        $gameVariables.setValue(resultVar, response);
                        console.log('[獲取結果] 結果:', response);
                    } catch (e) {
                        console.error('[獲取結果] 解析錯誤:', e);
                    }
                }
            };
            
            xhr.send();
        }
    }
    
    /**
     * 發送訊息到 AI（通用聊天）
     */
    function sendMessageToAI(role, message, historyVar, responseVar) {
        let history = $gameVariables.value(historyVar);
        if (!Array.isArray(history)) {
            history = [];
        }
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE_URL}/chat`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const reply = response.reply;
                    
                    // 更新歷史
                    history.push({ role: 'user', content: message });
                    history.push({ role: 'assistant', content: reply });
                    $gameVariables.setValue(historyVar, history);
                    
                    // 存儲回應
                    $gameVariables.setValue(responseVar, reply);
                    
                    console.log('[AI回應]', reply);
                    
                } catch (e) {
                    console.error('[AI聊天] 解析錯誤:', e);
                }
            }
        };
        
        xhr.send(JSON.stringify({
            role: role,
            message: message,
            history: history
        }));
    }
    
    // ========== 舊版函數（向後兼容）==========
    
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


