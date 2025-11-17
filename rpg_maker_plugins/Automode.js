/api/generate/*:
 * @target MV
 * @plugindesc 自動移動到 NPC 並啟動防詐騙遊戲插件
 * @author AI-Agent Team
 * @url https://github.com/yourusername/ai-agent
 * 
 * @help AutoMoveToNPC_MV.js
 * 
 * 這個插件允許玩家自動移動到指定的 NPC 並自動啟動防詐騙教育遊戲
 * 
 * 插件命令:
 * 
 * 1. moveToNPC eventId
 *    自動移動到指定事件ID的NPC
 * 
 * 2. moveToNPCAndStartGame eventId personaType
 *    自動移動到NPC並啟動防詐騙遊戲
 * 
 * 3. findAndMoveToNPC
 *    自動尋找並移動到最近的NPC（標記為防詐騙NPC）
 * 
 * 4. findAndStartGame
 *    自動尋找NPC並啟動遊戲
 * 
 * 事件備註標籤:
 * 在事件頁的備註欄中添加 <AntiFraudNPC> 標籤，插件會自動識別該NPC
 * 
 * @param moveSpeed
 * @text 移動速度
 * @desc 自動移動的速度（1-6，6為最快）
 * @type number
 * @min 1
 * @max 6
 * @default 4
 * 
 * @param searchRadius
 * @text 搜尋半徑
 * @desc 搜尋NPC的範圍（地圖格子數）
 * @type number
 * @min 1
 * @max 50
 * @default 20
 * 
 * @param autoStartGame
 * @text 自動啟動遊戲
 * @desc 移動到NPC後是否自動啟動遊戲
 * @type boolean
 * @default true
 * 
 * @param defaultPersonaType
 * @text 預設角色類型
 * @desc 預設的被騙人角色類型
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
 * @param sessionVarId
 * @text 會話ID變量
 * @desc 用於存儲會話ID的遊戲變量ID
 * @type variable
 * @default 10
 * 
 * @param dialogueVarId
 * @text 對話記錄變量
 * @desc 用於存儲對話記錄的遊戲變量ID
 * @type variable
 * @default 11
 * 
 * @param scoreVarId
 * @text 評分結果變量
 * @desc 用於存儲評分結果的遊戲變量ID
 * @type variable
 * @default 12
 * 
 * @param roundCount
 * @text 對話輪數
 * @desc 自動對話的輪數
 * @type number
 * @min 1
 * @max 20
 * @default 5
 * 
 * @command moveToNPC
 * @text 移動到NPC
 * @desc 自動移動到指定事件ID的NPC
 * 
 * @arg eventId
 * @text 事件ID
 * @desc 目標NPC的事件ID
 * @type number
 * @min 1
 * @default 1
 * 
 * @command moveToNPCAndStartGame
 * @text 移動到NPC並啟動遊戲
 * @desc 自動移動到NPC並啟動防詐騙遊戲
 * 
 * @arg eventId
 * @text 事件ID
 * @desc 目標NPC的事件ID
 * @type number
 * @min 1
 * @default 1
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
 * @command findAndMoveToNPC
 * @text 尋找並移動到NPC
 * @desc 自動尋找最近的防詐騙NPC並移動過去
 * 
 * @command findAndStartGame
 * @text 尋找NPC並啟動遊戲
 * @desc 自動尋找NPC並啟動防詐騙遊戲
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
 */

