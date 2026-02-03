/*:
 * @target MZ
 * @plugindesc Simulation 觀察器 v1.0 - 完整三方對話系統
 * @author AI-Agent Team
 * 
 * @help SimulationViewer.js
 * 
 * 這個插件讓 RPG Maker 使用 backend 的完整 simulation 系統
 * 包含 Victim, Scammer, Expert 三方 AI 對話
 * 
 * @command startSimulation
 * @text 啟動完整模擬
 * @desc 啟動三方 AI 對話模擬（使用 simulation_routes.py）
 * 
 * @arg victimPersona
 * @text 受騙者類型
 * @type select
 * @option elderly (長者)
 * @value elderly
 * @option average (一般市民)
 * @value average
 * @option overconfident (過度自信)
 * @value overconfident
 * @default average
 * 
 * @arg scamTactic
 * @text 詐騙類型
 * @type string
 * @default WhatsApp 對話詐騙
 * 
 * @arg mode
 * @text 模式
 * @type select
 * @option fast (快速)
 * @value fast
 * @option demo (演示)
 * @value demo
 * @default fast
 * 
 * @arg simulationIdVar
 * @text Simulation ID 變量
 * @desc 用於存儲 simulation ID 的遊戲變量 ID
 * @type variable
 * @default 20
 */

