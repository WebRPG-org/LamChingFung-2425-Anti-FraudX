/*:
 * @plugindesc 防詐騙訓練系統 - 簡化版（使用原生消息系統）
 * @author AI-Agent Team
 * 
 * @param ApiUrl
 * @desc 後端 API URL
 * @default http://localhost:8000
 * 
 * @param AutoStartOnMap
 * @desc 自動啟動的地圖ID
 * @default 2
 * 
 * @param AutoStartSwitch
 * @desc 自動啟動開關ID
 * @default 10
 * 
 * @help
 * 簡化版本 - 直接使用 RPG Maker 原生消息系統顯示對話
 * 不使用戰鬥場景，更簡單可靠
 */

(function() {
    'use strict';
    
    // ============================================================================
    // 參數讀取
    // ============================================================================
    
    const parameters = PluginManager.parameters('SimulationTraining_Simple');
    const API_URL = String(parameters['ApiUrl'] || 'http://localhost:8000');
    const AUTO_START_MAP_ID = Number(parameters['AutoStartOnMap'] || 2);
    const AUTO_START_SWITCH = Number(parameters['AutoStartSwitch'] || 10);
    
    // ============================================================================
    // 常量定義
    // ============================================================================
    
    const NPC_IDS = [1, 2, 3, 4, 5, 6];
    const NPC_POSITIONS = {
        1: {x: 10, y: 8},
        2: {x: 17, y: 8},
        3: {x: 24, y: 8},
        4: {x: 10, y: 15},
        5: {x: 17, y: 15},
        6: {x: 24, y: 15}
    };
    
    const SCAM_TYPES = {
        1: "冒充銀行客服詐騙",
        2: "假冒公安法院詐騙",
        3: "投資理財詐騙",
        4: "網絡購物詐騙",
        5: "冒充熟人詐騙",
        6: "虛假中獎詐騙",
        7: "網絡貸款詐騙",
        8: "色情詐騙",
        9: "退稅詐騙",
        10: "醫療保險詐騙"
    };
    
    const PERSONA_TYPES = ['A', 'B', 'C', 'D'];
    const PERSONA_MAPPING = {
        'A': 'elderly',
        'B': 'average',
        'C': 'overconfident',
        'D': 'student'
    };
    
    const PERSONA_NAMES = {
        'A': '陳老伯（長者）',
        'B': '林小姐（一般市民）',
        'C': '王先生（過度自信者）',
        'D': '李同學（年輕學生）'
    };
    
    // ============================================================================
    // 全局變量
    // ============================================================================
    
    let autoModeActive = false;
    let currentAutoNpcIndex = 0;
    let isMovingToNpc = false;
    let currentWebSocket = null;
    let currentSimulation = null;
    let isProcessingDialogue = false;
    let dialogueQueue = [];
    
    // ============================================================================
    // 插件命令
    // ============================================================================
    
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'StartAutoTraining') {
            startAutoMode();
        } else if (command === 'StopAutoTraining') {
            stopAutoMode();
        }
    };
    
    // ============================================================================
    // 自動模式管理
    // ============================================================================
    
    function startAutoMode() {
        if (autoModeActive) {
            console.log('[自動模式] 已經在運行中');
            return;
        }
        
        autoModeActive = true;
        currentAutoNpcIndex = 0;
        
        $gameMessage.add("╔══════════════════════════╗");
        $gameMessage.add("║   自動訓練模式啟動   ║");
        $gameMessage.add("╚══════════════════════════╝");
        $gameMessage.add("");
        $gameMessage.add("系統將自動帶您前往各個NPC");
        $gameMessage.add("進行防詐騙訓練...");
        
        console.log('[自動模式] ✅ 啟動成功');
        
        // 延遲開始，讓訊息顯示
        setTimeout(() => {
            moveToNextNpc();
        }, 2000);
    }
    
    function stopAutoMode() {
        autoModeActive = false;
        isMovingToNpc = false;
        
        if (currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        $gameMessage.add("自動訓練模式已停止");
        console.log('[自動模式] ❌ 已停止');
    }
    
    function moveToNextNpc() {
        if (!autoModeActive) return;
        
        if (currentAutoNpcIndex >= NPC_IDS.length) {
            // 完成一輪，重新開始
            console.log('[自動模式] 🔄 完成一輪，重新開始');
            currentAutoNpcIndex = 0;
            
            // 輪換人設
            rotatePersona();
            
            $gameMessage.add("");
            $gameMessage.add("━━━━━━━━━━━━━━━━━━━━━━━━");
            $gameMessage.add("✅ 完成一輪訓練！");
            $gameMessage.add("━━━━━━━━━━━━━━━━━━━━━━━━");
            $gameMessage.add("");
            $gameMessage.add(`切換人設：${getCurrentPersonaName()}`);
            $gameMessage.add("");
            $gameMessage.add("3秒後開始新一輪...");
            
            setTimeout(() => {
                moveToNextNpc();
            }, 3000);
            return;
        }
        
        const npcId = NPC_IDS[currentAutoNpcIndex];
        const targetPos = NPC_POSITIONS[npcId];
        
        console.log(`[自動移動] 前往 NPC ${npcId} at (${targetPos.x}, ${targetPos.y})`);
        
        isMovingToNpc = true;
        movePlayerToPosition(targetPos.x, targetPos.y, () => {
            isMovingToNpc = false;
            console.log(`[自動移動] 到達 NPC ${npcId}`);
            
            // 到達後開始訓練
            setTimeout(() => {
                startSimulationForNPC(npcId);
            }, 500);
        });
    }
    
    function movePlayerToPosition(targetX, targetY, callback) {
        const player = $gamePlayer;
        const currentX = player.x;
        const currentY = player.y;
        
        if (currentX === targetX && currentY === targetY) {
            if (callback) callback();
            return;
        }
        
        // 簡單路徑：先橫向再縱向
        const moveList = [];
        
        // 橫向移動
        if (currentX < targetX) {
            for (let i = 0; i < targetX - currentX; i++) {
                moveList.push(6); // 右
            }
        } else if (currentX > targetX) {
            for (let i = 0; i < currentX - targetX; i++) {
                moveList.push(4); // 左
            }
        }
        
        // 縱向移動
        if (currentY < targetY) {
            for (let i = 0; i < targetY - currentY; i++) {
                moveList.push(2); // 下
            }
        } else if (currentY > targetY) {
            for (let i = 0; i < currentY - targetY; i++) {
                moveList.push(8); // 上
            }
        }
        
        // 執行移動
        player.setMoveRoute({list: moveList.map(d => ({code: 1, parameters: [d]})).concat([{code: 0}]), repeat: false, skippable: false, wait: false});
        player.forceMoveRoute({list: moveList.map(d => ({code: 1, parameters: [d]})).concat([{code: 0}]), repeat: false, skippable: false, wait: false});
        
        // 等待移動完成
        const checkInterval = setInterval(() => {
            if (!player.isMoving() && player.x === targetX && player.y === targetY) {
                clearInterval(checkInterval);
                if (callback) callback();
            }
        }, 100);
    }
    
    // ============================================================================
    // 人設管理
    // ============================================================================
    
    function rotatePersona() {
        const currentPersona = $gameVariables.value(22) || 'A';
        const currentIndex = PERSONA_TYPES.indexOf(currentPersona);
        const nextIndex = (currentIndex + 1) % PERSONA_TYPES.length;
        const nextPersona = PERSONA_TYPES[nextIndex];
        
        $gameVariables.setValue(22, nextPersona);
        console.log(`[人設] 切換: ${currentPersona} → ${nextPersona}`);
    }
    
    function getCurrentPersonaName() {
        const persona = $gameVariables.value(22) || 'A';
        return PERSONA_NAMES[persona] || persona;
    }
    
    // ============================================================================
    // 模擬訓練（使用 simulation_routes.py）
    // ============================================================================
    
    function startSimulationForNPC(npcId) {
        console.log(`[模擬] 啟動 - NPC ${npcId}`);
        
        // 獲取騙局類型
        const npcIndex = NPC_IDS.indexOf(npcId);
        const varId = 11 + npcIndex;
        const scamType = $gameVariables.value(varId) || (npcIndex + 1);
        const scamTactic = SCAM_TYPES[scamType] || "冒充銀行客服詐騙";
        
        // 獲取人設
        const personaType = $gameVariables.value(22) || 'A';
        const victimPersona = PERSONA_MAPPING[personaType] || 'average';
        
        console.log(`  騙局: ${scamTactic}, 人設: ${personaType} (${victimPersona})`);
        
        // 顯示開場信息
        $gameMessage.add("╔══════════════════════════╗");
        $gameMessage.add("║   防詐騙實戰訓練   ║");
        $gameMessage.add("╚══════════════════════════╝");
        $gameMessage.add("");
        $gameMessage.add(`騙局類型：${scamTactic}`);
        $gameMessage.add(`您的角色：${getCurrentPersonaName()}`);
        $gameMessage.add("");
        $gameMessage.add("━━━━━━━━━━━━━━━━━━━━━━━━");
        $gameMessage.add("");
        
        // 調用 simulation API
        fetch(`${API_URL}/simulation/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                victim_persona: victimPersona,
                scam_tactic: scamTactic,
                mode: 'demo',
                auto_train: false
            })
        })
        .then(response => response.json())
        .then(data => {
            const simulationId = data.simulation_id;
            
            currentSimulation = {
                id: simulationId,
                npcId: npcId,
                scamType: scamType,
                persona: personaType,
                victimPersona: victimPersona,
                scamTactic: scamTactic
            };
            
            console.log('[模擬] ✅ 創建成功:', simulationId);
            
            // 連接 WebSocket
            connectWebSocket(simulationId);
        })
        .catch(error => {
            console.error('[模擬] 啟動失敗:', error);
            $gameMessage.add("");
            $gameMessage.add("❌ 連接失敗，跳過此NPC");
            
            // 繼續下一個
            setTimeout(() => {
                currentAutoNpcIndex++;
                moveToNextNpc();
            }, 2000);
        });
    }
    
    // ============================================================================
    // WebSocket 連接
    // ============================================================================
    
    function connectWebSocket(simulationId) {
        const wsUrl = `${API_URL.replace('http', 'ws')}/ws/simulation/${simulationId}`;
        
        console.log('[WebSocket] 連接:', wsUrl);
        
        try {
            currentWebSocket = new WebSocket(wsUrl);
            
            currentWebSocket.onopen = function() {
                console.log('[WebSocket] ✅ 已連接');
            };
            
            currentWebSocket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[WebSocket] 收到消息:', data.event_type);
                    
                    handleWebSocketEvent(data);
                } catch (error) {
                    console.error('[WebSocket] 解析消息失敗:', error);
                }
            };
            
            currentWebSocket.onerror = function(error) {
                console.error('[WebSocket] 錯誤:', error);
            };
            
            currentWebSocket.onclose = function() {
                console.log('[WebSocket] ❌ 已斷開');
                currentWebSocket = null;
            };
        } catch (error) {
            console.error('[WebSocket] 創建失敗:', error);
        }
    }
    
    // ============================================================================
    // WebSocket 事件處理（直接用 $gameMessage 顯示）
    // ============================================================================
    
    function handleWebSocketEvent(data) {
        const eventType = data.event_type;
        
        if (eventType === 'simulation_start') {
            handleSimulationStart(data.payload);
        } else if (eventType === 'dialogue') {
            handleDialogue(data.payload);
        } else if (eventType === 'trust_update') {
            handleTrustUpdate(data.payload);
        } else if (eventType === 'simulation_end') {
            handleSimulationEnd(data.payload);
        }
    }
    
    function handleSimulationStart(payload) {
        console.log('[模擬] 開始事件');
        
        $gameMessage.add("旁白：模擬對話開始...");
        $gameMessage.add("");
    }
    
    function handleDialogue(payload) {
        const { character, dialogue } = payload;
        
        console.log('[對話] 收到:', character, dialogue.substring(0, 30) + '...');
        
        // 加入對話隊列
        dialogueQueue.push({character, dialogue});
        
        // 如果沒有在處理對話，開始處理
        if (!isProcessingDialogue) {
            processDialogueQueue();
        }
    }
    
    function processDialogueQueue() {
        if (dialogueQueue.length === 0) {
            isProcessingDialogue = false;
            return;
        }
        
        isProcessingDialogue = true;
        
        // 檢查消息系統是否忙碌
        if ($gameMessage.isBusy()) {
            // 等待100ms後重試
            setTimeout(() => {
                processDialogueQueue();
            }, 100);
            return;
        }
        
        // 取出一條對話
        const {character, dialogue} = dialogueQueue.shift();
        
        // 顯示對話
        let displayName = '';
        if (character === 'scammer') {
            displayName = '\\C[2]詐騙犯\\C[0]';
        } else if (character === 'victim') {
            displayName = '\\C[23]您\\C[0]';
        } else if (character === 'expert') {
            displayName = '\\C[3]專家\\C[0]';
        }
        
        $gameMessage.add(`${displayName}：${dialogue}`);
        $gameMessage.add("");
        
        console.log('[對話] ✅ 已顯示:', character);
        
        // 繼續處理下一條（延遲一點，讓消息系統有時間更新）
        setTimeout(() => {
            processDialogueQueue();
        }, 200);
    }
    
    function handleTrustUpdate(payload) {
        const trustInScammer = Math.round(payload.trust_in_scammer);
        const trustInExpert = Math.round(payload.trust_in_expert);
        
        console.log('[信任度] 更新:', trustInScammer, trustInExpert);
        
        $gameVariables.setValue(27, trustInScammer);
        $gameVariables.setValue(28, trustInExpert);
        
        // 等待對話隊列清空
        waitForDialogueQueue(() => {
            $gameMessage.add("━━━━━━━━━━━━━━━━━━━━━━━━");
            $gameMessage.add(`\\C[11]信任度 - 詐騙犯: ${trustInScammer}% | 專家: ${trustInExpert}%\\C[0]`);
            $gameMessage.add("━━━━━━━━━━━━━━━━━━━━━━━━");
            $gameMessage.add("");
        });
    }
    
    function handleSimulationEnd(payload) {
        const outcome = payload.outcome;
        const analysis = payload.analysis || {};
        
        console.log('[模擬] 結束 - 結果:', outcome);
        
        $gameVariables.setValue(24, outcome);
        
        // 關閉 WebSocket
        if (currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        // 等待對話隊列清空
        waitForDialogueQueue(() => {
            // 顯示結果
            $gameMessage.add("");
            $gameMessage.add("╔══════════════════════════╗");
            $gameMessage.add("║      訓練結果評分      ║");
            $gameMessage.add("╚══════════════════════════╝");
            $gameMessage.add("");
            
            if (outcome === 'SUCCESS') {
                $gameMessage.add("\\C[3]【結果】✓ 成功識破詐騙！\\C[0]");
            } else if (outcome === 'FAILURE') {
                $gameMessage.add("\\C[2]【結果】✗ 不幸被騙\\C[0]");
            } else {
                $gameMessage.add("\\C[6]【結果】⚠ 未明確判斷\\C[0]");
            }
            $gameMessage.add("");
            
            // 顯示最終信任度
            const trustInScammer = $gameVariables.value(27) || 0;
            const trustInExpert = $gameVariables.value(28) || 0;
            $gameMessage.add("\\C[11]最終信任度：\\C[0]");
            $gameMessage.add(`  詐騙犯：${trustInScammer}%`);
            $gameMessage.add(`  專家：${trustInExpert}%`);
            $gameMessage.add("");
            
            // 顯示關鍵因素
            if (analysis.key_factors && analysis.key_factors.length > 0) {
                $gameMessage.add("\\C[3]【關鍵因素】\\C[0]");
                analysis.key_factors.slice(0, 3).forEach(factor => {
                    $gameMessage.add(`  • ${factor}`);
                });
                $gameMessage.add("");
            }
            
            $gameMessage.add("3秒後前往下一個NPC...");
            
            // 繼續下一個NPC
            setTimeout(() => {
                currentAutoNpcIndex++;
                moveToNextNpc();
            }, 3000);
        });
    }
    
    function waitForDialogueQueue(callback) {
        if (dialogueQueue.length === 0 && !isProcessingDialogue) {
            callback();
        } else {
            setTimeout(() => {
                waitForDialogueQueue(callback);
            }, 200);
        }
    }
    
    // ============================================================================
    // 自動啟動（地圖進入時）
    // ============================================================================
    
    const _Scene_Map_start = Scene_Map.prototype.start;
    Scene_Map.prototype.start = function() {
        _Scene_Map_start.call(this);
        
        // 檢查是否應該自動啟動
        if ($gameMap.mapId() === AUTO_START_MAP_ID && $gameSwitches.value(AUTO_START_SWITCH) && !autoModeActive) {
            console.log('[自動啟動] 檢測到條件滿足');
            
            setTimeout(() => {
                startAutoMode();
            }, 1000);
        }
    };
    
})();