(function() {
    'use strict';

    const pluginName = 'AutoMoveToNPC_MV';
    const parameters = PluginManager.parameters(pluginName);
    
    // 參數設定
    const moveSpeed = Number(parameters['moveSpeed'] || 4);
    const searchRadius = Number(parameters['searchRadius'] || 20);
    const autoStartGame = parameters['autoStartGame'] === 'true';
    const defaultPersonaType = String(parameters['defaultPersonaType'] || 'A');
    const sessionVarId = Number(parameters['sessionVarId'] || 10);
    const dialogueVarId = Number(parameters['dialogueVarId'] || 11);
    const scoreVarId = Number(parameters['scoreVarId'] || 12);
    const roundCount = Number(parameters['roundCount'] || 5);
    
    // API 設定
    const API_BASE_URL = 'http://localhost:8000';
    
    // 移動狀態
    let isMoving = false;
    let targetEvent = null;
    let onArriveCallback = null;
    
    // ========== 插件命令註冊 ==========
    
    PluginManager.registerCommand(pluginName, 'moveToNPC', function(args) {
        const eventId = Number(args.eventId || 1);
        moveToEvent(eventId, null);
    });
    
    PluginManager.registerCommand(pluginName, 'moveToNPCAndStartGame', function(args) {
        const eventId = Number(args.eventId || 1);
        const personaType = String(args.personaType || defaultPersonaType);
        moveToEvent(eventId, function() {
            startAntiFraudGame(personaType);
        });
    });
    
    PluginManager.registerCommand(pluginName, 'findAndMoveToNPC', function(args) {
        const npcData = findNearestAntiFraudNPC();
        if (npcData) {
            moveToEvent(npcData.eventId, null);
        } else {
            $gameMessage.add('附近沒有找到防詐騙NPC！');
        }
    });
    
    PluginManager.registerCommand(pluginName, 'findAndStartGame', function(args) {
        const personaType = String(args.personaType || defaultPersonaType);
        const npcData = findNearestAntiFraudNPC();
        if (npcData) {
            moveToEvent(npcData.eventId, function() {
                startAntiFraudGame(personaType);
            });
        } else {
            $gameMessage.add('附近沒有找到防詐騙NPC！');
        }
    });
    
    // ========== 核心功能函數 ==========
    
    // 移動到指定事件
    function moveToEvent(eventId, callback) {
        const event = $gameMap.event(eventId);
        if (!event) {
            $gameMessage.add('找不到指定的事件！');
            return;
        }
        
        targetEvent = {
            event: event,
            eventId: eventId
        };
        onArriveCallback = callback;
        isMoving = true;
        
        // 設定移動速度
        $gamePlayer.setMoveSpeed(moveSpeed);
        
        // 開始移動
        startAutoMove();
    }
    
    // 開始自動移動
    function startAutoMove() {
        if (!isMoving || !targetEvent) {
            return;
        }
        
        const player = $gamePlayer;
        const target = targetEvent.event;
        
        // 檢查是否已到達（允許相鄰位置）
        const distance = Math.abs(player.x - target.x) + Math.abs(player.y - target.y);
        if (distance <= 1) {
            // 已到達目標
            isMoving = false;
            $gameMessage.add('已到達NPC！');
            
            // 面向NPC
            player.turnTowardCharacter(target);
            
            // 執行回調
            if (onArriveCallback) {
                onArriveCallback();
                onArriveCallback = null;
            }
            return;
        }
        
        // 使用 MV 的內建方法移動向目標
        // 計算最佳方向
        const dx = target.x - player.x;
        const dy = target.y - player.y;
        
        let direction = 0;
        
        // 優先移動主要方向
        if (Math.abs(dx) > Math.abs(dy)) {
            direction = dx > 0 ? 6 : 4; // 右或左
        } else {
            direction = dy > 0 ? 2 : 8; // 下或上
        }
        
        // 檢查是否可以移動
        if (direction > 0 && player.canPass(player.x, player.y, direction)) {
            player.moveStraight(direction);
        } else {
            // 嘗試替代方向
            const altDirections = [];
            if (dx !== 0) altDirections.push(dx > 0 ? 6 : 4);
            if (dy !== 0) altDirections.push(dy > 0 ? 2 : 8);
            
            let moved = false;
            for (let i = 0; i < altDirections.length; i++) {
                const dir = altDirections[i];
                if (player.canPass(player.x, player.y, dir)) {
                    player.moveStraight(dir);
                    moved = true;
                    break;
                }
            }
            
            // 如果都無法移動，嘗試繞路
            if (!moved) {
                const aroundDirs = [2, 4, 6, 8]; // 下、左、右、上
                for (let i = 0; i < aroundDirs.length; i++) {
                    const dir = aroundDirs[i];
                    if (player.canPass(player.x, player.y, dir)) {
                        player.moveStraight(dir);
                        break;
                    }
                }
            }
        }
    }
    
    // 尋找最近的防詐騙NPC
    function findNearestAntiFraudNPC() {
        const player = $gamePlayer;
        let nearestData = null;
        let minDistance = searchRadius + 1;
        
        // 遍歷所有事件
        for (let eventId = 1; eventId <= $dataMap.events.length; eventId++) {
            const event = $gameMap.event(eventId);
            if (!event) continue;
            
            // 檢查事件是否有 <AntiFraudNPC> 標籤
            const eventData = $dataMap.events[eventId];
            if (!eventData) continue;
            
            // 檢查當前活動的事件頁
            const pages = eventData.pages || [];
            let hasTag = false;
            
            for (let i = 0; i < pages.length; i++) {
                const page = pages[i];
                if (page && page.list) {
                    // 檢查條件和備註
                    const note = page.note || '';
                    if (note.indexOf('<AntiFraudNPC>') !== -1) {
                        hasTag = true;
                        break;
                    }
                }
            }
            
            if (!hasTag) continue;
            
            // 計算距離
            const dx = event.x - player.x;
            const dy = event.y - player.y;
            const distance = Math.abs(dx) + Math.abs(dy);
            
            if (distance < minDistance) {
                minDistance = distance;
                nearestData = {
                    event: event,
                    eventId: eventId
                };
            }
        }
        
        return nearestData;
    }
    
    // 啟動防詐騙遊戲
    function startAntiFraudGame(personaType) {
        $gameMessage.add('正在啟動防詐騙教育遊戲...');
        
        // 1. 開始遊戲
        startNewGame(personaType, function(sessionId) {
            if (sessionId) {
                $gameVariables.setValue(sessionVarId, sessionId);
                $gameMessage.add('遊戲已開始！');
                
                // 2. 開始自動對話
                setTimeout(function() {
                    startAutoDialogue(sessionId);
                }, 1000);
            }
        });
    }
    
    // 開始新遊戲
    function startNewGame(personaType, callback) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', API_BASE_URL + '/api/game/start', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const sessionId = response.session_id;
                    callback(sessionId);
                } catch (e) {
                    console.error('解析遊戲啟動回應時發生錯誤:', e);
                    $gameMessage.add('啟動遊戲失敗！');
                    callback(null);
                }
            } else {
                console.error('遊戲啟動失敗:', xhr.status);
                $gameMessage.add('無法連接到遊戲服務器！');
                callback(null);
            }
        };
        
        xhr.onerror = function() {
            console.error('遊戲啟動連接錯誤');
            $gameMessage.add('網路連接失敗！');
            callback(null);
        };
        
        xhr.send(JSON.stringify({ persona_type: personaType }));
    }
    
    // 開始自動對話
    function startAutoDialogue(sessionId) {
        $gameMessage.add('開始自動對話...');
        
        let dialogueLog = [];
        let currentRound = 0;
        
        function performRound() {
            if (currentRound >= roundCount) {
                // 對話完成
                $gameVariables.setValue(dialogueVarId, JSON.stringify(dialogueLog));
                $gameMessage.add('自動對話完成！');
                
                // 獲取評分
                setTimeout(function() {
                    getGameScore(sessionId);
                }, 1000);
                return;
            }
            
            currentRound++;
            
            // 獲取被騙人訊息
            const personaMessage = getPersonaMessage(currentRound);
            dialogueLog.push({ speaker: '被騙人', message: personaMessage });
            
            // 發送給騙子
            sendToScammer(sessionId, personaMessage, function(scammerReply) {
                dialogueLog.push({ speaker: '騙子', message: scammerReply });
                
                // 獲取助手建議
                getAssistantAdvice(sessionId, personaMessage, scammerReply, function(assistantAdvice) {
                    dialogueLog.push({ speaker: '助手', message: assistantAdvice });
                    
                    // 顯示對話
                    $gameMessage.add('被騙人：' + personaMessage);
                    $gameMessage.add('騙子：' + scammerReply);
                    $gameMessage.add('助手：' + assistantAdvice);
                    
                    // 繼續下一輪
                    setTimeout(function() {
                        performRound();
                    }, 2000);
                });
            });
        }
        
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
        xhr.open('POST', API_BASE_URL + '/api/game/message', true);
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
        xhr.open('POST', API_BASE_URL + '/chat', true);
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
            message: '被騙人說：「' + personaMessage + '」，詐騙者回應：「' + scammerReply + '」',
            history: []
        }));
    }
    
    // 獲取評分
    function getGameScore(sessionId) {
        $gameMessage.add('正在分析對話並評分...');
        
        const xhr = new XMLHttpRequest();
        xhr.open('GET', API_BASE_URL + '/api/game/session/' + sessionId, true);
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const conversations = response.conversations || [];
                    
                    // 請求評分
                    const dialogueText = conversations.map(function(c) {
                        return c.role + ': ' + c.message;
                    }).join('\n');
                    
                    const scoreXhr = new XMLHttpRequest();
                    scoreXhr.open('POST', API_BASE_URL + '/chat', true);
                    scoreXhr.setRequestHeader('Content-Type', 'application/json');
                    
                    scoreXhr.onload = function() {
                        if (scoreXhr.status === 200) {
                            const scoreResponse = JSON.parse(scoreXhr.responseText);
                            $gameVariables.setValue(scoreVarId, scoreResponse.reply);
                            $gameMessage.add('評分完成！');
                            $gameMessage.add(scoreResponse.reply);
                            
                            // 結束遊戲
                            endCurrentGame(sessionId);
                        }
                    };
                    
                    scoreXhr.send(JSON.stringify({
                        role: '評分AI，分析防詐騙表現並給出評分和建議',
                        message: '請分析以下對話，評估被騙人的防詐騙表現：\n\n' + dialogueText,
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
    function endCurrentGame(sessionId) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', API_BASE_URL + '/api/game/end?session_id=' + sessionId, true);
        xhr.send();
        
        $gameVariables.setValue(sessionVarId, 0);
        $gameMessage.add('遊戲已結束');
    }
    
    // ========== 覆蓋 Game_Player 方法以支援自動移動 ==========
    
    const _Game_Player_update = Game_Player.prototype.update;
    Game_Player.prototype.update = function(sceneActive) {
        _Game_Player_update.call(this, sceneActive);
        
        // 如果正在自動移動且玩家沒有在移動中，繼續移動
        if (isMoving && sceneActive && !this.isMoving()) {
            startAutoMove();
        }
    };
    
    // 覆蓋 Scene_Map 的 update 方法以確保移動持續
    const _Scene_Map_update = Scene_Map.prototype.update;
    Scene_Map.prototype.update = function() {
        _Scene_Map_update.call(this);
        
        // 確保自動移動持續進行
        if (isMoving && $gamePlayer.isMoving() === false) {
            // 玩家停止移動時，繼續嘗試移動
            if (targetEvent && targetEvent.event) {
                startAutoMove();
            }
        }
    };
    
})();