(() => {
    'use strict';

    const pluginName = 'SimulationViewer';
    const API_BASE = 'http://localhost:8000';

    // 全局狀態
    let currentSimulationId = null;
    let pollingInterval = null;
    let lastEventSeq = 0;
    let allEvents = [];

    // 註冊命令
    PluginManager.registerCommand(pluginName, 'startSimulation', async (args) => {
        const victimPersona = String(args.victimPersona || 'average');
        const scamTactic = String(args.scamTactic || 'WhatsApp 對話詐騙');
        const mode = String(args.mode || 'fast');
        const simulationIdVar = Number(args.simulationIdVar || 20);

        await startSimulation(victimPersona, scamTactic, mode, simulationIdVar);
    });

    // ========== 核心功能 ==========

    async function startSimulation(victimPersona, scamTactic, mode, simulationIdVar) {
        $gameMessage.add('正在啟動 AI 三方對話模擬...');
        $gameMessage.add(`受騙者: ${victimPersona}`);
        $gameMessage.add(`詐騙類型: ${scamTactic}`);
        $gameMessage.add(`模式: ${mode}`);

        try {
            // 1. 啟動 simulation
            const response = await fetch(`${API_BASE}/simulation/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    victim_persona: victimPersona,
                    scam_tactic: scamTactic,
                    mode: mode,
                    auto_train: true  // 自動生成訓練數據
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            currentSimulationId = data.simulation_id;

            // 存儲到遊戲變量
            $gameVariables.setValue(simulationIdVar, currentSimulationId);

            $gameMessage.add('✓ Simulation 已啟動');
            $gameMessage.add(`ID: ${currentSimulationId.substring(0, 8)}...`);

            // 2. 重置狀態
            lastEventSeq = 0;
            allEvents = [];

            // 3. 開始輪詢事件
            startEventPolling();

            // 4. 切換到觀察場景
            SceneManager.push(Scene_SimulationViewer);

        } catch (error) {
            console.error('啟動 Simulation 失敗:', error);
            $gameMessage.add('✗ 啟動失敗: ' + error.message);
        }
    }

    function startEventPolling() {
        // 清理舊的輪詢
        stopEventPolling();

        console.log('[SimulationViewer] 開始輪詢事件...');

        // 每 2 秒輪詢一次
        pollingInterval = setInterval(async () => {
            if (currentSimulationId) {
                await fetchSimulationEvents();
            } else {
                console.log('[SimulationViewer] 沒有活動的 simulation');
            }
        }, 2000);
    }

    function stopEventPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            console.log('[SimulationViewer] 停止輪詢事件');
        }
    }

    async function fetchSimulationEvents() {
        try {
            const url = `${API_BASE}/simulation/events/${currentSimulationId}?since_seq=${lastEventSeq}`;
            const response = await fetch(url);

            if (!response.ok) {
                console.error('[SimulationViewer] 獲取事件失敗:', response.status);
                return;
            }

            const data = await response.json();
            const events = data.events || [];
            lastEventSeq = data.next_seq || lastEventSeq;

            // 處理新事件
            if (events.length > 0) {
                console.log(`[SimulationViewer] 收到 ${events.length} 個新事件`);
                
                events.forEach(event => {
                    allEvents.push(event);
                    handleSimulationEvent(event);
                });
            }

        } catch (error) {
            console.error('[SimulationViewer] 輪詢事件失敗:', error);
        }
    }

    function handleSimulationEvent(event) {
        const eventType = event.event;
        const eventData = event.data || {};

        console.log('[Event]', eventType, eventData);

        // 更新場景（如果在觀察場景中）
        if (SceneManager._scene instanceof Scene_SimulationViewer) {
            SceneManager._scene.handleEvent(eventType, eventData);
        }
    }

    // ========== Simulation 觀察場景 ==========

    class Scene_SimulationViewer extends Scene_MenuBase {
        create() {
            super.create();
            
            this._dialogues = [];
            this._trustData = { trust_in_scammer: 50, trust_in_expert: 50 };
            this._currentRound = 0;
            this._status = '啟動中...';
            this._outcome = '';
            this._metrics = {};
            
            this.createWindows();
        }

        createWindows() {
            // 對話視窗（上半部）
            const dialogueRect = new Rectangle(10, 10, Graphics.boxWidth - 20, 340);
            this._dialogueWindow = new Window_SimulationDialogue(dialogueRect);
            this.addWindow(this._dialogueWindow);

            // 狀態視窗（左下）
            const statusRect = new Rectangle(10, 360, 300, 220);
            this._statusWindow = new Window_SimulationStatus(statusRect);
            this.addWindow(this._statusWindow);

            // 性能視窗（右下）
            const metricsRect = new Rectangle(320, 360, Graphics.boxWidth - 330, 220);
            this._metricsWindow = new Window_SimulationMetrics(metricsRect);
            this.addWindow(this._metricsWindow);
        }

        handleEvent(eventType, eventData) {
            switch (eventType) {
                case 'simulation_start':
                    this.onSimulationStart(eventData);
                    break;

                case 'agent_message':
                    this.onAgentMessage(eventData);
                    break;

                case 'trust_update':
                    this.onTrustUpdate(eventData);
                    break;

                case 'round_end':
                    this.onRoundEnd(eventData);
                    break;

                case 'simulation_end':
                    this.onSimulationEnd(eventData);
                    break;

                case 'recorder_analysis':
                    this.onRecorderAnalysis(eventData);
                    break;

                case 'error':
                    this.onError(eventData);
                    break;
            }
        }

        onSimulationStart(data) {
            this._status = '運行中';
            this._dialogues = [];
            this._statusWindow.setStatus(this._status);
            console.log('[Scene] Simulation 開始');
        }

        onAgentMessage(data) {
            const speaker = data.agent || '未知';
            const message = data.message || '';
            const round = data.round || 0;

            this._dialogues.push({ speaker, message, round });
            
            // 限制對話數量
            if (this._dialogues.length > 15) {
                this._dialogues.shift();
            }
            
            this._dialogueWindow.setDialogues(this._dialogues);
        }

        onTrustUpdate(data) {
            this._trustData = data;
            this._statusWindow.updateTrust(data);
        }

        onRoundEnd(data) {
            this._currentRound = data.round || 0;
            this._statusWindow.setRound(this._currentRound);
            
            if (data.metrics) {
                this._metrics = data.metrics;
                this._metricsWindow.updateMetrics(data.metrics);
            }
        }

        onSimulationEnd(data) {
            this._status = '已完成';
            this._outcome = data.outcome || 'UNKNOWN';
            this._statusWindow.setStatus(this._status);
            this._statusWindow.setOutcome(this._outcome);
            
            console.log('[Scene] Simulation 結束:', data.outcome);
            
            // 顯示完成消息
            setTimeout(() => {
                $gameMessage.add('=== Simulation 完成 ===');
                $gameMessage.add(`結果: ${this._outcome}`);
                $gameMessage.add(`總輪數: ${this._currentRound}`);
            }, 1000);
        }

        onRecorderAnalysis(data) {
            console.log('[Scene] RecorderAgent 分析:', data);
            
            // 顯示評分
            setTimeout(() => {
                if (data.scammer_performance) {
                    const sp = data.scammer_performance;
                    $gameMessage.add(`騙徒評分: ${sp.overall_score}/100`);
                    
                    if (sp.key_successes && sp.key_successes.length > 0) {
                        $gameMessage.add(`成功: ${sp.key_successes.join(', ')}`);
                    }
                }
                
                if (data.expert_performance) {
                    const ep = data.expert_performance;
                    $gameMessage.add(`專家評分: ${ep.overall_score}/100`);
                    
                    if (ep.key_successes && ep.key_successes.length > 0) {
                        $gameMessage.add(`成功: ${ep.key_successes.join(', ')}`);
                    }
                }
            }, 2000);
        }

        onError(data) {
            this._status = '錯誤';
            this._statusWindow.setStatus(this._status);
            console.error('[Scene] Simulation 錯誤:', data);
            
            $gameMessage.add('✗ 錯誤: ' + (data.message || '未知錯誤'));
        }

        update() {
            super.update();
            
            // 按 X/Esc 返回
            if (Input.isTriggered('cancel') || Input.isTriggered('menu')) {
                if (this._status === '已完成' || this._status === '錯誤') {
                    stopEventPolling();
                    SceneManager.pop();
                } else {
                    // 確認是否要退出
                    const confirmed = confirm('Simulation 還在運行中，確定要退出嗎？');
                    if (confirmed) {
                        stopEventPolling();
                        SceneManager.pop();
                    }
                }
            }
        }

        terminate() {
            super.terminate();
            // 場景結束時不停止輪詢，因為可能切換到其他場景
        }
    }

    // ========== 對話視窗 ==========

    class Window_SimulationDialogue extends Window_Scrollable {
        initialize(rect) {
            super.initialize(rect);
            this._dialogues = [];
            this.refresh();
        }

        setDialogues(dialogues) {
            this._dialogues = dialogues;
            this.refresh();
        }

        refresh() {
            this.contents.clear();
            
            const lineHeight = this.lineHeight();
            let y = 0;

            // 標題
            this.changeTextColor(ColorManager.systemColor());
            this.drawText('=== 三方 AI 實時對話 ===', 0, y, this.width - 40);
            this.resetTextColor();
            y += lineHeight * 1.5;

            // 繪製對話
            this._dialogues.forEach((dialogue) => {
                const speaker = dialogue.speaker;
                const message = dialogue.message;
                const round = dialogue.round;

                // 顏色編碼
                let speakerColor = 0;
                if (speaker.includes('騙徒')) speakerColor = 2;   // 紅色
                if (speaker.includes('專家')) speakerColor = 3;   // 綠色
                if (speaker.includes('受騙者')) speakerColor = 6;  // 黃色

                // 回合標記
                this.changeTextColor(ColorManager.dimColor1());
                this.drawText(`[R${round}]`, 0, y, 40);
                
                // 發言者
                this.changeTextColor(ColorManager.textColor(speakerColor));
                this.drawText(speaker, 45, y, 100);
                this.resetTextColor();
                this.drawText(':', 145, y, 10);
                
                y += lineHeight;

                // 消息內容（分行）
                const lines = this.splitMessageToLines(message, this.width - 60);
                lines.forEach(line => {
                    this.drawText(line, 20, y, this.width - 40);
                    y += lineHeight;
                });

                y += lineHeight * 0.3;  // 對話間距
            });

            // 更新滾動區域
            this.paint();
        }

        splitMessageToLines(message, maxWidth) {
            const words = message.split('');
            const lines = [];
            let currentLine = '';

            for (const word of words) {
                if (this.textWidth(currentLine + word) <= maxWidth) {
                    currentLine += word;
                } else {
                    if (currentLine) lines.push(currentLine);
                    currentLine = word;
                }
            }

            if (currentLine) lines.push(currentLine);
            return lines.length > 0 ? lines : [message];
        }
    }

    // ========== 狀態視窗 ==========

    class Window_SimulationStatus extends Window_Base {
        initialize(rect) {
            super.initialize(rect);
            this._status = '等待中';
            this._round = 0;
            this._outcome = '';
            this._trustInScammer = 50;
            this._trustInExpert = 50;
            this.refresh();
        }

        setStatus(status) {
            this._status = status;
            this.refresh();
        }

        setRound(round) {
            this._round = round;
            this.refresh();
        }

        setOutcome(outcome) {
            this._outcome = outcome;
            this.refresh();
        }

        updateTrust(data) {
            this._trustInScammer = data.trust_in_scammer || 50;
            this._trustInExpert = data.trust_in_expert || 50;
            this.refresh();
        }

        refresh() {
            this.contents.clear();
            
            const lineHeight = this.lineHeight();
            let y = 0;

            // 標題
            this.changeTextColor(ColorManager.systemColor());
            this.drawText('=== 狀態監控 ===', 0, y, this.width - 40);
            this.resetTextColor();
            y += lineHeight * 1.5;

            // 狀態
            const statusColor = this._status === '已完成' ? 3 : 
                              this._status === '錯誤' ? 2 : 0;
            this.changeTextColor(ColorManager.textColor(statusColor));
            this.drawText(`${this._status}`, 80, y, 150);
            this.resetTextColor();
            this.drawText('狀態:', 0, y, 80);
            y += lineHeight;

            // 回合
            this.drawText('回合:', 0, y, 80);
            this.drawText(`${this._round}`, 80, y, 50);
            y += lineHeight;

            // 結果
            if (this._outcome) {
                this.drawText('結果:', 0, y, 80);
                const outcomeColor = this._outcome === 'SUCCESS' ? 3 :
                                   this._outcome === 'FAILURE' ? 2 : 6;
                this.changeTextColor(ColorManager.textColor(outcomeColor));
                this.drawText(this._outcome, 80, y, 150);
                this.resetTextColor();
                y += lineHeight;
            }

            y += lineHeight * 0.5;

            // 信任度儀表
            this.changeTextColor(ColorManager.systemColor());
            this.drawText('--- 信任度 ---', 0, y, this.width);
            this.resetTextColor();
            y += lineHeight;

            this.drawText('對騙徒:', 0, y, 70);
            this.drawGauge(70, y + 4, 150, this._trustInScammer / 100,
                ColorManager.textColor(2), ColorManager.gaugeBackColor());
            this.drawText(`${this._trustInScammer}%`, 230, y, 50);
            y += lineHeight;

            this.drawText('對專家:', 0, y, 70);
            this.drawGauge(70, y + 4, 150, this._trustInExpert / 100,
                ColorManager.textColor(3), ColorManager.gaugeBackColor());
            this.drawText(`${this._trustInExpert}%`, 230, y, 50);
        }
    }

    // ========== 性能指標視窗 ==========

    class Window_SimulationMetrics extends Window_Base {
        initialize(rect) {
            super.initialize(rect);
            this._metrics = { scammer: {}, expert: {} };
            this.refresh();
        }

        updateMetrics(metrics) {
            this._metrics = metrics || { scammer: {}, expert: {} };
            this.refresh();
        }

        refresh() {
            this.contents.clear();
            
            const lineHeight = this.lineHeight();
            let y = 0;

            // 標題
            this.changeTextColor(ColorManager.systemColor());
            this.drawText('=== 性能指標 ===', 0, y, this.width - 40);
            this.resetTextColor();
            y += lineHeight * 1.5;

            // 騙徒指標
            this.changeTextColor(ColorManager.textColor(2));
            this.drawText('騙徒表現:', 0, y, this.width);
            this.resetTextColor();
            y += lineHeight;

            const s = this._metrics.scammer || {};
            this.drawSmallBar('說服力', s.persuasiveness || 50, y);
            y += lineHeight * 0.8;
            this.drawSmallBar('可信度', s.credibility || 50, y);
            y += lineHeight * 1.2;

            // 專家指標
            this.changeTextColor(ColorManager.textColor(3));
            this.drawText('專家表現:', 0, y, this.width);
            this.resetTextColor();
            y += lineHeight;

            const e = this._metrics.expert || {};
            this.drawSmallBar('干預效果', e.intervention_effectiveness || 50, y);
            y += lineHeight * 0.8;
            this.drawSmallBar('清晰度', e.clarity || 50, y);
        }

        drawSmallBar(label, value, y) {
            const labelWidth = 80;
            const barWidth = this.width - labelWidth - 80;
            const barHeight = 12;

            // 標籤
            this.drawText(label, 10, y, labelWidth);

            // 進度條
            const barX = labelWidth + 10;
            const barY = y + (this.lineHeight() - barHeight) / 2;

            // 背景
            this.contents.fillRect(barX, barY, barWidth, barHeight, 'rgba(0,0,0,0.6)');

            // 填充
            const fillWidth = Math.floor(barWidth * (value / 100));
            let fillColor;
            if (value >= 70) fillColor = '#00ff00';
            else if (value >= 40) fillColor = '#ffaa00';
            else fillColor = '#ff0000';
            
            this.contents.fillRect(barX + 2, barY + 2, fillWidth - 4, barHeight - 4, fillColor);

            // 數值
            this.drawText(`${value}`, barX + barWidth + 5, y, 50);
        }
    }

    // 導出到全局
    window.Scene_SimulationViewer = Scene_SimulationViewer;
    window.SimulationViewerAPI = {
        start: startSimulation,
        stop: stopEventPolling,
        getCurrentId: () => currentSimulationId,
        getAllEvents: () => allEvents
    };

})();

