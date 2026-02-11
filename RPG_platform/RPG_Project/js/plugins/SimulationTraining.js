/*:
 * @target MZ MV
 * @plugindesc 防詐騙模擬訓練系統 - 使用 simulation_routes.py API
 * @author AI-Agent Team
 * @url https://github.com/yourusername/ai-agent
 * 
 * @help SimulationTraining.js
 * 
 * 這個插件實現了完整的防詐騙模擬訓練系統，
 * 使用 backend/api/simulation_routes.py 的 API
 * 
 * 插件命令：
 * 
 * 1. StartSimulation victim_persona scam_tactic mode
 *    啟動單次模擬
 *    - victim_persona: elderly/average/overconfident
 *    - scam_tactic: 詐騙手法名稱
 *    - mode: fast/demo
 * 
 * 2. StartAutoTraining rounds mode
 *    啟動自動訓練
 *    - rounds: 訓練輪數（0=無限）
 *    - mode: fast/demo
 * 
 * 3. StopAutoTraining
 *    停止自動訓練
 * 
 * 4. ShowSimulationStatus
 *    顯示當前模擬狀態
 * 
 * @param apiBaseUrl
 * @text API Base URL
 * @desc 後端API的基礎URL
 * @type string
 * @default http://localhost:8000
 * 
 * @param wsBaseUrl
 * @text WebSocket Base URL
 * @desc WebSocket的基礎URL
 * @type string
 * @default ws://localhost:8000
 * 
 * @param autoReconnect
 * @text 自動重連
 * @desc WebSocket斷開後是否自動重連
 * @type boolean
 * @default true
 * 
 * @param showTrustUpdates
 * @text 顯示信任度更新
 * @desc 是否在遊戲中顯示信任度更新
 * @type boolean
 * @default true
 * 
 * @param showPerformanceScores
 * @text 顯示性能評分
 * @desc 是否在遊戲中顯示性能評分
 * @type boolean
 * @default true
 * 
 * @param simulationVarId
 * @text 模擬ID變量
 * @desc 用於存儲當前模擬ID的遊戲變量ID
 * @type variable
 * @default 20
 * 
 * @param trustScammerVarId
 * @text 對騙徒信任度變量
 * @desc 用於存儲對騙徒信任度的遊戲變量ID
 * @type variable
 * @default 21
 * 
 * @param trustExpertVarId
 * @text 對專家信任度變量
 * @desc 用於存儲對專家信任度的遊戲變量ID
 * @type variable
 * @default 22
 * 
 * @param outcomeVarId
 * @text 結果變量
 * @desc 用於存儲模擬結果的遊戲變量ID (SUCCESS/FAILURE/PARTIAL)
 * @type variable
 * @default 23
 * 
 * @param autoTrainingRoundsVarId
 * @text 自動訓練輪數變量
 * @desc 用於存儲已完成的自動訓練輪數的遊戲變量ID
 * @type variable
 * @default 24
 */

