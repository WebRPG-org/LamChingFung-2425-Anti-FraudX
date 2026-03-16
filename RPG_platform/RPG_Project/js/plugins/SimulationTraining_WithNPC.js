/*:
 * @target MZ MV
 * @plugindesc 防詐騙模擬訓練系統（帶NPC自動移動）- 基於 simulation_routes.py
 * @author AI-Agent Team
 * 
 * @help SimulationTraining_WithNPC.js
 * 
 * 此插件結合了完整的 simulation_routes.py 流程和 NPC 自動移動功能
 * 
 * 插件命令：
 * 
 * 1. StartAutoTrainingWithNPC rounds mode
 *    啟動自動訓練（會自動移動到各個訓練NPC）
 * 
 * 2. StopAutoTraining
 *    停止自動訓練
 * 
 * 3. SetupTrainingNPC eventId persona tactic
 *    設置訓練NPC的參數
 * 
 * NPC 設置：
 * - 在地圖上放置多個事件（NPC）
 * - 在事件備註中添加 <TrainingNPC> 標籤
 * - 使用 SetupTrainingNPC 命令配置每個NPC
 * 
 * @param apiBaseUrl
 * @text API Base URL
 * @default http://localhost:8000
 * 
 * @param wsBaseUrl
 * @text WebSocket Base URL
 * @default ws://localhost:8000
 * 
 * @param moveSpeed
 * @text 移動速度
 * @type number
 * @min 1
 * @max 6
 * @default 4
 * 
 * @param showSimulationDetails
 * @text 顯示模擬詳情
 * @type boolean
 * @default false
 * 
 * @param simulationVarId
 * @text 模擬ID變量
 * @type variable
 * @default 20
 * 
 * @param trustScammerVarId
 * @text 對騙徒信任度變量
 * @type variable
 * @default 21
 * 
 * @param trustExpertVarId
 * @text 對專家信任度變量
 * @type variable
 * @default 22
 * 
 * @param outcomeVarId
 * @text 結果變量
 * @type variable
 * @default 23
 * 
 * @param completedRoundsVarId
 * @text 已完成輪數變量
 * @type variable
 * @default 24
 */

