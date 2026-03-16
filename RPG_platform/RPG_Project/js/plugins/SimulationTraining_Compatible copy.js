/*:
 * @plugindesc 防詐騙模擬訓練系統 - 完全兼容原有RotatingScamSystem設置
 * @author AI-Agent Team
 * 
 * @param API_URL
 * @desc AI後台API地址
 * @default http://localhost:8000
 * 
 * @param AutoStartOnMap
 * @desc 進入指定地圖時自動啟動訓練（0=不自動啟動）
 * @default 0
 * 
 * @param AutoStartSwitch
 * @desc 自動啟動開關ID（0=不使用開關）
 * @default 0
 * 
 * @param AutoStartDelay
 * @desc 自動啟動延遲（秒）
 * @default 3
 * 
 * @param AutoSelectNewGame
 * @desc 自動選擇 New Game（true/false）
 * @default false
 * 
 * @param NewGameDelay
 * @desc New Game 選擇延遲（秒）
 * @default 2
 * 
 * @param AutoTransferToTrainingMap
 * @desc 自動傳送到訓練地圖（true/false）
 * @default false
 * 
 * @param TrainingMapId
 * @desc 訓練地圖ID（例如：forest town 的地圖ID）
 * @default 1
 * 
 * @param TrainingMapX
 * @desc 傳送到訓練地圖的X座標
 * @default 10
 * 
 * @param TrainingMapY
 * @desc 傳送到訓練地圖的Y座標
 * @default 10
 * 
 * @param TransferDelay
 * @desc 傳送延遲（秒）
 * @default 2
 * 
 * @param AutoSelectDialogue
 * @desc 自動選擇對話選項（true/false）
 * @default false
 * 
 * @param DialogueSelectionDelay
 * @desc 對話選擇延遲（秒）
 * @default 1
 * 
 * @help
 * ============================================================================
 * 系統說明
 * ============================================================================
 * 
 * 此插件完全兼容原有的 RotatingScamSystem.js 設置：
 * - 使用相同的 6 個 NPC (Event 12-17)
 * - 使用相同的 NPC 位置和路徑
 * - 使用相同的變量配置
 * - 但使用新的 simulation_routes.py API
 * 
 * ============================================================================
 * NPC 配置（與原系統相同）
 * ============================================================================
 * 
 * NPC 1 (Event 17): 位置 (18, 9)
 * NPC 2 (Event 16): 位置 (35, 20)
 * NPC 3 (Event 12): 位置 (19, 23)
 * NPC 4 (Event 13): 位置 (20, 31)
 * NPC 5 (Event 14): 位置 (8, 32)
 * NPC 6 (Event 15): 位置 (8, 25)
 * 
 * ============================================================================
 * 自動啟動設定
 * ============================================================================
 * 
 * 1. AutoSelectNewGame: 自動選擇 New Game（true/false）
 *    - 設為 true: 進入標題畫面後自動選擇 New Game
 *    - 設為 false: 不自動選擇（預設）
 * 
 * 2. NewGameDelay: New Game 選擇延遲秒數（預設：2秒）
 *    - 進入標題畫面後等待幾秒再自動選擇
 * 
 * 3. AutoTransferToTrainingMap: 自動傳送到訓練地圖（true/false）
 *    - 設為 true: New Game 後自動傳送到訓練地圖（例如：forest town）
 *    - 設為 false: 不自動傳送（預設）
 * 
 * 4. TrainingMapId: 訓練地圖ID（例如：forest town 的地圖ID）
 *    - 設為目標地圖的ID
 * 
 * 5. TrainingMapX/Y: 傳送到訓練地圖的座標
 *    - 設為防詐騙助理附近的座標
 * 
 * 6. TransferDelay: 傳送延遲秒數（預設：2秒）
 *    - 進入地圖後等待幾秒再傳送
 * 
 * 7. AutoStartOnMap: 設定地圖ID，進入該地圖時自動啟動訓練
 *    - 設為 0: 不限定地圖
 *    - 設為訓練地圖ID: 只在訓練地圖自動啟動
 * 
 * 8. AutoStartSwitch: 設定開關ID，當開關ON時才自動啟動
 *    - 設為 0: 不使用開關
 * 
 * 9. AutoStartDelay: 訓練啟動延遲秒數（預設：3秒）
 * 
 * 終極自動化配置（推薦）：
 * - AutoSelectNewGame=true: 自動選擇 New Game
 * - NewGameDelay=2: 2秒後選擇
 * - AutoTransferToTrainingMap=true: 自動傳送到訓練地圖
 * - TrainingMapId=2: Forest Town 地圖ID
 * - TrainingMapX=5, TrainingMapY=9: Forest Town 座標
 * - TransferDelay=2: 2秒後傳送
 * - AutoSelectDialogue=true: 自動選擇對話選項
 * - DialogueSelectionDelay=1: 1秒後選擇
 * - AutoStartOnMap=2: 到達訓練地圖後自動啟動
 * - AutoStartSwitch=0: 不使用開關
 * - AutoStartDelay=3: 3秒後開始訓練
 * 
 * 效果：啟動 → 自動 New Game → 自動傳送 → 自動選擇對話 → 自動訓練
 * 
 * ============================================================================
 * 插件命令
 * ============================================================================
 * 
 * StartAutoMode       - 手動啟動自動訓練模式
 * StopAutoMode        - 停止自動訓練模式
 * ShowStats           - 顯示訓練統計
 * 
 * ============================================================================
 * 變量配置（與原系統相同）
 * ============================================================================
 * 
 * 變量 11-16: NPC1-6 當前騙局類型
 * 變量 20: 總對話次數
 * 變量 21: 當前模擬ID
 * 變量 22: 當前人設 (A/B/C/D)
 * 變量 24: 當前結果 (SUCCESS/FAILURE)
 * 變量 25: 人設索引 (0-3)
 * 變量 26: 已完成輪數
 * 變量 27: 對騙徒信任度
 * 變量 28: 對專家信任度
 */