(function() {
    'use strict';

    const pluginName = 'SimulationTraining';
    const parameters = PluginManager.parameters(pluginName);
    
    // 參數設定
    const API_BASE_URL = String(parameters['apiBaseUrl'] || 'http://localhost:8000');
    const WS_BASE_URL = String(parameters['wsBaseUrl'] || 'ws://localhost:8000');
    const AUTO_RECONNECT = parameters['autoReconnect'] === 'true';
    const SHOW_TRUST_UPDATES = parameters['showTrustUpdates'] === 'true';
    const SHOW_PERFORMANCE_SCORES = parameters['showPerformanceScores'] === 'true';
    
    const SIM_VAR_ID = Number(parameters['simulationVarId'] || 20);
    const TRUST_SCAMMER_VAR_ID = Number(parameters['trustScammerVarId'] || 21);
    const TRUST_EXPERT_VAR_ID = Number(parameters['trustExpertVarId'] || 22);
    const OUTCOME_VAR_ID = Number(parameters['outcomeVarId'] || 23);
    const AUTO_TRAINING_ROUNDS_VAR_ID = Number(parameters['autoTrainingRoundsVarId'] || 24);
    
    // 全局狀態
    let currentSimulation = null;
    let currentWebSocket = null;
    let autoTrainingActive = false;
    let autoTrainingTotalRounds = 0;
    let autoTrainingCompletedRounds = 0;
    let autoTrainingMode = 'fast';
    
    // 詐騙手法列表
    const SCAM_TACTICS = [
        "冒充銀行客服詐騙",
        "冒充政府機關詐騙",
        "投資理財詐騙",
        "網購退款詐騙",
        "假冒親友詐騙",
        "求職詐騙",
        "中獎詐騙",
        "愛情交友詐騙"
    ];
    
    // 受害者類型列表
    const VICTIM_PERSONAS = ["elderly", "average", "overconfident"];
    
    // ========== 插件命令註冊 ==========
    
    if (typeof PluginManager !== 'undefined' && PluginManager.registerCommand) {
        // MZ 格式
        PluginManager.registerCommand(pluginName, 'StartSimulation', function(args) {
            const victimPersona = String(args.victim_persona || 'average');
            const scamTactic = String(args.scam_tactic || SCAM_TACTICS[0]);
            const mode = String(args.mode || 'fast');
            startSimulation(victimPersona, scamTactic, mode, false);
        });
        
        PluginManager.registerCommand(pluginName, 'StartAutoTraining', function(args) {
            const rounds = Number(args.rounds || 0);
            const mode = String(args.mode || 'fast');
            startAutoTraining(rounds, mode);
        });
        
        PluginManager.registerCommand(pluginName, 'StopAutoTraining', function(args) {
            stopAutoTraining();
        });
        
        PluginManager.registerCommand(pluginName, 'ShowSimulationStatus', function(args) {
            showSimulationStatus();
        });
    }
    
    // MV 兼容
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'StartSimulation') {
            const victimPersona = args[0] || 'average';
            const scamTactic = args.slice(1).join(' ') || SCAM_TACTICS[0];
            const mode = args[args.length - 1] || 'fast';
            startSimulation(victimPersona, scamTactic, mode, false);
        } else if (command === 'StartAutoTraining') {
            const rounds = Number(args[0] || 0);
            const mode = args[1] || 'fast';
            startAutoTraining(rounds, mode);
        } else if (command === 'StopAutoTraining') {
            stopAutoTraining();
        } else if (command === 'ShowSimulationStatus') {
            showSimulationStatus();
        }
    };
    
    // ========== 核心功能函數 ==========
    
    /**
     * 啟動單次模擬
     */
    function startSimulation(victimPersona, scamTactic, mode, isAutoTraining) {
        console.log(`[SimulationTraining] 啟動模擬 - persona: ${victimPersona}, tactic: ${scamTactic}, mode: ${mode}`);
        
        if (!isAutoTraining) {
            $gameMessage.add("========== 啟動防詐騙模擬 ==========");
            $gameMessage.add(`受害者類型: ${getPersonaDisplayName(victimPersona)}`);
            $gameMessage.add(`詐騙手法: ${scamTactic}`);
            $gameMessage.add(`模式: ${mode === 'demo' ? '演示' : '快速'}`);
        }
        
        // 調用 /simulation/start API
        const xhr = new XMLHttpRequest();
        xhr.open('POST', API_BASE_URL + '/simulation/start', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    const simulationId = response.simulation_id;
                    const wsUrl = response.websocket_url;
                    
                    console.log(`[SimulationTraining] 模擬已啟動 - ID: ${simulationId}`);
                    
                    // 保存模擬狀態
                    currentSimulation = {
                        id: simulationId,
                        victimPersona: victimPersona,
                        scamTactic: scamTactic,
                        mode: mode,
                        isAutoTraining: isAutoTraining,
                        conversationHistory: [],
                        trustInScammer: 70,
                        trustInExpert: 50,
                        outcome: null
                    };
                    
                    // 保存到遊戲變量
                    $gameVariables.setValue(SIM_VAR_ID, simulationId);
                    $gameVariables.setValue(TRUST_SCAMMER_VAR_ID, 70);
                    $gameVariables.setValue(TRUST_EXPERT_VAR_ID, 50);
                    
                    // 建立 WebSocket 連接
                    connectWebSocket(simulationId);
                    
                } catch (e) {
                    console.error('[SimulationTraining] 解析啟動回應時發生錯誤:', e);
                    $gameMessage.add('啟動模擬失敗！');
                }
            } else {
                console.error('[SimulationTraining] 模擬啟動失敗:', xhr.status);
                $gameMessage.add('無法連接到模擬服務器！');
            }
        };
        
        xhr.onerror = function() {
            console.error('[SimulationTraining] 模擬啟動連接錯誤');
            $gameMessage.add('網路連接失敗！');
        };
        
        const payload = {
            victim_persona: victimPersona,
            scam_tactic: scamTactic,
            mode: mode,
            auto_train: isAutoTraining
        };
        
        xhr.send(JSON.stringify(payload));
    }
    
    /**
     * 建立 WebSocket 連接
     */
    function connectWebSocket(simulationId) {
        console.log(`[SimulationTraining] 建立 WebSocket 連接 - ID: ${simulationId}`);
        
        const wsUrl = `${WS_BASE_URL}/ws/simulation/${simulationId}`;
        
        try {
            currentWebSocket = new WebSocket(wsUrl);
            
            currentWebSocket.onopen = function(event) {
                console.log('[SimulationTraining] WebSocket 已連接');
            };
            
            currentWebSocket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketEvent(data);
                } catch (e) {
                    console.error('[SimulationTraining] 解析 WebSocket 訊息時發生錯誤:', e);
                }
            };
            
            currentWebSocket.onerror = function(error) {
                console.error('[SimulationTraining] WebSocket 錯誤:', error);
            };
            
            currentWebSocket.onclose = function(event) {
                console.log('[SimulationTraining] WebSocket 已關閉');
                
                if (AUTO_RECONNECT && currentSimulation && !currentSimulation.outcome) {
                    // 如果模擬還在進行中，嘗試重連
                    console.log('[SimulationTraining] 嘗試重新連接...');
                    setTimeout(() => {
                        connectWebSocket(simulationId);
                    }, 2000);
                }
            };
            
        } catch (e) {
            console.error('[SimulationTraining] 建立 WebSocket 連接失敗:', e);
            $gameMessage.add('無法建立即時連接！');
        }
    }
    
    /**
     * 處理 WebSocket 事件
     */
    function handleWebSocketEvent(data) {
        const eventType = data.event_type;
        const payload = data.payload;
        
        console.log(`[SimulationTraining] 收到事件: ${eventType}`);
        
        switch (eventType) {
            case 'connection_success':
                handleConnectionSuccess(payload);
                break;
            
            case 'simulation_start':
                handleSimulationStart(payload);
                break;
            
            case 'agent_turn':
                handleAgentTurn(payload);
                break;
            
            case 'trust_update':
                handleTrustUpdate(payload);
                break;
            
            case 'performance_scores':
                handlePerformanceScores(payload);
                break;
            
            case 'simulation_end':
                handleSimulationEnd(payload);
                break;
            
            case 'turn_progress':
                handleTurnProgress(payload);
                break;
            
            case 'tool_use':
                handleToolUse(payload);
                break;
            
            case 'heartbeat':
                // 心跳事件，不需要處理
                break;
            
            case 'auto_new_round_starting':
                handleAutoNewRoundStarting(payload);
                break;
            
            default:
                console.log(`[SimulationTraining] 未知事件類型: ${eventType}`);
        }
    }
    
    /**
     * 處理連接成功
     */
    function handleConnectionSuccess(payload) {
        console.log('[SimulationTraining] 連接成功');
        if (currentSimulation && !currentSimulation.isAutoTraining) {
            $gameMessage.add('即時連接已建立！');
        }
    }
    
    /**
     * 處理模擬開始
     */
    function handleSimulationStart(payload) {
        console.log('[SimulationTraining] 模擬開始');
        
        if (currentSimulation) {
            currentSimulation.characters = payload.characters;
            currentSimulation.initialTrust = payload.initial_trust;
            currentSimulation.initialScores = payload.initial_scores;
        }
        
        if (!currentSimulation || !currentSimulation.isAutoTraining) {
            $gameMessage.add("========== 對話開始 ==========");
            
            if (payload.characters) {
                payload.characters.forEach(char => {
                    $gameMessage.add(`${char.name}: ${char.persona_summary}`);
                });
            }
        }
    }
    
    /**
     * 處理角色回合
     */
    function handleAgentTurn(payload) {
        const characterName = payload.character_name;
        const dialogue = payload.dialogue;
        
        console.log(`[SimulationTraining] ${characterName}: ${dialogue.substring(0, 50)}...`);
        
        if (currentSimulation) {
            currentSimulation.conversationHistory.push({
                speaker: characterName,
                dialogue: dialogue
            });
        }
        
        // 顯示對話（如果不是自動訓練或者是演示模式）
        if (!currentSimulation || !currentSimulation.isAutoTraining || currentSimulation.mode === 'demo') {
            $gameMessage.add(`【${characterName}】`);
            $gameMessage.add(dialogue);
        }
    }
    
    /**
     * 處理信任度更新
     */
    function handleTrustUpdate(payload) {
        const trustInScammer = payload.trust_in_scammer;
        const trustInExpert = payload.trust_in_expert;
        const alertness = payload.alertness;
        const emotionalState = payload.emotional_state;
        
        console.log(`[SimulationTraining] 信任度更新 - 騙徒: ${trustInScammer}, 專家: ${trustInExpert}`);
        
        if (currentSimulation) {
            currentSimulation.trustInScammer = trustInScammer;
            currentSimulation.trustInExpert = trustInExpert;
            currentSimulation.alertness = alertness;
            currentSimulation.emotionalState = emotionalState;
        }
        
        // 更新遊戲變量
        $gameVariables.setValue(TRUST_SCAMMER_VAR_ID, trustInScammer);
        $gameVariables.setValue(TRUST_EXPERT_VAR_ID, trustInExpert);
        
        // 顯示信任度更新
        if (SHOW_TRUST_UPDATES && (!currentSimulation || !currentSimulation.isAutoTraining)) {
            $gameMessage.add(`【信任度】騙徒: ${trustInScammer}/100, 專家: ${trustInExpert}/100`);
        }
    }
    
    /**
     * 處理性能評分
     */
    function handlePerformanceScores(payload) {
        const turn = payload.turn;
        const scammerScores = payload.scammer;
        const expertScores = payload.expert;
        
        console.log(`[SimulationTraining] 第${turn}輪評分 - 騙徒: ${scammerScores.overall_score}, 專家: ${expertScores.overall_score}`);
        
        // 顯示性能評分（僅在非自動訓練或演示模式下）
        if (SHOW_PERFORMANCE_SCORES && (!currentSimulation || !currentSimulation.isAutoTraining || currentSimulation.mode === 'demo')) {
            $gameMessage.add(`【第${turn}輪評分】`);
            $gameMessage.add(`騙徒: ${scammerScores.overall_score.toFixed(1)}/100`);
            $gameMessage.add(`專家: ${expertScores.overall_score.toFixed(1)}/100`);
        }
    }
    
    /**
     * 處理模擬結束
     */
    function handleSimulationEnd(payload) {
        const outcome = payload.outcome;
        const resultText = payload.result_text;
        const analysis = payload.analysis;
        const filename = payload.filename;
        
        console.log(`[SimulationTraining] 模擬結束 - 結果: ${outcome}`);
        
        if (currentSimulation) {
            currentSimulation.outcome = outcome;
            currentSimulation.resultText = resultText;
            currentSimulation.analysis = analysis;
            currentSimulation.filename = filename;
        }
        
        // 更新遊戲變量
        $gameVariables.setValue(OUTCOME_VAR_ID, outcome);
        
        // 顯示結果
        const isAutoTraining = currentSimulation && currentSimulation.isAutoTraining;
        
        if (!isAutoTraining) {
            $gameMessage.add("========== 模擬結束 ==========");
            $gameMessage.add(`結果: ${resultText}`);
            $gameMessage.add(`判定: ${outcome}`);
            
            if (analysis) {
                if (analysis.success_reason) {
                    $gameMessage.add(`成功原因: ${analysis.success_reason.substring(0, 50)}...`);
                } else if (analysis.failure_reason) {
                    $gameMessage.add(`失敗原因: ${analysis.failure_reason.substring(0, 50)}...`);
                }
                
                if (analysis.improvement_suggestion) {
                    $gameMessage.add(`改進建議: ${analysis.improvement_suggestion.substring(0, 50)}...`);
                }
            }
            
            if (filename) {
                $gameMessage.add(`訓練數據已保存: ${filename}`);
            }
        } else {
            // 自動訓練模式
            autoTrainingCompletedRounds++;
            $gameVariables.setValue(AUTO_TRAINING_ROUNDS_VAR_ID, autoTrainingCompletedRounds);
            
            console.log(`[自動訓練] 第${autoTrainingCompletedRounds}輪完成 - 結果: ${outcome}`);
            
            // 檢查是否繼續訓練
            if (autoTrainingTotalRounds === 0 || autoTrainingCompletedRounds < autoTrainingTotalRounds) {
                // 繼續下一輪（等待後端自動啟動新模擬）
                console.log(`[自動訓練] 等待下一輪模擬...`);
            } else {
                // 訓練完成
                stopAutoTraining();
                $gameMessage.add("========== 自動訓練完成 ==========");
                $gameMessage.add(`已完成 ${autoTrainingCompletedRounds} 輪訓練`);
            }
        }
        
        // 關閉 WebSocket（如果不是自動訓練）
        if (!isAutoTraining && currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        // 清除當前模擬狀態（如果不是自動訓練）
        if (!isAutoTraining) {
            currentSimulation = null;
        }
    }
    
    /**
     * 處理回合進度
     */
    function handleTurnProgress(payload) {
        const currentTurn = payload.current_turn;
        const maxTurns = payload.max_turns;
        
        console.log(`[SimulationTraining] 回合進度: ${currentTurn}/${maxTurns}`);
    }
    
    /**
     * 處理工具使用
     */
    function handleToolUse(payload) {
        const characterName = payload.character_name;
        const action = payload.action;
        
        console.log(`[SimulationTraining] ${characterName} 使用工具: ${action}`);
        
        // 僅在非自動訓練模式下顯示
        if (!currentSimulation || !currentSimulation.isAutoTraining) {
            $gameMessage.add(`【${characterName}】${action}`);
        }
    }
    
    /**
     * 處理自動新輪次開始
     */
    function handleAutoNewRoundStarting(payload) {
        const newSimulationId = payload.new_simulation_id;
        const victimPersona = payload.victim_persona;
        const scamTactic = payload.scam_tactic;
        const mode = payload.mode;
        
        console.log(`[自動訓練] 新輪次開始 - ID: ${newSimulationId}, persona: ${victimPersona}, tactic: ${scamTactic}`);
        
        // 更新當前模擬狀態
        if (currentSimulation) {
            currentSimulation.id = newSimulationId;
            currentSimulation.victimPersona = victimPersona;
            currentSimulation.scamTactic = scamTactic;
            currentSimulation.mode = mode;
            currentSimulation.conversationHistory = [];
            currentSimulation.trustInScammer = 70;
            currentSimulation.trustInExpert = 50;
            currentSimulation.outcome = null;
        }
        
        // 更新遊戲變量
        $gameVariables.setValue(SIM_VAR_ID, newSimulationId);
        $gameVariables.setValue(TRUST_SCAMMER_VAR_ID, 70);
        $gameVariables.setValue(TRUST_EXPERT_VAR_ID, 50);
        
        // 重新建立 WebSocket 連接
        if (currentWebSocket) {
            currentWebSocket.close();
        }
        connectWebSocket(newSimulationId);
    }
    
    /**
     * 啟動自動訓練
     */
    function startAutoTraining(rounds, mode) {
        console.log(`[自動訓練] 啟動 - 輪數: ${rounds === 0 ? '無限' : rounds}, 模式: ${mode}`);
        
        autoTrainingActive = true;
        autoTrainingTotalRounds = rounds;
        autoTrainingCompletedRounds = 0;
        autoTrainingMode = mode;
        
        $gameVariables.setValue(AUTO_TRAINING_ROUNDS_VAR_ID, 0);
        
        $gameMessage.add("========== 自動訓練啟動 ==========");
        $gameMessage.add(`訓練輪數: ${rounds === 0 ? '無限' : rounds}`);
        $gameMessage.add(`訓練模式: ${mode === 'demo' ? '演示' : '快速'}`);
        $gameMessage.add("正在啟動第一輪模擬...");
        
        // 隨機選擇參數
        const victimPersona = VICTIM_PERSONAS[Math.floor(Math.random() * VICTIM_PERSONAS.length)];
        const scamTactic = SCAM_TACTICS[Math.floor(Math.random() * SCAM_TACTICS.length)];
        
        // 啟動第一次模擬
        startSimulation(victimPersona, scamTactic, mode, true);
    }
    
    /**
     * 停止自動訓練
     */
    function stopAutoTraining() {
        console.log(`[自動訓練] 停止 - 已完成 ${autoTrainingCompletedRounds} 輪`);
        
        autoTrainingActive = false;
        
        // 如果有正在進行的模擬，發送停止指令
        if (currentWebSocket && currentWebSocket.readyState === WebSocket.OPEN) {
            try {
                currentWebSocket.send('stop_now');
            } catch (e) {
                console.error('[自動訓練] 發送停止指令失敗:', e);
            }
        }
        
        // 關閉 WebSocket
        if (currentWebSocket) {
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        // 清除狀態
        currentSimulation = null;
        
        $gameMessage.add("========== 自動訓練已停止 ==========");
        $gameMessage.add(`已完成 ${autoTrainingCompletedRounds} 輪訓練`);
    }
    
    /**
     * 顯示模擬狀態
     */
    function showSimulationStatus() {
        if (!currentSimulation) {
            $gameMessage.add("========== 模擬狀態 ==========");
            $gameMessage.add("當前沒有進行中的模擬");
            return;
        }
        
        $gameMessage.add("========== 模擬狀態 ==========");
        $gameMessage.add(`模擬ID: ${currentSimulation.id}`);
        $gameMessage.add(`受害者類型: ${getPersonaDisplayName(currentSimulation.victimPersona)}`);
        $gameMessage.add(`詐騙手法: ${currentSimulation.scamTactic}`);
        $gameMessage.add(`對騙徒信任度: ${currentSimulation.trustInScammer}/100`);
        $gameMessage.add(`對專家信任度: ${currentSimulation.trustInExpert}/100`);
        $gameMessage.add(`對話輪數: ${currentSimulation.conversationHistory.length}`);
        
        if (autoTrainingActive) {
            $gameMessage.add("--- 自動訓練中 ---");
            $gameMessage.add(`已完成輪數: ${autoTrainingCompletedRounds}`);
            if (autoTrainingTotalRounds > 0) {
                $gameMessage.add(`目標輪數: ${autoTrainingTotalRounds}`);
            } else {
                $gameMessage.add(`目標輪數: 無限`);
            }
        }
    }
    
    /**
     * 獲取角色類型顯示名稱
     */
    function getPersonaDisplayName(persona) {
        const displayNames = {
            'elderly': '長者（高風險）',
            'average': '一般市民',
            'overconfident': '過度自信者'
        };
        return displayNames[persona] || persona;
    }
    
    // ========== 窗口關閉時清理 ==========
    
    window.addEventListener('beforeunload', function() {
        if (currentWebSocket) {
            currentWebSocket.close();
        }
    });
    
})();

