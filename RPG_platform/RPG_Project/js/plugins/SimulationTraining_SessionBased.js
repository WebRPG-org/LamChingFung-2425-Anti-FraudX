/*:
 * @plugindesc 防詐騙訓練系統 - Session/歷史記錄版本
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
 * @help
 * 使用 Session/歷史記錄方式
 * WebSocket 消息先存入變量，模擬結束後一次性顯示
 */

(function() {
    'use strict';
    
    const parameters = PluginManager.parameters('SimulationTraining_SessionBased');
    const API_URL = String(parameters['ApiUrl'] || 'http://localhost:8000');
    const AUTO_START_MAP_ID = Number(parameters['AutoStartOnMap'] || 2);
    
    // 全局變量
    let autoModeActive = false;
    let currentAutoNpcIndex = 0;
    let isMovingToNpc = false;
    let currentWebSocket = null;
    let currentSimulation = null;
    
    // Session 數據（存儲對話歷史）
    let dialogueHistory = [];  // [{character, dialogue, round}, ...]
    let trustHistory = [];      // [{round, trust_in_scammer, trust_in_expert}, ...]
    let finalResult = null;
    
    const NPC_IDS = [17, 16, 12, 13, 14, 15];
    const NPC_POSITIONS = {
        17: {x: 10, y: 8},
        16: {x: 17, y: 8},
        12: {x: 24, y: 8},
        13: {x: 10, y: 15},
        14: {x: 17, y: 15},
        15: {x: 24, y: 15}
    };
    
    const SCAM_TYPES = {
        1: "投資理財詐騙",
        2: "冒充政府機關詐騙",
        3: "網購退款詐騙",
        4: "假冒親友詐騙",
        5: "網路交友詐騙",
        6: "假冒客服詐騙",
        7: "虛假中獎詐騙",
        8: "求職詐騙",
        9: "虛假招聘詐騙",
        10: "假冒銀行詐騙"
    };
    
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
    // 自動模式
    // ============================================================================
    
    function startAutoMode() {
        if (autoModeActive) return;
        
        autoModeActive = true;
        currentAutoNpcIndex = 0;
        
        console.log('[自動模式] ✅ 啟動');
        
        setTimeout(() => {
            moveToNextNpc();
        }, 1000);
    }
    
    function stopAutoMode() {
        autoModeActive = false;
        isMovingToNpc = false;
        
        if (currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        console.log('[自動模式] ❌ 停止');
    }
    
    function moveToNextNpc() {
        if (!autoModeActive) return;
        
        if (currentAutoNpcIndex >= NPC_IDS.length) {
            currentAutoNpcIndex = 0;
            rotatePersona();
            
            console.log('[自動模式] 🔄 完成一輪，切換人設');
            
            setTimeout(() => {
                moveToNextNpc();
            }, 3000);
            return;
        }
        
        const npcId = NPC_IDS[currentAutoNpcIndex];
        const targetPos = NPC_POSITIONS[npcId];
        
        console.log(`[自動移動] 前往 NPC ${npcId}`);
        
        isMovingToNpc = true;
        movePlayerToPosition(targetPos.x, targetPos.y, () => {
            isMovingToNpc = false;
            console.log(`[自動移動] 到達 NPC ${npcId}`);
            
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
        
        const moveList = [];
        
        if (currentX < targetX) {
            for (let i = 0; i < targetX - currentX; i++) moveList.push(6);
        } else if (currentX > targetX) {
            for (let i = 0; i < currentX - targetX; i++) moveList.push(4);
        }
        
        if (currentY < targetY) {
            for (let i = 0; i < targetY - currentY; i++) moveList.push(2);
        } else if (currentY > targetY) {
            for (let i = 0; i < currentY - targetY; i++) moveList.push(8);
        }
        
        player.setMoveRoute({list: moveList.map(d => ({code: 1, parameters: [d]})).concat([{code: 0}]), repeat: false, skippable: false, wait: false});
        player.forceMoveRoute({list: moveList.map(d => ({code: 1, parameters: [d]})).concat([{code: 0}]), repeat: false, skippable: false, wait: false});
        
        const checkInterval = setInterval(() => {
            if (!player.isMoving() && player.x === targetX && player.y === targetY) {
                clearInterval(checkInterval);
                if (callback) callback();
            }
        }, 100);
    }
    
    function rotatePersona() {
        const personas = ['A', 'B', 'C', 'D'];
        const currentPersona = $gameVariables.value(22) || 'A';
        const currentIndex = personas.indexOf(currentPersona);
        const nextPersona = personas[(currentIndex + 1) % personas.length];
        
        $gameVariables.setValue(22, nextPersona);
        console.log(`[人設] 切換: ${currentPersona} → ${nextPersona}`);
    }
    
    // ============================================================================
    // 模擬訓練
    // ============================================================================
    
    function startSimulationForNPC(npcId) {
        console.log(`[模擬] 啟動 - NPC ${npcId}`);
        
        // 清空 session 數據
        dialogueHistory = [];
        trustHistory = [];
        finalResult = null;
        
        const npcIndex = NPC_IDS.indexOf(npcId);
        const varId = 11 + npcIndex;
        const scamType = $gameVariables.value(varId) || (npcIndex + 1);
        const scamTactic = SCAM_TYPES[scamType] || "冒充銀行客服詐騙";
        
        const personaType = $gameVariables.value(22) || 'A';
        const victimPersona = PERSONA_MAPPING[personaType] || 'average';
        
        console.log(`  騙局: ${scamTactic}, 人設: ${personaType} (${victimPersona})`);
        
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
            
            // 連接 WebSocket 並收集數據
            connectWebSocket(simulationId);
        })
        .catch(error => {
            console.error('[模擬] 啟動失敗:', error);
            
            setTimeout(() => {
                currentAutoNpcIndex++;
                moveToNextNpc();
            }, 2000);
        });
    }
    
    // ============================================================================
    // WebSocket - 收集數據
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
                    console.error('[WebSocket] 解析失敗:', error);
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
    
    function handleWebSocketEvent(data) {
        const eventType = data.event_type;
        const payload = data.payload;
        
        if (eventType === 'simulation_start') {
            console.log('[Session] 模擬開始');
        } else if (eventType === 'dialogue') {
            // 存儲對話到歷史
            const round = dialogueHistory.filter(d => d.round !== undefined).length + 1;
            dialogueHistory.push({
                character: payload.character,
                dialogue: payload.dialogue,
                round: Math.floor(dialogueHistory.length / 3) + 1
            });
            
            console.log('[Session] 對話已記錄:', payload.character, '-', payload.dialogue.substring(0, 30) + '...');
            console.log('[Session] 當前對話總數:', dialogueHistory.length);
        } else if (eventType === 'trust_update') {
            // 存儲信任度到歷史
            trustHistory.push({
                round: trustHistory.length + 1,
                trust_in_scammer: payload.trust_in_scammer,
                trust_in_expert: payload.trust_in_expert
            });
            
            console.log('[Session] 信任度已記錄:', payload.trust_in_scammer, '/', payload.trust_in_expert);
        } else if (eventType === 'simulation_end') {
            // 存儲最終結果
            finalResult = payload;
            
            console.log('[Session] 模擬結束，開始顯示');
            console.log('[Session] 對話總數:', dialogueHistory.length);
            console.log('[Session] 信任度記錄:', trustHistory.length);
            
            // 關閉 WebSocket
            if (currentWebSocket) {
                currentWebSocket.close();
                currentWebSocket = null;
            }
            
            // 延遲顯示，確保數據完整
            setTimeout(() => {
                displayCompleteSession();
            }, 1000);
        }
    }
    
    // ============================================================================
    // 顯示完整 Session（一次性）
    // ============================================================================
    
    function displayCompleteSession() {
        console.log('[顯示] 開始顯示完整對話');
        console.log('[顯示] 對話數量:', dialogueHistory.length);
        
        if (!currentSimulation) {
            console.error('[顯示] ❌ currentSimulation 不存在');
            return;
        }
        
        // 使用 $gameMessage 顯示
        $gameMessage.add("╔══════════════════════════╗");
        $gameMessage.add("║   防詐騙實戰訓練   ║");
        $gameMessage.add("╚══════════════════════════╝");
        $gameMessage.add("");
        $gameMessage.add(`騙局類型：${currentSimulation.scamTactic}`);
        $gameMessage.add(`您的角色：${PERSONA_NAMES[currentSimulation.persona]}`);
        $gameMessage.add("");
        $gameMessage.add("━━━━━━━━━━━━━━━━━━━━━━━━");
        $gameMessage.add("");
        
        // 按輪次顯示對話
        let currentRound = 0;
        dialogueHistory.forEach((entry, index) => {
            if (entry.round && entry.round !== currentRound) {
                currentRound = entry.round;
                $gameMessage.add("");
                $gameMessage.add(`\\C[14]━━━ 第 ${currentRound} 輪 ━━━\\C[0]`);
                $gameMessage.add("");
            }
            
            let colorCode = '';
            let displayName = '';
            
            if (entry.character === 'scammer') {
                colorCode = '\\C[2]';
                displayName = '詐騙犯';
            } else if (entry.character === 'victim') {
                colorCode = '\\C[23]';
                displayName = '您';
            } else if (entry.character === 'expert') {
                colorCode = '\\C[3]';
                displayName = '專家';
            }
            
            $gameMessage.add(`${colorCode}${displayName}：\\C[0]${entry.dialogue}`);
            $gameMessage.add("");
            
            console.log('[顯示] 對話 ' + (index + 1) + ':', displayName, entry.dialogue.substring(0, 30) + '...');
        });
        
        // 顯示信任度歷史
        if (trustHistory.length > 0) {
            $gameMessage.add("");
            $gameMessage.add("\\C[14]━━━ 信任度變化 ━━━\\C[0]");
            $gameMessage.add("");
            
            trustHistory.forEach((trust, index) => {
                const scammer = Math.round(trust.trust_in_scammer);
                const expert = Math.round(trust.trust_in_expert);
                $gameMessage.add(`第 ${trust.round} 輪：詐騙犯 ${scammer}% | 專家 ${expert}%`);
            });
        }
        
        // 顯示最終結果
        if (finalResult) {
            $gameMessage.add("");
            $gameMessage.add("╔══════════════════════════╗");
            $gameMessage.add("║      訓練結果評分      ║");
            $gameMessage.add("╚══════════════════════════╝");
            $gameMessage.add("");
            
            if (finalResult.outcome === 'SUCCESS') {
                $gameMessage.add("\\C[3]【結果】✓ 成功識破詐騙！\\C[0]");
            } else if (finalResult.outcome === 'FAILURE') {
                $gameMessage.add("\\C[2]【結果】✗ 不幸被騙\\C[0]");
            } else {
                $gameMessage.add("\\C[6]【結果】⚠ 未明確判斷\\C[0]");
            }
            $gameMessage.add("");
            
            const trustInScammer = trustHistory.length > 0 ? Math.round(trustHistory[trustHistory.length - 1].trust_in_scammer) : 0;
            const trustInExpert = trustHistory.length > 0 ? Math.round(trustHistory[trustHistory.length - 1].trust_in_expert) : 0;
            
            $gameMessage.add("\\C[11]最終信任度：\\C[0]");
            $gameMessage.add(`  詐騙犯：${trustInScammer}%`);
            $gameMessage.add(`  專家：${trustInExpert}%`);
            $gameMessage.add("");
            
            if (finalResult.analysis && finalResult.analysis.key_factors) {
                $gameMessage.add("\\C[3]【關鍵因素】\\C[0]");
                finalResult.analysis.key_factors.slice(0, 3).forEach(factor => {
                    $gameMessage.add(`  • ${factor}`);
                });
                $gameMessage.add("");
            }
        }
        
        $gameMessage.add("3秒後前往下一個NPC...");
        
        console.log('[顯示] ✅ 完整對話已顯示');
        console.log('[顯示] $gameMessage 行數:', $gameMessage._texts.length);
        
        // 繼續下一個NPC
        setTimeout(() => {
            currentAutoNpcIndex++;
            moveToNextNpc();
        }, 3000);
    }
    
    // ============================================================================
    // 自動啟動
    // ============================================================================
    
    const _Scene_Map_start = Scene_Map.prototype.start;
    Scene_Map.prototype.start = function() {
        _Scene_Map_start.call(this);
        
        if ($gameMap.mapId() === AUTO_START_MAP_ID && !autoModeActive) {
            console.log('[自動啟動] 檢測到地圖 ' + AUTO_START_MAP_ID);
            
            setTimeout(() => {
                startAutoMode();
            }, 1000);
        }
    };
    
})();