(function() {
    'use strict';

    const parameters = PluginManager.parameters('SimulationTraining_Compatible');
    const API_URL = String(parameters['API_URL'] || 'http://localhost:8000');
    const AUTO_START_MAP = Number(parameters['AutoStartOnMap'] || 0);
    const AUTO_START_SWITCH = Number(parameters['AutoStartSwitch'] || 0);
    const AUTO_START_DELAY = Number(parameters['AutoStartDelay'] || 3);
    const AUTO_SELECT_NEW_GAME = String(parameters['AutoSelectNewGame'] || 'false').toLowerCase() === 'true';
    const NEW_GAME_DELAY = Number(parameters['NewGameDelay'] || 2);
    const AUTO_TRANSFER_TO_TRAINING_MAP = String(parameters['AutoTransferToTrainingMap'] || 'false').toLowerCase() === 'true';
    const TRAINING_MAP_ID = Number(parameters['TrainingMapId'] || 1);
    const TRAINING_MAP_X = Number(parameters['TrainingMapX'] || 10);
    const TRAINING_MAP_Y = Number(parameters['TrainingMapY'] || 10);
    const TRANSFER_DELAY = Number(parameters['TransferDelay'] || 2);
    const AUTO_SELECT_DIALOGUE = String(parameters['AutoSelectDialogue'] || 'false').toLowerCase() === 'true';
    const DIALOGUE_SELECTION_DELAY = Number(parameters['DialogueSelectionDelay'] || 1);
    
    // ============================================================================
    // 自定義對話窗口（參考 AutoScamBattle.js）
    // ============================================================================
    
    let customDialogueWindow = null;
    
    function Window_SimulationDialogue() {
        this.initialize.apply(this, arguments);
    }
    
    Window_SimulationDialogue.prototype = Object.create(Window_Base.prototype);
    Window_SimulationDialogue.prototype.constructor = Window_SimulationDialogue;
    
    Window_SimulationDialogue.prototype.initialize = function() {
        const width = Graphics.boxWidth;
        const height = Graphics.boxHeight;
        Window_Base.prototype.initialize.call(this, 0, 0, width, height);
        this._lines = [];
        this._scrollY = 0;
        this._maxVisibleLines = Math.floor((height - 72) / 44);
        this.opacity = 255;
        this.refresh();
    };
    
    Window_SimulationDialogue.prototype.addLine = function(text) {
        console.log('[Window] addLine 被調用, 輸入文本:', text.substring(0, 50) + '...');
        console.log('[Window] 當前行數:', this._lines.length);
        
        const maxCharsPerLine = 28;
        const wrappedLines = this.wrapText(text, maxCharsPerLine);
        
        console.log('[Window] 換行後行數:', wrappedLines.length);
        console.log('[Window] 換行後內容:', wrappedLines);
        
        wrappedLines.forEach(line => {
            this._lines.push(line);
        });
        
        if (this._lines.length > this._maxVisibleLines) {
            this._scrollY = this._lines.length - this._maxVisibleLines;
        }
        
        console.log('[Window] 添加後總行數:', this._lines.length);
        console.log('[Window] 調用 refresh()');
        
        this.refresh();
        
        console.log('[Window] refresh() 完成');
    };
    
    Window_SimulationDialogue.prototype.wrapText = function(text, maxChars) {
        const lines = [];
        let currentLine = '';
        let currentLength = 0;
        let controlCodes = '';
        
        let i = 0;
        while (i < text.length) {
            const char = text[i];
            
            if (char === '\n') {
                if (currentLine.trim() || currentLength > 0) {
                    if (controlCodes) currentLine += '\\C[0]';
                    lines.push(currentLine);
                }
                currentLine = controlCodes || '';
                currentLength = 0;
                i++;
                continue;
            }
            
            if (char === '\\' && i + 1 < text.length) {
                const nextChar = text[i + 1];
                if (nextChar === 'C' && text[i + 2] === '[') {
                    const endBracket = text.indexOf(']', i + 3);
                    if (endBracket !== -1) {
                        const controlCode = text.substring(i, endBracket + 1);
                        currentLine += controlCode;
                        if (controlCode === '\\C[0]') {
                            controlCodes = '';
                        } else {
                            controlCodes = controlCode;
                        }
                        i = endBracket + 1;
                        continue;
                    }
                }
            }
            
            currentLine += char;
            currentLength++;
            i++;
            
            if (currentLength >= maxChars) {
                if (controlCodes) currentLine += '\\C[0]';
                lines.push(currentLine);
                currentLine = controlCodes || '';
                currentLength = 0;
            }
        }
        
        if (currentLine.trim() || currentLength > 0) {
            lines.push(currentLine);
        }
        
        return lines.length > 0 ? lines : [''];
    };
    
    Window_SimulationDialogue.prototype.update = function() {
        Window_Base.prototype.update.call(this);
        
        if (this._lines.length > this._maxVisibleLines) {
            if (Input.isRepeated('up')) {
                this.scrollUp();
            } else if (Input.isRepeated('down')) {
                this.scrollDown();
            }
        }
    };
    
    Window_SimulationDialogue.prototype.scrollUp = function() {
        if (this._scrollY > 0) {
            this._scrollY--;
            this.refresh();
        }
    };
    
    Window_SimulationDialogue.prototype.scrollDown = function() {
        const maxScroll = Math.max(0, this._lines.length - this._maxVisibleLines);
        if (this._scrollY < maxScroll) {
            this._scrollY++;
            this.refresh();
        }
    };
    
    Window_SimulationDialogue.prototype.clear = function() {
        this._lines = [];
        this._scrollY = 0;
        this.refresh();
    };
    
    Window_SimulationDialogue.prototype.refresh = function() {
        console.log('[Window] refresh() 被調用');
        console.log('[Window] 總行數:', this._lines.length);
        console.log('[Window] 可見行數:', this._maxVisibleLines);
        console.log('[Window] 滾動位置:', this._scrollY);
        console.log('[Window] contents 存在:', !!this.contents);
        console.log('[Window] visible:', this.visible);
        console.log('[Window] opacity:', this.opacity);
        
        if (!this.contents) {
            console.error('[Window] ❌ contents 不存在！');
            return;
        }
        
        this.contents.clear();
        const lineHeight = 36;
        const lineSpacing = 2;
        let y = 0;
        
        const startIndex = Math.max(0, this._scrollY);
        const endIndex = Math.min(this._lines.length, startIndex + this._maxVisibleLines);
        
        console.log('[Window] 準備繪製行 ' + startIndex + ' 到 ' + endIndex);
        
        for (let i = startIndex; i < endIndex; i++) {
            console.log('[Window] 繪製第 ' + i + ' 行:', this._lines[i].substring(0, 50) + '...');
            this.resetFontSettings();
            this.drawTextEx(this._lines[i], 0, y);
            y += lineHeight + lineSpacing;
        }
        
        if (this._lines.length > this._maxVisibleLines) {
            const scrollPercent = Math.round((this._scrollY / (this._lines.length - this._maxVisibleLines)) * 100);
            const indicatorY = this.contents.height - lineHeight - 10;
            this.drawText(`▼ ${scrollPercent}%`, this.contents.width - 100, indicatorY, 100, 'right');
        }
        
        console.log('[Window] refresh() 完成');
    };
    
    // ============================================================================
    // 原有配置（完全兼容）
    // ============================================================================
    
    // 人設配置
    const PERSONAS = ['A', 'B', 'C', 'D'];
    const PERSONA_MAPPING = {
        'A': 'elderly',      // 陳老伯（長者）
        'B': 'average',      // 林小姐（一般市民）
        'C': 'overconfident', // 王先生（過度自信者）
        'D': 'average'       // 李同學（年輕學生）-> 映射到 average
    };
    
    // 10種騙局配置（與原系統相同）
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
        10: "假冒親友詐騙"
    };
    
    // NPC順序（與原系統相同）
    const NPC_IDS = [17, 16, 12, 13, 14, 15];
    
    // NPC位置（與原系統相同）
    const NPC_POSITIONS = {
        12: {x: 19, y: 23},
        13: {x: 20, y: 31},
        14: {x: 8, y: 32},
        15: {x: 8, y: 25},
        16: {x: 35, y: 20},
        17: {x: 18, y: 9}
    };
    
    // NPC路徑點（與原系統相同）
    const NPC_ROUTES = {
        17: [{x: 18, y: 10}],
        16: [{x: 20, y: 10}, {x: 20, y: 20}, {x: 34, y: 20}],
        12: [{x: 20, y: 20}, {x: 20, y: 23}],
        13: [{x: 20, y: 30}],
        14: [{x: 19, y: 30}, {x: 19, y: 34}, {x: 9, y: 34}, {x: 9, y: 32}],
        15: [{x: 9, y: 25}]
    };
    
    // ============================================================================
    // 全局狀態
    // ============================================================================
    
    let autoModeActive = false;
    let currentAutoNpcIndex = 0;
    let isMovingToNpc = false;
    let isInBattle = false;
    let currentWebSocket = null;
    let currentSimulation = null;
    let hasAutoStarted = false;  // 防止重複自動啟動
    let hasAutoTransferred = false;  // 防止重複自動傳送
    
    // ============================================================================
    // 插件命令註冊
    // ============================================================================
    
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'StartAutoMode') {
            startAutoMode();
        } else if (command === 'StopAutoMode') {
            stopAutoMode();
        } else if (command === 'ShowStats') {
            showStats();
        }
    };
    
    // ============================================================================
    // 初始化系統
    // ============================================================================
    
    function initializeSystem() {
        console.log('[系統] 初始化...');
        
        // 設定每個NPC的起始騙局
        for (let i = 0; i < NPC_IDS.length; i++) {
            const varId = 11 + i;
            if (!$gameVariables.value(varId)) {
                $gameVariables.setValue(varId, i + 1);
            }
        }
        
        // 初始化統計
        if (!$gameVariables.value(20)) {
            $gameVariables.setValue(20, 0);
        }
        
        // 初始化人設
        if (!$gameVariables.value(25)) {
            $gameVariables.setValue(25, 0);
            $gameVariables.setValue(22, 'A');
        }
        
        // 初始化已完成輪數
        if (!$gameVariables.value(26)) {
            $gameVariables.setValue(26, 0);
        }
        
        console.log('[系統] 初始化完成');
    }
    
    // ============================================================================
    // 自動訓練模式
    // ============================================================================
    
    function startAutoMode() {
        initializeSystem();
        
        autoModeActive = true;
        currentAutoNpcIndex = 0;
        isInBattle = false;
        
        console.log("========== 自動模式啟動 ==========");
        console.log("系統將自動與6個NPC依次對話");
        console.log("使用完整的 simulation_routes.py 流程");
        console.log("按StopAutoMode可隨時停止");
        console.log("================================");
        
        // 等待當前事件完全結束
        const waitForEventEnd = () => {
            console.log("[自動移動] 檢查事件狀態...");
            console.log("  - $gameMessage.isBusy():", $gameMessage.isBusy());
            console.log("  - $gameMap.isEventRunning():", $gameMap.isEventRunning());
            console.log("  - $gamePlayer.isMoving():", $gamePlayer.isMoving());
            
            if ($gameMessage.isBusy() || $gameMap.isEventRunning() || $gamePlayer.isMoving()) {
                console.log("  [自動移動] 等待事件結束...");
                setTimeout(waitForEventEnd, 300);
                return;
            }
            
            console.log("  [自動移動] ✅ 事件已結束，開始移動");
            setTimeout(() => {
                console.log("  [自動移動] 開始自動移動序列");
                moveToNextNpc();
            }, 500);
        };
        
        waitForEventEnd();
    }
    
    function stopAutoMode() {
        autoModeActive = false;
        isMovingToNpc = false;
        isInBattle = false;
        
        // 關閉 WebSocket
        if (currentWebSocket) {
            try {
                currentWebSocket.send('stop_now');
            } catch (e) {
                console.error('[停止] 發送停止指令失敗:', e);
            }
            currentWebSocket.close();
            currentWebSocket = null;
        }
        
        // 清除移動
        if ($gamePlayer.isMoveRouteForcing()) {
            $gamePlayer._moveRouteForcing = false;
            $gamePlayer._moveRoute = null;
            $gamePlayer._moveRouteIndex = 0;
        }
        
        $gameMessage.add("========== 自動模式已停止 ==========");
        $gameMessage.add("您已恢復控制權");
        
        console.log("自動模式已停止");
    }
    
    function moveToNextNpc() {
        if (!autoModeActive || isInBattle) return;
        
        // 檢查是否完成一輪
        if (currentAutoNpcIndex >= NPC_IDS.length) {
            const completedRounds = $gameVariables.value(26) + 1;
            $gameVariables.setValue(26, completedRounds);
            
            const nextPersona = PERSONAS[($gameVariables.value(25) + 1) % PERSONAS.length];
            const nextPersonaName = getPersonaName(nextPersona);
            
            $gameMessage.add("========== 一輪訓練完成 ==========");
            $gameMessage.add(`✓ 已完成第 ${completedRounds} 輪訓練`);
            $gameMessage.add(`✓ 已與所有 ${NPC_IDS.length} 個NPC對話完畢`);
            $gameMessage.add("");
            $gameMessage.add("【下一輪】");
            $gameMessage.add(`新人設：${nextPersonaName}`);
            $gameMessage.add(`準備返回第一個NPC繼續訓練...`);
            $gameMessage.add("========================");
            
            // 重置索引並繼續
            currentAutoNpcIndex = 0;
            
            // 輪換人設
            rotatePersona();
            
            // 3秒後返回第一個NPC
            setTimeout(() => {
                if (autoModeActive) {
                    console.log(`[自動訓練] 第${completedRounds}輪完成，返回NPC 1開始新一輪`);
                    moveToNextNpc();
                }
            }, 3000);
            return;
        }
        
        const npcId = NPC_IDS[currentAutoNpcIndex];
        const npcPos = NPC_POSITIONS[npcId];
        const route = NPC_ROUTES[npcId] || [];
        
        if (!npcPos) {
            console.error(`找不到NPC ${npcId}的位置`);
            currentAutoNpcIndex++;
            moveToNextNpc();
            return;
        }
        
        console.log(`自動移動到NPC${currentAutoNpcIndex + 1} (ID:${npcId})`);
        
        isMovingToNpc = true;
        
        const finalTarget = route.length > 0 ? route[route.length - 1] : npcPos;
        
        movePlayerViaRoute(route, finalTarget.x, finalTarget.y, () => {
            isMovingToNpc = false;
            console.log(`✓ 到達NPC旁邊`);
            
            setTimeout(() => {
                if (autoModeActive && !isInBattle) {
                    startSimulationForNPC(npcId);
                }
            }, 500);
        });
    }
    
    // ============================================================================
    // 移動邏輯
    // ============================================================================
    
    function movePlayerViaRoute(waypoints, finalX, finalY, callback) {
        if (waypoints.length === 0) {
            movePlayerToPosition(finalX, finalY, callback);
            return;
        }
        
        let currentWaypointIndex = 0;
        
        function moveToNextWaypoint() {
            if (!autoModeActive) {
                if (callback) callback();
                return;
            }
            
            if (currentWaypointIndex < waypoints.length) {
                const waypoint = waypoints[currentWaypointIndex];
                movePlayerToPosition(waypoint.x, waypoint.y, () => {
                    currentWaypointIndex++;
                    setTimeout(moveToNextWaypoint, 100);
                });
            } else {
                const player = $gamePlayer;
                if (player.x === finalX && player.y === finalY) {
                    if (callback) callback();
                } else {
                    movePlayerToPosition(finalX, finalY, callback);
                }
            }
        }
        
        moveToNextWaypoint();
    }
    
    function movePlayerToPosition(targetX, targetY, callback) {
        const player = $gamePlayer;
        const maxSteps = 100;
        let steps = 0;
        
        function tryMove() {
            if (!autoModeActive) {
                if (callback) callback();
                return;
            }
            
            if (steps++ > maxSteps) {
                console.error('[移動] 超過最大步數');
                if (callback) callback();
                return;
            }
            
            const dx = targetX - player.x;
            const dy = targetY - player.y;
            
            if (dx === 0 && dy === 0) {
                if (callback) callback();
                return;
            }
            
            let direction = 0;
            if (Math.abs(dx) > Math.abs(dy)) {
                direction = dx > 0 ? 6 : 4;
            } else {
                direction = dy > 0 ? 2 : 8;
            }
            
            if (direction > 0 && player.canPass(player.x, player.y, direction)) {
                player.moveStraight(direction);
            }
            
            setTimeout(() => {
                if (!player.isMoving()) {
                    tryMove();
                } else {
                    const checkMoving = setInterval(() => {
                        if (!player.isMoving()) {
                            clearInterval(checkMoving);
                            tryMove();
                        }
                    }, 50);
                }
            }, 50);
        }
        
        player.setMoveSpeed(4);
        tryMove();
    }
    
    // ============================================================================
    // 模擬管理（使用 simulation_routes.py）
    // ============================================================================
    
    function startSimulationForNPC(npcId) {
        console.log(`[模擬] 啟動 - NPC ${npcId}`);
        
        isInBattle = true;
        
        // 獲取當前騙局類型
        const npcIndex = NPC_IDS.indexOf(npcId);
        const varId = 11 + npcIndex;
        const scamType = $gameVariables.value(varId) || (npcIndex + 1);
        const scamTactic = SCAM_TYPES[scamType] || "冒充銀行客服詐騙";
        
        // 獲取當前人設
        const personaType = $gameVariables.value(22) || 'A';
        const victimPersona = PERSONA_MAPPING[personaType] || 'average';
        
        console.log(`  騙局: ${scamTactic}, 人設: ${personaType} (${victimPersona})`);
        
        // 保存當前模擬信息到變量（用於戰鬥場景）
        $gameVariables.setValue(30, scamType);  // 騙局類型ID
        $gameVariables.setValue(31, npcIndex);  // NPC索引
        
        // 調用 simulation API
        fetch(`${API_URL}/simulation/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                victim_persona: victimPersona,
                scam_tactic: scamTactic,
                mode: 'demo',  // 使用 demo 模式以有延遲
                auto_train: false
            })
        })
        .then(response => response.json())
        .then(data => {
            const simulationId = data.simulation_id;
            
            // 保存到全局變量，供其他函數使用
            currentSimulation = {
                id: simulationId,
                npcId: npcId,
                scamType: scamType,
                persona: personaType,
                victimPersona: victimPersona,
                scamTactic: scamTactic
            };
            
            $gameVariables.setValue(21, simulationId);
            
            console.log('[模擬] ✅ 模擬創建成功:', simulationId);
            console.log('[模擬] 保存的信息:', currentSimulation);
            
            // 進入戰鬥場景顯示對話
            setTimeout(() => {
                console.log('[模擬] 進入對話場景');
                
                // 設置戰鬥（使用假的戰鬥來顯示對話窗口）
                BattleManager.setup(1, false, false);
                $gamePlayer.makeEncounterCount();
                
                // 進入戰鬥場景（窗口創建後會自動調用 displaySimulationOpening 和 connectWebSocketForSimulation）
                SceneManager.push(Scene_Battle);
            }, 100);
        })
        .catch(error => {
            console.error('[模擬] 啟動失敗:', error);
            isInBattle = false;
            
            // 繼續下一個NPC
            setTimeout(() => {
                currentAutoNpcIndex++;
                moveToNextNpc();
            }, 1000);
        });
    }
    
    //=============================================================================
    // 顯示開場信息（同步模式）
    //=============================================================================
    
    function displaySimulationOpening() {
        console.log('[開場] 開始顯示開場信息');
        console.log('[開場] customDialogueWindow 存在:', !!customDialogueWindow);
        
        if (!customDialogueWindow) {
            console.error('[開場] ❌ customDialogueWindow 不存在！');
            return;
        }
        
        if (!currentSimulation) {
            console.error('[開場] ❌ currentSimulation 不存在！');
            return;
        }
        
        const { scamTactic, persona, victimPersona } = currentSimulation;
        const personaName = getPersonaName(persona);
        
        console.log('[開場] 騙局:', scamTactic);
        console.log('[開場] 人設:', personaName);
        
        // 清空窗口並添加開場文字
        customDialogueWindow.clear();
        customDialogueWindow.addLine('\\C[14]╔══════════════════════════╗\\C[0]');
        customDialogueWindow.addLine('\\C[14]║   防詐騙實戰訓練   ║\\C[0]');
        customDialogueWindow.addLine('\\C[14]╚══════════════════════════╝\\C[0]');
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine(`\\C[11]騙局類型：${scamTactic}\\C[0]`);
        customDialogueWindow.addLine(`\\C[3]您的角色：${personaName}\\C[0]`);
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine('\\C[6]旁白：模擬對話開始，請注意觀察...\\C[0]');
        customDialogueWindow.addLine('\\C[14]━━━━━━━━━━━━━━━━━━━━━━━━\\C[0]');
        customDialogueWindow.addLine('');
        
        console.log('[開場] ✅ 開場信息已添加到窗口');
        console.log('[開場] 窗口行數:', customDialogueWindow._lines.length);
    }
    
    //=============================================================================
    // 連接 WebSocket（從全局變量讀取）
    //=============================================================================
    
    function connectWebSocketForSimulation() {
        console.log('[WebSocket] 準備連接');
        console.log('[WebSocket] currentSimulation:', currentSimulation);
        
        if (!currentSimulation || !currentSimulation.id) {
            console.error('[WebSocket] ❌ 沒有有效的 simulation ID！');
            return;
        }
        
        const simulationId = currentSimulation.id;
        console.log('[WebSocket] 使用 simulation ID:', simulationId);
        
        connectWebSocket(simulationId);
    }
    
    function connectWebSocket(simulationId) {
        const wsUrl = `${API_URL.replace('http', 'ws')}/ws/simulation/${simulationId}`;
        
        console.log('[WebSocket] 準備連接...');
        console.log('[WebSocket] URL:', wsUrl);
        console.log('[WebSocket] customDialogueWindow 在連接時存在:', !!customDialogueWindow);
        
        currentWebSocket = new WebSocket(wsUrl);
        
        currentWebSocket.onopen = function() {
            console.log('[WebSocket] ✅ 連接成功！');
            console.log('[WebSocket] customDialogueWindow 在連接成功時存在:', !!customDialogueWindow);
        };
        
        currentWebSocket.onmessage = function(event) {
            console.log('[WebSocket] 收到原始消息:', event.data.substring(0, 100) + '...');
            try {
                const data = JSON.parse(event.data);
                handleWebSocketEvent(data);
            } catch (error) {
                console.error('[WebSocket] ❌ 解析消息失敗:', error);
            }
        };
        
        currentWebSocket.onerror = function(error) {
            console.error('[WebSocket] ❌ 錯誤:', error);
        };
        
        currentWebSocket.onclose = function() {
            console.log('[WebSocket] 連接已關閉');
        };
    }
    
    function handleWebSocketEvent(data) {
        const eventType = data.event_type;
        const payload = data.payload;
        
        console.log('[WebSocket] 收到事件 - 類型:', eventType);
        console.log('[WebSocket] Payload:', JSON.stringify(payload).substring(0, 100) + '...');
        
        switch (eventType) {
            case 'simulation_start':
                console.log('[WebSocket] 處理 simulation_start 事件');
                handleSimulationStart(payload);
                break;
            
            case 'dialogue':
                console.log('[WebSocket] 處理 dialogue 事件');
                handleDialogue(payload);
                break;
            
            case 'trust_update':
                console.log('[WebSocket] 處理 trust_update 事件');
                handleTrustUpdate(payload);
                break;
            
            case 'simulation_end':
                console.log('[WebSocket] 處理 simulation_end 事件');
                handleSimulationEnd(payload);
                break;
            
            default:
                console.warn('[WebSocket] ⚠️ 未知事件類型:', eventType);
                break;
        }
    }
    
    function handleSimulationStart(payload) {
        console.log('[模擬] 開始對話 - customDialogueWindow 存在:', !!customDialogueWindow);
        
        if (!customDialogueWindow) {
            console.error('[模擬] ❌ customDialogueWindow 不存在，無法顯示開場信息！');
            return;
        }
        
        const npcIndex = NPC_IDS.indexOf(currentSimulation.npcId);
        const scamName = SCAM_TYPES[currentSimulation.scamType] || '未知騙局';
        const personaName = getPersonaName(currentSimulation.persona);
        
        console.log('[模擬] 開場信息 - NPC:', npcIndex + 1, '騙局:', scamName, '人設:', personaName);
        
        customDialogueWindow.clear();
        customDialogueWindow.addLine('\\C[14]╔══════════════════════════╗\\C[0]');
        customDialogueWindow.addLine(`\\C[14]║   NPC${npcIndex + 1} 對話訓練   ║\\C[0]`);
        customDialogueWindow.addLine('\\C[14]╚══════════════════════════╝\\C[0]');
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine(`\\C[11]騙局類型：${scamName}\\C[0]`);
        customDialogueWindow.addLine(`\\C[3]您的人設：${personaName}\\C[0]`);
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine('\\C[6]旁白：對話即將開始...\\C[0]');
        customDialogueWindow.addLine('');
        
        console.log('[模擬] ✅ 開場信息已顯示');
    }
    
    function handleDialogue(payload) {
        const character = payload.character;
        const dialogue = payload.dialogue;
        
        console.log('='.repeat(60));
        console.log('[對話] 📨 收到對話事件');
        console.log('[對話] 角色:', character);
        console.log('[對話] 內容:', dialogue ? dialogue.substring(0, 50) + '...' : 'null');
        console.log('[對話] customDialogueWindow 存在:', !!customDialogueWindow);
        console.log('[對話] customDialogueWindow.visible:', customDialogueWindow ? customDialogueWindow.visible : 'N/A');
        console.log('[對話] customDialogueWindow._lines.length:', customDialogueWindow ? customDialogueWindow._lines.length : 'N/A');
        console.log('='.repeat(60));
        
        // 如果窗口不存在，說明時序有問題（不應該發生）
        if (!customDialogueWindow) {
            console.error('[對話] ❌ 窗口不存在！這不應該發生！');
            return;
        }
        
        // 根據角色顯示對話（帶顏色）
        let colorCode = '';
        let displayName = '';
        
        if (character === 'scammer') {
            colorCode = '\\C[2]';  // 紅色
            displayName = '詐騙犯';
        } else if (character === 'victim') {
            colorCode = '\\C[23]'; // 藍色
            displayName = '您';
        } else if (character === 'expert') {
            colorCode = '\\C[3]';  // 綠色
            displayName = '專家';
        }
        
        const line = `${colorCode}${displayName}：\\C[0]${dialogue}`;
        console.log('[對話] 準備添加對話行:', line.substring(0, 50) + '...');
        
        try {
            // 确保窗口可见
            if (!customDialogueWindow.visible) {
                console.log('[對話] ⚠️ 窗口不可見，設置為可見');
                customDialogueWindow.visible = true;
                customDialogueWindow.open();
            }
            
            // 添加对话
            customDialogueWindow.addLine(line);
            customDialogueWindow.addLine('');
            
            // 强制刷新（像信任度那样）
            customDialogueWindow.refresh();
            
            console.log('[對話] ✅ 對話已成功添加到窗口');
            console.log('[對話] 當前總行數:', customDialogueWindow._lines.length);
            console.log('[對話] 最後3行:',  customDialogueWindow._lines.slice(-3));
        } catch (error) {
            console.error('[對話] ❌ 添加對話失敗:', error);
            console.error('[對話] 錯誤堆棧:', error.stack);
        }
    }
    
    function handleTrustUpdate(payload) {
        const trustInScammer = Math.round(payload.trust_in_scammer);
        const trustInExpert = Math.round(payload.trust_in_expert);
        
        console.log('[信任度] 收到更新事件');
        console.log('[信任度] 詐騙犯:', trustInScammer, '%, 專家:', trustInExpert, '%');
        console.log('[信任度] customDialogueWindow 存在:', !!customDialogueWindow);
        console.log('[信任度] 當前行數:', customDialogueWindow ? customDialogueWindow._lines.length : 'N/A');
        
        $gameVariables.setValue(27, trustInScammer);
        $gameVariables.setValue(28, trustInExpert);
        
        // 在自定義窗口中顯示信任度
        if (customDialogueWindow) {
            customDialogueWindow.addLine('\\C[14]━━━━━━━━━━━━━━━━━━━━━━━━\\C[0]');
            customDialogueWindow.addLine(`\\C[11]信任度 - 詐騙犯: ${trustInScammer}% | 專家: ${trustInExpert}%\\C[0]`);
            customDialogueWindow.addLine('\\C[14]━━━━━━━━━━━━━━━━━━━━━━━━\\C[0]');
            customDialogueWindow.addLine('');
            
            console.log('[信任度] ✅ 信任度已顯示');
            console.log('[信任度] 更新後行數:', customDialogueWindow._lines.length);
        } else {
            console.error('[信任度] ❌ customDialogueWindow 不存在！');
        }
    }
    
    function handleSimulationEnd(payload) {
        const outcome = payload.outcome;
        const analysis = payload.analysis || {};
        const resultText = payload.result_text || '';
        
        console.log(`[模擬] 結束 - 結果: ${outcome}`);
        
        $gameVariables.setValue(24, outcome);
        
        // 在自定義窗口中顯示結果
        if (customDialogueWindow) {
            customDialogueWindow.addLine('');
            customDialogueWindow.addLine('\\C[14]╔══════════════════════════╗\\C[0]');
            customDialogueWindow.addLine('\\C[14]║      訓練結果評分      ║\\C[0]');
            customDialogueWindow.addLine('\\C[14]╚══════════════════════════╝\\C[0]');
            customDialogueWindow.addLine('');
            
            // 顯示結果
            if (outcome === 'SUCCESS') {
                customDialogueWindow.addLine('\\C[3]【結果】✓ 成功識破詐騙！\\C[0]');
            } else if (outcome === 'FAILURE') {
                customDialogueWindow.addLine('\\C[2]【結果】✗ 不幸被騙\\C[0]');
            } else {
                customDialogueWindow.addLine('\\C[6]【結果】⚠ 未明確判斷\\C[0]');
            }
            customDialogueWindow.addLine('');
            
            // 顯示最終信任度
            const trustInScammer = $gameVariables.value(27) || 0;
            const trustInExpert = $gameVariables.value(28) || 0;
            customDialogueWindow.addLine('\\C[11]最終信任度：\\C[0]');
            customDialogueWindow.addLine(`  詐騙犯：${trustInScammer}%`);
            customDialogueWindow.addLine(`  專家：${trustInExpert}%`);
            customDialogueWindow.addLine('');
            
            // 顯示分析
            if (analysis.key_factors && analysis.key_factors.length > 0) {
                customDialogueWindow.addLine('\\C[3]【關鍵因素】\\C[0]');
                analysis.key_factors.slice(0, 3).forEach(factor => {
                    customDialogueWindow.addLine(`  • ${factor}`);
                });
                customDialogueWindow.addLine('');
            }
            
            customDialogueWindow.addLine('\\C[6]旁白：3秒後返回地圖，前往下一個NPC...\\C[0]');
        }
        
        // 更新總對話次數
        const totalConversations = $gameVariables.value(20) + 1;
        $gameVariables.setValue(20, totalConversations);
        
        // 輪換騙局
        rotateScamForNPC(currentSimulation.npcId);
        
        // 延遲後退出戰鬥場景
        setTimeout(() => {
            console.log('[模擬] ==========================================');
            console.log('[模擬] 準備退出戰鬥場景並移動到下一個NPC');
            console.log('[模擬] autoModeActive:', autoModeActive);
            console.log('[模擬] currentAutoNpcIndex:', currentAutoNpcIndex);
            console.log('[模擬] ==========================================');
            
            // 關閉 WebSocket
            if (currentWebSocket) {
                currentWebSocket.close();
                currentWebSocket = null;
            }
            
            // 退出戰鬥場景
            if (SceneManager._scene instanceof Scene_Battle) {
                console.log('[模擬] 退出對話場景');
                BattleManager.abort();
                SceneManager.pop();
            }
            
            isInBattle = false;
            currentSimulation = null;
            
            // 移動到下一個NPC
            currentAutoNpcIndex++;
            console.log('[模擬] currentAutoNpcIndex 已增加至:', currentAutoNpcIndex);
            
            // 立即尝试移动，不等待
            if (autoModeActive) {
                console.log('[模擬] ✅ 立即觸發移動到下一個NPC');
                setTimeout(() => {
                    console.log('[模擬] 執行 moveToNextNpc()');
                    moveToNextNpc();
                }, 500);  // 短延迟
            } else {
                console.log('[模擬] ⚠️ autoModeActive = false，不移動');
            }
        }, 3000);
    }
    
    // ============================================================================
    // 輔助函數
    // ============================================================================
    
    function getPersonaName(personaType) {
        const PERSONA_NAMES = {
            'A': '陳老伯（長者）',
            'B': '林小姐（一般市民）',
            'C': '王先生（過度自信者）',
            'D': '李同學（年輕學生）'
        };
        return PERSONA_NAMES[personaType] || personaType;
    }
    
    // ============================================================================
    // 輪換邏輯
    // ============================================================================
    
    function rotateScamForNPC(npcId) {
        const npcIndex = NPC_IDS.indexOf(npcId);
        if (npcIndex === -1) return;
        
        const varId = 11 + npcIndex;
        let currentScam = $gameVariables.value(varId) || (npcIndex + 1);
        
        // 輪換到下一個騙局
        currentScam = (currentScam % 10) + 1;
        $gameVariables.setValue(varId, currentScam);
        
        console.log(`NPC ${npcId} 輪換到騙局 ${currentScam}`);
    }
    
    function rotatePersona() {
        let personaIndex = $gameVariables.value(25) || 0;
        personaIndex = (personaIndex + 1) % PERSONAS.length;
        
        $gameVariables.setValue(25, personaIndex);
        $gameVariables.setValue(22, PERSONAS[personaIndex]);
        
        console.log(`人設輪換到: ${PERSONAS[personaIndex]}`);
    }
    
    // ============================================================================
    // 統計顯示
    // ============================================================================
    
    function showStats() {
        const totalConversations = $gameVariables.value(20) || 0;
        const completedRounds = $gameVariables.value(26) || 0;
        const currentPersona = $gameVariables.value(22) || 'A';
        const currentPersonaName = getPersonaName(currentPersona);
        
        $gameMessage.add("========== 訓練統計 ==========");
        $gameMessage.add(`總對話次數: ${totalConversations}`);
        $gameMessage.add(`已完成輪數: ${completedRounds}`);
        $gameMessage.add(`每輪訓練: ${NPC_IDS.length} 個NPC`);
        $gameMessage.add(`總計: ${completedRounds * NPC_IDS.length} 次完整對話`);
        $gameMessage.add("");
        $gameMessage.add(`當前人設: ${currentPersonaName}`);
        $gameMessage.add(`訓練模式: ${autoModeActive ? '運行中 🔄' : '已停止'}`);
        $gameMessage.add("");
        $gameMessage.add("【各NPC當前騙局】");
        
        for (let i = 0; i < NPC_IDS.length; i++) {
            const npcId = NPC_IDS[i];
            const varId = 11 + i;
            const scamType = $gameVariables.value(varId) || (i + 1);
            const scamName = SCAM_TYPES[scamType];
            $gameMessage.add(`NPC ${i + 1}: ${scamName}`);
        }
        $gameMessage.add("========================");
    }
    
    // ============================================================================
    // 自動啟動系統
    // ============================================================================
    
    // Hook Scene_Map.start 以實現自動傳送和自動啟動
    const _Scene_Map_start = Scene_Map.prototype.start;
    Scene_Map.prototype.start = function() {
        _Scene_Map_start.call(this);
        
        // 調試日誌：顯示所有傳送相關配置
        console.log(`[傳送檢查] AUTO_TRANSFER_TO_TRAINING_MAP: ${AUTO_TRANSFER_TO_TRAINING_MAP}`);
        console.log(`[傳送檢查] hasAutoTransferred: ${hasAutoTransferred}`);
        console.log(`[傳送檢查] 當前地圖ID: ${$gameMap.mapId()}`);
        console.log(`[傳送檢查] 目標地圖ID: ${TRAINING_MAP_ID}`);
        
        // 優先檢查是否需要自動傳送
        if (AUTO_TRANSFER_TO_TRAINING_MAP && !hasAutoTransferred && $gameMap.mapId() !== TRAINING_MAP_ID) {
            hasAutoTransferred = true;
            
            console.log(`[自動傳送] ✅ 檢測到需要傳送到訓練地圖（ID: ${TRAINING_MAP_ID}）`);
            console.log(`[自動傳送] 當前地圖: ${$gameMap.mapId()}, 目標地圖: ${TRAINING_MAP_ID}`);
            
            // 顯示傳送提示（不使用 $gameMessage，避免阻塞）
            console.log("========================================");
            console.log("  🤖 防詐騙訓練系統 - 自動傳送");
            console.log("========================================");
            console.log(`目標地圖ID: ${TRAINING_MAP_ID}`);
            console.log(`目標座標: (${TRAINING_MAP_X}, ${TRAINING_MAP_Y})`);
            console.log(`${TRANSFER_DELAY}秒後自動傳送...`);
            
            // 立即執行傳送（不等待消息框）
            setTimeout(() => {
                console.log('[自動傳送] 正在執行傳送...');
                
                // 執行傳送
                $gamePlayer.reserveTransfer(TRAINING_MAP_ID, TRAINING_MAP_X, TRAINING_MAP_Y, 0, 0);
                
                console.log('[自動傳送] 傳送已預約');
            }, 100);  // 很短的延遲，幾乎立即執行
            
            return;  // 傳送後退出，等待下次 start 調用
        }
        
        // 檢查是否應該自動啟動訓練
        if (!hasAutoStarted && shouldAutoStart()) {
            hasAutoStarted = true;
            
            console.log('[自動啟動] 檢測到自動啟動條件，準備啟動訓練...');
            
            // 延遲啟動
            setTimeout(() => {
                if (!autoModeActive && !$gameMessage.isBusy()) {
                    console.log('[自動啟動] 正在啟動自動訓練模式...');
                    
                    $gameMessage.add("========================================");
                    $gameMessage.add("  🤖 防詐騙訓練系統");
                    $gameMessage.add("========================================");
                    $gameMessage.add("");
                    $gameMessage.add("檢測到自動啟動設定");
                    $gameMessage.add(`${AUTO_START_DELAY}秒後自動開始訓練...`);
                    $gameMessage.add("");
                    $gameMessage.add("系統將自動：");
                    $gameMessage.add("✓ 移動到所有6個NPC");
                    $gameMessage.add("✓ 進行完整對話訓練");
                    $gameMessage.add("✓ 自動循環無限訓練");
                    $gameMessage.add("");
                    $gameMessage.add("使用 StopAutoMode 可隨時停止");
                    $gameMessage.add("========================================");
                    
                    setTimeout(() => {
                        startAutoMode();
                    }, AUTO_START_DELAY * 1000);
                }
            }, 1000);
        }
    };
    
    // 檢查是否應該自動啟動
    function shouldAutoStart() {
        // 檢查地圖ID
        if (AUTO_START_MAP > 0 && $gameMap.mapId() === AUTO_START_MAP) {
            console.log(`[自動啟動] 地圖ID匹配: ${$gameMap.mapId()}`);
            
            // 如果設定了開關，還要檢查開關
            if (AUTO_START_SWITCH > 0) {
                const switchOn = $gameSwitches.value(AUTO_START_SWITCH);
                console.log(`[自動啟動] 開關${AUTO_START_SWITCH}狀態: ${switchOn}`);
                return switchOn;
            }
            
            return true;
        }
        
        // 如果只設定了開關（沒有設定地圖）
        if (AUTO_START_SWITCH > 0 && AUTO_START_MAP === 0) {
            const switchOn = $gameSwitches.value(AUTO_START_SWITCH);
            console.log(`[自動啟動] 僅開關模式 - 開關${AUTO_START_SWITCH}狀態: ${switchOn}`);
            return switchOn;
        }
        
        return false;
    }
    
    // Hook Scene_Map.stop 以重置自動啟動標記（當離開地圖時）
    const _Scene_Map_stop = Scene_Map.prototype.stop;
    Scene_Map.prototype.stop = function() {
        _Scene_Map_stop.call(this);
        
        // 如果離開了自動啟動地圖，重置標記
        if (AUTO_START_MAP > 0 && $gameMap.mapId() === AUTO_START_MAP) {
            hasAutoStarted = false;
        }
    };
    
    // Hook Game_Player.update 以確保自動模式在玩家停止移動後觸發
    const _Game_Player_update = Game_Player.prototype.update;
    let lastMoveCheckTime = 0;
    Game_Player.prototype.update = function(sceneActive) {
        const wasMoving = this.isMoving();
        _Game_Player_update.call(this, sceneActive);
        const isMovingNow = this.isMoving();
        
        // 如果自動模式已啟動，玩家剛停止移動，且不在戰鬥中
        if (autoModeActive && wasMoving && !isMovingNow && !isInBattle && !isMovingToNpc) {
            console.log('[自動移動] 檢測到玩家停止移動，檢查是否需要觸發自動移動...');
            
            // 檢查是否有消息或事件正在運行
            if (!$gameMessage.isBusy() && !$gameMap.isEventRunning()) {
                console.log('[自動移動] 條件滿足，延遲後觸發自動移動');
                setTimeout(() => {
                    if (autoModeActive && !isInBattle && !isMovingToNpc) {
                        console.log('[自動移動] ✅ 觸發自動移動到下一個NPC');
                        moveToNextNpc();
                    }
                }, 1000);  // 給玩家 1 秒的緩衝時間
            }
        }
        
        // 每 3 秒检查一次：如果自动模式启动，玩家不在移动，也不在战斗，强制触发移动
        const now = Date.now();
        if (autoModeActive && !isInBattle && !isMovingToNpc && !this.isMoving() && now - lastMoveCheckTime > 3000) {
            lastMoveCheckTime = now;
            if (!$gameMessage.isBusy() && !$gameMap.isEventRunning()) {
                console.log('[自動移動] 🔄 3秒定時檢查：強制觸發移動');
                moveToNextNpc();
            }
        }
    };
    
    // ============================================================================
    // 標題畫面自動選擇 New Game
    // ============================================================================
    
    if (AUTO_SELECT_NEW_GAME) {
        // Hook Scene_Title.create 以實現自動選擇
        const _Scene_Title_create = Scene_Title.prototype.create;
        Scene_Title.prototype.create = function() {
            _Scene_Title_create.call(this);
            
            console.log('[自動選擇] New Game 自動選擇已啟用');
            
            // 延遲自動選擇 New Game
            setTimeout(() => {
                if (SceneManager._scene instanceof Scene_Title) {
                    console.log('[自動選擇] 正在自動選擇 New Game...');
                    
                    // 自動選擇第一個選項（New Game）
                    if (this._commandWindow) {
                        this._commandWindow.select(0);  // 選擇第一個選項
                        
                        // 延遲後自動確認
                        setTimeout(() => {
                            if (SceneManager._scene instanceof Scene_Title && this._commandWindow) {
                                console.log('[自動選擇] 確認選擇 New Game');
                                this._commandWindow.processOk();  // 確認選擇
                            }
                        }, 500);
                    }
                }
            }, NEW_GAME_DELAY * 1000);
        };
        
        // 也可以 Hook commandNewGame 以添加日誌
        const _Scene_Title_commandNewGame = Scene_Title.prototype.commandNewGame;
        Scene_Title.prototype.commandNewGame = function() {
            console.log('[自動選擇] New Game 已選擇，開始新遊戲...');
            _Scene_Title_commandNewGame.call(this);
        };
    }
    
    // ============================================================================
    // Scene_Battle Hook - 創建自定義對話窗口
    // ============================================================================
    
    // Hook Scene_Battle.create - 最早的檢測點
    const _Scene_Battle_create = Scene_Battle.prototype.create;
    Scene_Battle.prototype.create = function() {
        // 檢查變量 30 判斷是否為模擬訓練
        const scamTypeId = $gameVariables.value(30);
        console.log('[對話場景] Scene_Battle.create - 變量30 =', scamTypeId);
        console.log('[對話場景] Scene_Battle.create - isInBattle =', isInBattle);
        
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            console.log('[對話場景] ✅ 確認為模擬訓練，設置 isSimulationBattle = true');
            isInBattle = true;  // 設置全局標志
        } else {
            console.log('[對話場景] ❌ 非模擬訓練，isInBattle =', isInBattle);
        }
        
        _Scene_Battle_create.call(this);
    };
    
    const _Scene_Battle_createAllWindows = Scene_Battle.prototype.createAllWindows;
    Scene_Battle.prototype.createAllWindows = function() {
        console.log('[對話場景] createAllWindows - isInBattle =', isInBattle);
        
        // 先調用原始函數完成初始化（重要！）
        _Scene_Battle_createAllWindows.call(this);
        
        // 使用全局標志而不是直接檢查變量
        if (isInBattle) {
            console.log('[對話場景] ✅ 檢測到模擬訓練，設置自定義對話窗口');
            
            // 隱藏所有默認戰鬥窗口
            if (this._partyCommandWindow) {
                this._partyCommandWindow.deactivate();
                this._partyCommandWindow.visible = false;
                this._partyCommandWindow.close();
                console.log('[對話場景] 隱藏 partyCommandWindow');
            }
            
            if (this._actorCommandWindow) {
                this._actorCommandWindow.deactivate();
                this._actorCommandWindow.visible = false;
                this._actorCommandWindow.close();
                console.log('[對話場景] 隱藏 actorCommandWindow');
            }
            
            if (this._statusWindow) {
                this._statusWindow.visible = false;
                this._statusWindow.close();
                console.log('[對話場景] 隱藏 statusWindow');
            }
            
            if (this._logWindow) {
                this._logWindow.visible = false;
                this._logWindow.opacity = 0;
                this._logWindow.close();
                this._logWindow.clear();
                console.log('[對話場景] 隱藏 logWindow');
            }
            
            // 創建自定義對話窗口
            customDialogueWindow = new Window_SimulationDialogue();
            this.addWindow(customDialogueWindow);
            
            console.log('[對話場景] ✅ 自定義對話窗口創建完成');
            console.log('[對話場景] customDialogueWindow 存在:', !!customDialogueWindow);
            console.log('[對話場景] customDialogueWindow 可見:', customDialogueWindow ? customDialogueWindow.visible : 'N/A');
            
            // 立即顯示開場信息（同步模式，像 AutoScamBattle 一樣）
            setTimeout(() => {
                console.log('[對話場景] ⏰ 500ms 後開始顯示開場信息');
                displaySimulationOpening();
                
                // 顯示開場後，再連接 WebSocket（延遲 1500ms）
                setTimeout(() => {
                    console.log('[對話場景] 📡 開始連接 WebSocket');
                    connectWebSocketForSimulation();
                }, 1500);
            }, 500);
        }
    };
    
    // 禁用默認戰鬥消息
    const _BattleManager_displayStartMessages = BattleManager.displayStartMessages;
    BattleManager.displayStartMessages = function() {
        if (isInBattle) {
            console.log('[對話場景] ✅ 攔截默認戰鬥訊息（isInBattle = true）');
            return;
        }
        _BattleManager_displayStartMessages.call(this);
    };
    
    const _BattleManager_startTurn = BattleManager.startTurn;
    BattleManager.startTurn = function() {
        if (isInBattle) {
            console.log('[對話場景] ✅ 攔截回合開始（isInBattle = true）');
            return;
        }
        _BattleManager_startTurn.call(this);
    };
    
    // 戰鬥結束清理
    const _Scene_Battle_terminate = Scene_Battle.prototype.terminate;
    Scene_Battle.prototype.terminate = function() {
        if (isInBattle) {
            console.log('[對話場景] ✅ 戰鬥結束，清理窗口（isInBattle = true）');
            
            if (customDialogueWindow) {
                customDialogueWindow.visible = false;
                customDialogueWindow.close();
                customDialogueWindow = null;
                console.log('[對話場景] customDialogueWindow 已清理');
            }
            
            // 清除變量
            $gameVariables.setValue(30, 0);
            $gameVariables.setValue(31, 0);
            
            // 注意：isInBattle 會在 handleSimulationEnd 中設置為 false
            console.log('[對話場景] 變量已清除');
        }
        
        _Scene_Battle_terminate.call(this);
    };
    
    // ============================================================================
    // 自動點擊對話框和選項
    // ============================================================================
    
    // Hook Window_Message 以實現自動點擊對話框
    const _Window_Message_update = Window_Message.prototype.update;
    Window_Message.prototype.update = function() {
        _Window_Message_update.call(this);
        
        // 如果對話框開啟且暫停等待輸入（使用 pause 屬性）
        if (this.isOpen() && this.pause && !$gameMessage.isChoice()) {
            // 自動點擊確認（延遲300ms避免太快）
            if (!this._autoClickTimer) {
                this._autoClickTimer = setTimeout(() => {
                    if (this.isOpen() && this.pause) {
                        console.log('[自動點擊] 自動確認對話框');
                        // 模擬按鍵輸入
                        Input._currentState['ok'] = true;
                        Input._latestButton = 'ok';
                        this._autoClickTimer = null;
                        
                        // 重置按鍵狀態
                        setTimeout(() => {
                            Input._currentState['ok'] = false;
                            Input._latestButton = null;
                        }, 100);
                    }
                }, 300);
            }
        } else {
            if (this._autoClickTimer) {
                clearTimeout(this._autoClickTimer);
                this._autoClickTimer = null;
            }
        }
    };
    
    if (AUTO_SELECT_DIALOGUE) {
        // Hook Window_ChoiceList 以實現自動選擇選項
        const _Window_ChoiceList_start = Window_ChoiceList.prototype.start;
        Window_ChoiceList.prototype.start = function() {
            _Window_ChoiceList_start.call(this);
            
            console.log('[自動選擇] 檢測到對話選項');
            
            // 延遲自動選擇第一個選項
            setTimeout(() => {
                if (this.isOpen() && this.active) {
                    console.log('[自動選擇] 自動選擇第一個選項...');
                    
                    // 選擇第一個選項（通常是"開始訓練"或類似選項）
                    this.select(0);
                    
                    // 延遲後自動確認
                    setTimeout(() => {
                        if (this.isOpen() && this.active) {
                            console.log('[自動選擇] 確認選擇');
                            this.processOk();
                        }
                    }, 500);
                }
            }, DIALOGUE_SELECTION_DELAY * 1000);
        };
        
        // Hook Window_EventItem 以實現自動選擇物品（如果需要）
        if (Window_EventItem) {
            const _Window_EventItem_onOk = Window_EventItem.prototype.onOk;
            Window_EventItem.prototype.onOk = function() {
                console.log('[自動選擇] 自動選擇物品');
                _Window_EventItem_onOk.call(this);
            };
        }
    }
    
})();