(function() {
    'use strict';

    const pluginName = 'SimulationTraining_WithNPC';
    const parameters = PluginManager.parameters(pluginName);
    
    // 參數
    const API_BASE_URL = String(parameters['apiBaseUrl'] || 'http://localhost:8000');
    const WS_BASE_URL = String(parameters['wsBaseUrl'] || 'ws://localhost:8000');
    const MOVE_SPEED = Number(parameters['moveSpeed'] || 4);
    const SHOW_DETAILS = parameters['showSimulationDetails'] === 'true';
    
    const SIM_VAR_ID = Number(parameters['simulationVarId'] || 20);
    const TRUST_SCAMMER_VAR_ID = Number(parameters['trustScammerVarId'] || 21);
    const TRUST_EXPERT_VAR_ID = Number(parameters['trustExpertVarId'] || 22);
    const OUTCOME_VAR_ID = Number(parameters['outcomeVarId'] || 23);
    const COMPLETED_ROUNDS_VAR_ID = Number(parameters['completedRoundsVarId'] || 24);
    
    // 全局狀態
    let autoTrainingActive = false;
    let currentNPCIndex = 0;
    let trainingNPCs = [];
    let currentSimulation = null;
    let currentWebSocket = null;
    let isMovingToNPC = false;
    let isInSimulation = false;
    let totalRounds = 0;
    let completedRounds = 0;
    let currentMode = 'fast';
    
    // NPC 配置存儲
    const npcConfigs = {};
    
    // ==================== 插件命令註冊 ====================
    
    if (typeof PluginManager !== 'undefined' && PluginManager.registerCommand) {
        // MZ 格式
        PluginManager.registerCommand(pluginName, 'StartAutoTrainingWithNPC', function(args) {
            const rounds = Number(args.rounds || 0);
            const mode = String(args.mode || 'fast');
            startAutoTrainingWithNPC(rounds, mode);
        });
        
        PluginManager.registerCommand(pluginName, 'StopAutoTraining', function(args) {
            stopAutoTraining();
        });
        
        PluginManager.registerCommand(pluginName, 'SetupTrainingNPC', function(args) {
            const eventId = Number(args.eventId);
            const persona = String(args.persona || 'average');
            const tactic = String(args.tactic || '冒充銀行客服詐騙');
            setupTrainingNPC(eventId, persona, tactic);
        });
    }
    
    // MV 兼容
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'StartAutoTrainingWithNPC') {
            const rounds = Number(args[0] || 0);
            const mode = args[1] || 'fast';
            startAutoTrainingWithNPC(rounds, mode);
        } else if (command === 'StopAutoTraining') {
            stopAutoTraining();
        } else if (command === 'SetupTrainingNPC') {
            const eventId = Number(args[0]);
            const persona = args[1] || 'average';
            const tactic = args.slice(2).join(' ') || '冒充銀行客服詐騙';
            setupTrainingNPC(eventId, persona, tactic);
        }
    };
    
    // ==================== NPC 管理 ====================
    
    function setupTrainingNPC(eventId, persona, tactic) {
        npcConfigs[eventId] = {
            eventId: eventId,
            persona: persona,
            tactic: tactic
        };
        console.log(`[訓練NPC] 已設置 Event ${eventId}: persona=${persona}, tactic=${tactic}`);
    }
    
    function findAllTrainingNPCs() {
        const npcs = [];
        const map = $dataMap;
        
        if (!map || !map.events) return npcs;
        
        for (let i = 1; i < map.events.length; i++) {
            const eventData = map.events[i];
            if (!eventData) continue;
            
            // 檢查備註中是否有 <TrainingNPC> 標籤
            const note = eventData.note || '';
            if (note.includes('<TrainingNPC>')) {
                const event = $gameMap.event(i);
                if (event) {
                    npcs.push({
                        eventId: i,
                        event: event,
                        x: event.x,
                        y: event.y,
                        config: npcConfigs[i] || {
                            persona: 'average',
                            tactic: '冒充銀行客服詐騙'
                        }
                    });
                }
            }
        }
        
        return npcs;
    }
    
    // ==================== 自動訓練流程 ====================
    
    function startAutoTrainingWithNPC(rounds, mode) {
        console.log(`[自動訓練] 啟動 - 輪數: ${rounds}, 模式: ${mode}`);
        
        // 查找所有訓練NPC
        trainingNPCs = findAllTrainingNPCs();
        
        if (trainingNPCs.length === 0) {
            $gameMessage.add("========== 錯誤 ==========");
            $gameMessage.add("地圖上沒有找到訓練NPC！");
            $gameMessage.add("請在事件備註中添加 <TrainingNPC> 標籤");
            return;
        }
        
        autoTrainingActive = true;
        currentNPCIndex = 0;
        totalRounds = rounds;
        completedRounds = 0;
        currentMode = mode;
        isMovingToNPC = false;
        isInSimulation = false;
        
        $gameVariables.setValue(COMPLETED_ROUNDS_VAR_ID, 0);
        
        $gameMessage.add("========== 自動訓練啟動 ==========");
        $gameMessage.add(`找到 ${trainingNPCs.length} 個訓練NPC`);
        $gameMessage.add(`訓練輪數: ${rounds === 0 ? '無限' : rounds}`);
        $gameMessage.add(`模式: ${mode === 'demo' ? '演示' : '快速'}`);
        
        // 開始移動到第一個NPC
        setTimeout(() => {
            moveToNextNPC();
        }, 1000);
    }
    
    function stopAutoTraining() {
        console.log('[自動訓練] 停止');
        
        autoTrainingActive = false;
        isMovingToNPC = false;
        isInSimulation = false;
        
        // 停止當前模擬
        if (currentWebSocket && currentWebSocket.readyState === WebSocket.OPEN) {
            try {
                currentWebSocket.send('stop_now');
            } catch (e) {
                console.error('[自動訓練] 發送停止指令失敗:', e);
            }
        }
        
        // 關閉WebSocket
        if (currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        // 清除移動狀態
        if ($gamePlayer.isMoveRouteForcing()) {
            $gamePlayer._moveRouteForcing = false;
            $gamePlayer._moveRoute = null;
            $gamePlayer._moveRouteIndex = 0;
        }
        
        currentSimulation = null;
        
        $gameMessage.add("========== 自動訓練已停止 ==========");
        $gameMessage.add(`已完成 ${completedRounds} 輪訓練`);
    }
    
    function moveToNextNPC() {
        if (!autoTrainingActive || isInSimulation) return;
        
        // 檢查是否完成所有輪次
        if (totalRounds > 0 && completedRounds >= totalRounds) {
            stopAutoTraining();
            $gameMessage.add("========== 訓練完成 ==========");
            $gameMessage.add(`已完成 ${completedRounds} 輪訓練`);
            return;
        }
        
        // 檢查是否完成一輪NPC
        if (currentNPCIndex >= trainingNPCs.length) {
            completedRounds++;
            $gameVariables.setValue(COMPLETED_ROUNDS_VAR_ID, completedRounds);
            
            console.log(`[自動訓練] 完成第 ${completedRounds} 輪`);
            
            // 重置NPC索引
            currentNPCIndex = 0;
            
            // 繼續下一輪
            if (autoTrainingActive) {
                setTimeout(() => {
                    moveToNextNPC();
                }, 2000);
            }
            return;
        }
        
        const npcData = trainingNPCs[currentNPCIndex];
        console.log(`[自動訓練] 移動到 NPC ${currentNPCIndex + 1}/${trainingNPCs.length}`);
        
        isMovingToNPC = true;
        
        // 設置移動速度
        $gamePlayer.setMoveSpeed(MOVE_SPEED);
        
        // 移動到NPC
        movePlayerToPosition(npcData.x, npcData.y, () => {
            isMovingToNPC = false;
            
            // 面向NPC
            $gamePlayer.turnTowardCharacter(npcData.event);
            
            // 啟動模擬
            startSimulationForNPC(npcData);
        });
    }
    
    function movePlayerToPosition(targetX, targetY, callback) {
        const player = $gamePlayer;
        
        // 使用路徑查找移動
        const route = findPath(player.x, player.y, targetX, targetY);
        
        if (route.length === 0) {
            console.error('[移動] 無法找到路徑');
            callback();
            return;
        }
        
        executeRoute(route, callback);
    }
    
    function findPath(startX, startY, goalX, goalY) {
        // 簡單的A*路徑查找
        const openList = [{x: startX, y: startY, g: 0, h: Math.abs(goalX - startX) + Math.abs(goalY - startY), parent: null}];
        const closedList = [];
        
        while (openList.length > 0) {
            // 找到f值最小的節點
            let currentIndex = 0;
            for (let i = 1; i < openList.length; i++) {
                if (openList[i].g + openList[i].h < openList[currentIndex].g + openList[currentIndex].h) {
                    currentIndex = i;
                }
            }
            
            const current = openList[currentIndex];
            
            // 到達目標
            if (current.x === goalX && current.y === goalY) {
                const path = [];
                let node = current;
                while (node.parent) {
                    path.unshift({x: node.x, y: node.y});
                    node = node.parent;
                }
                return path;
            }
            
            // 移到closed list
            openList.splice(currentIndex, 1);
            closedList.push(current);
            
            // 檢查相鄰節點
            const neighbors = [
                {x: current.x, y: current.y - 1, d: 8},  // 上
                {x: current.x, y: current.y + 1, d: 2},  // 下
                {x: current.x - 1, y: current.y, d: 4},  // 左
                {x: current.x + 1, y: current.y, d: 6}   // 右
            ];
            
            for (const neighbor of neighbors) {
                // 檢查是否可通行
                if (!$gamePlayer.canPass(current.x, current.y, neighbor.d)) {
                    continue;
                }
                
                // 檢查是否在closed list
                if (closedList.some(n => n.x === neighbor.x && n.y === neighbor.y)) {
                    continue;
                }
                
                const g = current.g + 1;
                const h = Math.abs(goalX - neighbor.x) + Math.abs(goalY - neighbor.y);
                
                // 檢查是否在open list
                const existingIndex = openList.findIndex(n => n.x === neighbor.x && n.y === neighbor.y);
                if (existingIndex >= 0) {
                    if (g < openList[existingIndex].g) {
                        openList[existingIndex].g = g;
                        openList[existingIndex].parent = current;
                    }
                } else {
                    openList.push({x: neighbor.x, y: neighbor.y, g: g, h: h, parent: current});
                }
            }
            
            // 防止無限循環
            if (closedList.length > 500) {
                console.error('[路徑查找] 超過最大步數');
                return [];
            }
        }
        
        return [];
    }
    
    function executeRoute(route, callback) {
        if (route.length === 0) {
            callback();
            return;
        }
        
        let currentStep = 0;
        
        function moveNextStep() {
            if (!autoTrainingActive || currentStep >= route.length) {
                callback();
                return;
            }
            
            const target = route[currentStep];
            const player = $gamePlayer;
            
            // 計算方向
            const dx = target.x - player.x;
            const dy = target.y - player.y;
            
            let direction = 0;
            if (dx > 0) direction = 6;      // 右
            else if (dx < 0) direction = 4; // 左
            else if (dy > 0) direction = 2; // 下
            else if (dy < 0) direction = 8; // 上
            
            if (direction > 0 && player.canPass(player.x, player.y, direction)) {
                player.moveStraight(direction);
            }
            
            currentStep++;
            
            // 等待移動完成
            setTimeout(() => {
                if (!player.isMoving()) {
                    moveNextStep();
                } else {
                    // 等待移動完成後再繼續
                    const checkMoving = setInterval(() => {
                        if (!player.isMoving()) {
                            clearInterval(checkMoving);
                            moveNextStep();
                        }
                    }, 100);
                }
            }, 50);
        }
        
        moveNextStep();
    }
    
    // ==================== 模擬管理 ====================
    
    function startSimulationForNPC(npcData) {
        console.log(`[模擬] 啟動 - NPC ${npcData.eventId}`);
        
        isInSimulation = true;
        
        const persona = npcData.config.persona;
        const tactic = npcData.config.tactic;
        
        if (!SHOW_DETAILS) {
            $gameMessage.add(`正在訓練 (${currentNPCIndex + 1}/${trainingNPCs.length})...`);
        }
        
        // 調用 simulation API
        fetch(`${API_BASE_URL}/simulation/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                victim_persona: persona,
                scam_tactic: tactic,
                mode: currentMode,
                auto_train: false  // 我們自己管理循環
            })
        })
        .then(response => response.json())
        .then(data => {
            const simulationId = data.simulation_id;
            
            currentSimulation = {
                id: simulationId,
                npc: npcData,
                persona: persona,
                tactic: tactic
            };
            
            $gameVariables.setValue(SIM_VAR_ID, simulationId);
            
            // 建立WebSocket連接
            connectWebSocket(simulationId);
        })
        .catch(error => {
            console.error('[模擬] 啟動失敗:', error);
            $gameMessage.add(`模擬啟動失敗: ${error.message}`);
            isInSimulation = false;
            
            // 繼續下一個NPC
            setTimeout(() => {
                currentNPCIndex++;
                moveToNextNPC();
            }, 1000);
        });
    }
    
    function connectWebSocket(simulationId) {
        const wsUrl = `${WS_BASE_URL}/ws/simulation/${simulationId}`;
        currentWebSocket = new WebSocket(wsUrl);
        
        currentWebSocket.onopen = function() {
            console.log('[WebSocket] 已連接');
        };
        
        currentWebSocket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketEvent(data);
        };
        
        currentWebSocket.onerror = function(error) {
            console.error('[WebSocket] 錯誤:', error);
        };
        
        currentWebSocket.onclose = function() {
            console.log('[WebSocket] 已關閉');
        };
    }
    
    function handleWebSocketEvent(data) {
        const eventType = data.event_type;
        const payload = data.payload;
        
        switch (eventType) {
            case 'agent_turn':
                if (SHOW_DETAILS) {
                    $gameMessage.add(`${payload.character_name}: ${payload.dialogue.substring(0, 50)}...`);
                }
                break;
            
            case 'trust_update':
                $gameVariables.setValue(TRUST_SCAMMER_VAR_ID, payload.trust_in_scammer);
                $gameVariables.setValue(TRUST_EXPERT_VAR_ID, payload.trust_in_expert);
                break;
            
            case 'simulation_end':
                handleSimulationEnd(payload);
                break;
        }
    }
    
    function handleSimulationEnd(payload) {
        const outcome = payload.outcome;
        
        console.log(`[模擬] 結束 - 結果: ${outcome}`);
        
        $gameVariables.setValue(OUTCOME_VAR_ID, outcome);
        
        if (SHOW_DETAILS) {
            $gameMessage.add(`結果: ${outcome}`);
        }
        
        // 關閉WebSocket
        if (currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        isInSimulation = false;
        currentSimulation = null;
        
        // 移動到下一個NPC
        currentNPCIndex++;
        
        setTimeout(() => {
            if (autoTrainingActive) {
                moveToNextNPC();
            }
        }, 1000);
    }
    
    // ==================== 場景更新 ====================
    
    const _Scene_Map_update = Scene_Map.prototype.update;
    Scene_Map.prototype.update = function() {
        _Scene_Map_update.call(this);
        
        // 禁用玩家控制（在自動訓練期間）
        if (autoTrainingActive) {
            $gamePlayer.setMoveSpeed(MOVE_SPEED);
        }
    };
    
})();

