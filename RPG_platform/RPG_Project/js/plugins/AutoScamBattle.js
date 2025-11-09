//=============================================================================
// AutoScamBattle.js
//=============================================================================

/*:
 * @plugindesc 自动防诈骗战斗系统 - 完全自动化的对话战斗
 * @author AI Assistant
 * 
 * @param API_URL
 * @desc 后端API地址
 * @default http://localhost:8000
 *
 * @help
 * 这个插件实现完全自动化的防诈骗战斗系统
 * 
 * 功能：
 * - 自动进入战斗
 * - 自动生成AI对话
 * - 自动显示在战斗消息中
 * - 自动评分和结束
 * - 完全不需要玩家操作
 */

(function() {
    
    const parameters = PluginManager.parameters('AutoScamBattle');
    const API_URL = String(parameters['API_URL'] || 'http://localhost:8000');
    const USE_MOCK_DATA = true; // 设为true使用模拟数据测试（先测试界面，确认无误后改为false连接真实API）
    
    // 战斗相关变量
    let isAutoScamBattle = false;
    let currentRound = 0;
    let maxRounds = 8;
    let sessionId = null;
    let currentScamType = null;
    let dialogueHistory = [];
    let battleNpcId = null;
    let customDialogueWindow = null; // 自定义对话窗口
    
    // 显示延迟设置（毫秒） - 让玩家有足够时间阅读
    const CHAR_DELAY = 2500;  // 每个角色之间的延迟（2.5秒）
    const ROUND_DELAY = 3000; // 每轮之间的延迟（3秒）
    const OPENING_DELAY = 4000; // 开场延迟（4秒）
    
    //=============================================================================
    // 自定义对话窗口
    //=============================================================================
    
    function Window_ScamDialogue() {
        this.initialize.apply(this, arguments);
    }
    
    Window_ScamDialogue.prototype = Object.create(Window_Base.prototype);
    Window_ScamDialogue.prototype.constructor = Window_ScamDialogue;
    
    Window_ScamDialogue.prototype.initialize = function() {
        const width = Graphics.boxWidth;
        const height = Graphics.boxHeight;
        Window_Base.prototype.initialize.call(this, 0, 0, width, height);
        this._lines = [];
        this._scrollY = 0;
        this.opacity = 255;
        this.refresh();
    };
    
    Window_ScamDialogue.prototype.addLine = function(text) {
        this._lines.push(text);
        // 自动滚动到底部
        if (this._lines.length > 20) {
            this._scrollY++;
        }
        this.refresh();
    };
    
    Window_ScamDialogue.prototype.clear = function() {
        this._lines = [];
        this._scrollY = 0;
        this.refresh();
    };
    
    Window_ScamDialogue.prototype.refresh = function() {
        this.contents.clear();
        const lineHeight = 36;
        let y = 0;
        
        // 从滚动位置开始显示
        for (let i = this._scrollY; i < this._lines.length; i++) {
            if (y >= this.contents.height - lineHeight) break;
            this.drawTextEx(this._lines[i], 0, y);
            y += lineHeight;
        }
    };
    
    //=============================================================================
    // Plugin Commands
    //=============================================================================
    
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        if (command === 'StartScamBattle') {
            const npcId = Number(args[0]);
            const scamTypeId = Number(args[1]);
            startScamBattle(npcId, scamTypeId);
        }
    };
    
    //=============================================================================
    // 开始诈骗战斗
    //=============================================================================
    
    function startScamBattle(npcId, scamTypeId) {
        console.log(`========== 开始防诈骗战斗 ==========`);
        console.log(`NPC ID: ${npcId}, 骗局类型: ${scamTypeId}`);
        
        battleNpcId = npcId;
        
        // 获取骗局信息
        currentScamType = getScamTypeInfo(scamTypeId);
        
        // 设置变量
        $gameVariables.setValue(30, scamTypeId);  // 当前骗局类型
        $gameVariables.setValue(31, 0);           // 当前回合
        $gameVariables.setValue(32, '');          // 对话历史
        
        // 计算敌人ID (5-14对应骗局1-10)
        const enemyId = 4 + scamTypeId;
        
        // 设置战斗标记
        isAutoScamBattle = true;
        currentRound = 0;
        dialogueHistory = [];
        
        console.log(`触发战斗: Enemy ID ${enemyId}`);
        
        // 触发战斗
        BattleManager.setup(1, false, false);  // troopId=1（需要创建）
        BattleManager._troopId = enemyId;
        $gamePlayer.makeEncounterCount();
        SceneManager.push(Scene_Battle);
    }
    
    //=============================================================================
    // 获取骗局信息
    //=============================================================================
    
    function getScamTypeInfo(scamTypeId) {
        const scamTypes = {
            1: { name: '假冒親友', role: '假冒親友者' },
            2: { name: '投資理財', role: '投資顧問' },
            3: { name: '網購詐騙', role: '賣家' },
            4: { name: '公務機關', role: '公務員' },
            5: { name: '愛情交友', role: '網友' },
            6: { name: '工作兼職', role: '招聘人員' },
            7: { name: '虛擬綁架', role: '綁匪' },
            8: { name: '中獎通知', role: '客服人員' },
            9: { name: '健康產品', role: '銷售員' },
            10: { name: '技術支援', role: '技術人員' }
        };
        return scamTypes[scamTypeId] || scamTypes[1];
    }
    
    //=============================================================================
    // 修改战斗开始
    //=============================================================================
    
    const _Scene_Battle_start = Scene_Battle.prototype.start;
    Scene_Battle.prototype.start = function() {
        _Scene_Battle_start.call(this);
        
        if (isAutoScamBattle) {
            console.log('防诈骗战斗开始');
            // 初始化会话
            initializeScamSession();
        }
    };
    
    //=============================================================================
    // 初始化会话
    //=============================================================================
    
    function initializeScamSession() {
        const personaType = $gameVariables.value(22) || 'B';
        
        // 显示开场介绍
        setTimeout(() => {
            console.log('[AutoScamBattle] 準備顯示開場文字...');
            if (customDialogueWindow) {
                console.log('[AutoScamBattle] 自定義窗口存在，添加文字...');
                console.log('  - 窗口可見:', customDialogueWindow.visible);
                console.log('  - 窗口不透明度:', customDialogueWindow.opacity);
                
                customDialogueWindow.clear();
                customDialogueWindow.addLine(`\\C[14]╔═══════════════════════════╗\\C[0]`);
                customDialogueWindow.addLine(`\\C[14]║   防詐騙實戰訓練   ║\\C[0]`);
                customDialogueWindow.addLine(`\\C[14]╚═══════════════════════════╝\\C[0]`);
                customDialogueWindow.addLine('');
                customDialogueWindow.addLine(`\\C[11]騙局類型：${currentScamType.name}\\C[0]`);
                customDialogueWindow.addLine(`\\C[11]騙徒角色：${currentScamType.role}\\C[0]`);
                customDialogueWindow.addLine('');
                if (USE_MOCK_DATA) {
                    customDialogueWindow.addLine(`\\C[6]旁白：【測試模式】使用模擬數據...\\C[0]`);
                } else {
                    customDialogueWindow.addLine(`\\C[6]旁白：現在開始模擬對話訓練...\\C[0]`);
                }
                customDialogueWindow.addLine('');
                
                console.log('[AutoScamBattle] 開場文字已添加');
                console.log('  - 文字行數:', customDialogueWindow._lines.length);
            } else {
                console.error('[AutoScamBattle] 自定義窗口不存在！無法顯示開場文字');
            }
        }, 500);
        
        if (USE_MOCK_DATA) {
            // 使用模拟数据
            sessionId = 'mock_session_' + Date.now();
            $gameVariables.setValue(21, sessionId);
            console.log(`[測試模式] 使用模擬會話: ${sessionId}`);
            
            setTimeout(() => {
                startAutoDialogue();
            }, OPENING_DELAY);
            return;
        }
        
        // 尝试连接真实API
        fetch(`${API_URL}/api/game/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                persona_type: personaType,
                scam_type: currentScamType.name
            })
        })
        .then(response => response.json())
        .then(data => {
            sessionId = data.session_id;
            $gameVariables.setValue(21, sessionId);
            console.log(`会话创建成功: ${sessionId}`);
            
            setTimeout(() => {
                startAutoDialogue();
            }, 2000);
        })
        .catch(error => {
            console.error("创建会话失败:", error);
            if (customDialogueWindow) {
                customDialogueWindow.addLine(`\\C[2]連接AI服務失敗！\\C[0]`);
                customDialogueWindow.addLine(`\\C[2]API端點: ${API_URL}/api/game/start\\C[0]`);
                customDialogueWindow.addLine(`\\C[6]提示：可在插件中開啟測試模式\\C[0]`);
            }
            setTimeout(() => {
                BattleManager.processVictory();
            }, 3000);
        });
    }
    
    //=============================================================================
    // 开始自动对话 - 4个角色系统
    //=============================================================================
    
    function startAutoDialogue() {
        if (currentRound >= maxRounds) {
            endScamBattle();
            return;
        }
        
        currentRound++;
        $gameVariables.setValue(31, currentRound);
        
        console.log(`========== 第 ${currentRound} 轮对话 ==========`);
        
        // 显示回合信息
        if (customDialogueWindow) {
            customDialogueWindow.addLine(`\\C[14]━━━ 第 ${currentRound}/8 轮对话 ━━━\\C[0]`);
            customDialogueWindow.addLine('');
            console.log(`[AutoScamBattle] 第${currentRound}輪標題已添加`);
        }
        
        // 生成受害人回应
        generateVictimResponse((victimMsg) => {
            // 1. 受骗人（主角）说话
            if (customDialogueWindow) {
                customDialogueWindow.addLine(`\\C[23]受騙人：\\C[0]${victimMsg}`);
                console.log(`[AutoScamBattle] 受騙人對話已添加: ${victimMsg.substring(0, 20)}...`);
            }
            
            setTimeout(() => {
                // 2. 骗子回应
                generateScammerResponse(victimMsg, (scammerMsg) => {
                    if (customDialogueWindow) {
                        customDialogueWindow.addLine(`\\C[2]${currentScamType.role}：\\C[0]${scammerMsg}`);
                        console.log(`[AutoScamBattle] 騙子對話已添加: ${scammerMsg.substring(0, 20)}...`);
                    }
                    
                    setTimeout(() => {
                        // 3. 助手分析
                        const helperComment = generateHelperComment(victimMsg, scammerMsg);
                        if (customDialogueWindow) {
                            customDialogueWindow.addLine(`\\C[3]防詐助手：\\C[0]${helperComment}`);
                            console.log(`[AutoScamBattle] 助手分析已添加: ${helperComment.substring(0, 20)}...`);
                        }
                        
                        setTimeout(() => {
                            // 4. 旁白说明
                            const narratorComment = generateNarratorComment(currentRound, victimMsg, scammerMsg);
                            if (customDialogueWindow) {
                                customDialogueWindow.addLine(`\\C[6]旁白：\\C[0]${narratorComment}`);
                                customDialogueWindow.addLine('');
                                console.log(`[AutoScamBattle] 旁白說明已添加: ${narratorComment.substring(0, 20)}...`);
                            }
                            
                            // 记录对话
                            dialogueHistory.push({ 
                                victim: victimMsg, 
                                scammer: scammerMsg,
                                helper: helperComment,
                                narrator: narratorComment
                            });
                            
                            // 检查是否应该结束
                            // 在测试模式下，始终进行完整8轮
                            if (!USE_MOCK_DATA && shouldEndDialogue(victimMsg, scammerMsg)) {
                                setTimeout(() => endScamBattle(), ROUND_DELAY);
                            } else {
                                // 继续下一轮
                                setTimeout(() => startAutoDialogue(), ROUND_DELAY);
                            }
                        }, CHAR_DELAY); // 旁白延迟
                    }, CHAR_DELAY); // 助手延迟
                });
            }, CHAR_DELAY); // 骗子延迟
        });
    }
    
    //=============================================================================
    // 生成助手评论
    //=============================================================================
    
    function generateHelperComment(victimMsg, scammerMsg) {
        // 检测关键词给出提示
        if (scammerMsg.includes('急用') || scammerMsg.includes('快') || scammerMsg.includes('馬上')) {
            return '⚠️ 注意！對方製造緊急感，這是詐騙常用手法。';
        } else if (scammerMsg.includes('轉帳') || scammerMsg.includes('匯款') || scammerMsg.includes('錢')) {
            return '🚨 警告！要求金錢交易，務必提高警覺！';
        } else if (victimMsg.includes('報警') || victimMsg.includes('警察')) {
            return '✅ 很好！提到報警是正確的防範方式。';
        } else if (victimMsg.includes('確認') || victimMsg.includes('視訊')) {
            return '✅ 做得好！要求確認身份是關鍵步驟。';
        } else {
            return '繼續保持警覺，注意對方話術。';
        }
    }
    
    //=============================================================================
    // 生成旁白说明
    //=============================================================================
    
    function generateNarratorComment(round, victimMsg, scammerMsg) {
        const comments = [
            '詐騙犯正在建立信任關係...',
            '注意觀察對方的話術特點。',
            '詐騙犯開始製造緊急情況。',
            '這是決定性的時刻，要保持冷靜。',
            '詐騙犯加大施壓力度。',
            '現在是識破騙局的關鍵時刻。',
            '對話接近尾聲，考慮你的最終決定。',
            '這是最後的考驗時刻。'
        ];
        
        return comments[round - 1] || '繼續觀察對話發展。';
    }
    
    //=============================================================================
    // 生成受害人回应
    //=============================================================================
    
    function generateVictimResponse(callback) {
        if (USE_MOCK_DATA) {
            // 模拟数据
            const mockResponses = [
                '喂？是誰啊？',
                '你的聲音聽起來不太對...',
                '我需要先確認一下你的身份',
                '這聽起來很可疑，我要掛斷了',
                '等等，讓我先報警確認',
                '不對勁，我不相信你',
                '我要向警察報案',
                '騙子！我已經識破你了！'
            ];
            const response = mockResponses[currentRound - 1] || '...'
            setTimeout(() => callback(response), 500);
            return;
        }
        
        fetch(`${API_URL}/api/game/message`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                message: '受害人回应',
                role: 'victim'
            })
        })
        .then(response => response.json())
        .then(data => {
            callback(data.response || data.message || '...');
        })
        .catch(error => {
            console.error("生成受害人回应失败:", error);
            callback('无法回应...');
        });
    }
    
    //=============================================================================
    // 生成骗子回应
    //=============================================================================
    
    function generateScammerResponse(victimMsg, callback) {
        if (USE_MOCK_DATA) {
            // 模拟数据
            const mockResponses = [
                '媽，是我啊！我在外面出事了，手機掉了...',
                '真的是我！我現在很急，你能先轉5萬給我嗎？',
                '相信我！我真的需要錢，不然就要出大事了！',
                '時間來不及了，你快點轉帳，我保證明天就還你！',
                '不要報警！這樣會害我的，你就幫幫我吧！',
                '我發誓這是真的，你不相信我嗎？',
                '好吧好吧，那算了...',
                '...'
            ];
            const response = mockResponses[currentRound - 1] || '...';
            setTimeout(() => callback(response), 500);
            return;
        }
        
        fetch(`${API_URL}/api/game/message`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                message: victimMsg,
                role: 'scammer'
            })
        })
        .then(response => response.json())
        .then(data => {
            callback(data.response || data.message || '...');
        })
        .catch(error => {
            console.error("生成骗子回应失败:", error);
            callback('...');
        });
    }
    
    //=============================================================================
    // 检查是否应该结束对话
    //=============================================================================
    
    function shouldEndDialogue(victimMsg, scammerMsg) {
        const endKeywords = ['报警', '警察', '不相信', '骗子', '挂断', '再见'];
        const combinedMsg = victimMsg + scammerMsg;
        return endKeywords.some(keyword => combinedMsg.includes(keyword));
    }
    
    //=============================================================================
    // 结束诈骗战斗
    //=============================================================================
    
    function endScamBattle() {
        console.log('========== 战斗结束，请求评分 ==========');
        
        if (USE_MOCK_DATA) {
            // 模拟评分数据
            const mockScore = {
                score: 75,
                analysis: '✓ 能夠質疑對方身份\n✓ 注意到對方話術可疑\n✗ 未立即掛斷電話\n✗ 差點就要提供個人信息',
                suggestions: '1. 遇到可疑電話立即掛斷\n2. 使用官方管道確認信息\n3. 不要在電話中透露個人信息\n4. 保持冷靜，理性判斷'
            };
            displayScore(mockScore);
            // 给玩家足够时间阅读评分（8秒）
            setTimeout(() => BattleManager.processVictory(), 8000);
            return;
        }
        
        // 请求AI评分
        fetch(`${API_URL}/api/game/end`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            displayScore(data);
            
            // 根据评分判定胜负
            const score = data.score || 50;
            if (score >= 70) {
                setTimeout(() => BattleManager.processVictory(), 2000);
            } else {
                setTimeout(() => BattleManager.processDefeat(), 2000);
            }
        })
        .catch(error => {
            console.error("获取评分失败:", error);
            if (customDialogueWindow) {
                customDialogueWindow.addLine(`\\C[2]評分系統錯誤\\C[0]`);
            }
            setTimeout(() => BattleManager.processVictory(), 2000);
        });
    }
    
    //=============================================================================
    // 显示评分
    //=============================================================================
    
    function displayScore(scoreData) {
        if (!customDialogueWindow) return;
        
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine(`\\C[14]╔═══════════════════════════╗\\C[0]`);
        customDialogueWindow.addLine(`\\C[14]║      訓練結果評分      ║\\C[0]`);
        customDialogueWindow.addLine(`\\C[14]╚═══════════════════════════╝\\C[0]`);
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine(`\\C[11]防詐得分：${scoreData.score || 0}/100\\C[0]`);
        customDialogueWindow.addLine('');
        
        if (scoreData.analysis) {
            customDialogueWindow.addLine(`\\C[3]助手：表現分析\\C[0]`);
            const analysisLines = scoreData.analysis.split('\n');
            analysisLines.forEach(line => {
                if (line.trim()) {
                    customDialogueWindow.addLine(`  ${line}`);
                }
            });
            customDialogueWindow.addLine('');
        }
        
        if (scoreData.suggestions) {
            customDialogueWindow.addLine(`\\C[3]助手：改進建議\\C[0]`);
            const suggestionLines = scoreData.suggestions.split('\n');
            suggestionLines.forEach(line => {
                if (line.trim()) {
                    customDialogueWindow.addLine(`  ${line}`);
                }
            });
            customDialogueWindow.addLine('');
        }
        
        customDialogueWindow.addLine(`\\C[6]旁白：訓練結束，返回地圖...\\C[0]`);
        
        console.log('评分显示完成');
    }
    
    //=============================================================================
    // 修改战斗界面
    //=============================================================================
    
    const _Scene_Battle_createAllWindows = Scene_Battle.prototype.createAllWindows;
    Scene_Battle.prototype.createAllWindows = function() {
        _Scene_Battle_createAllWindows.call(this);
        
        if (isAutoScamBattle) {
            console.log('[AutoScamBattle] 設置自定義戰鬥窗口...');
            
            // 隐藏默认窗口
            this._partyCommandWindow.deactivate();
            this._partyCommandWindow.visible = false;
            this._actorCommandWindow.deactivate();
            this._actorCommandWindow.visible = false;
            this._logWindow.visible = false; // 隐藏默认log窗口
            
            // 创建自定义对话窗口
            customDialogueWindow = new Window_ScamDialogue();
            this.addWindow(customDialogueWindow);
            
            console.log('[AutoScamBattle] 自定義對話窗口創建完成');
            console.log('  - 窗口存在:', !!customDialogueWindow);
            console.log('  - 窗口可見:', customDialogueWindow.visible);
        }
    };
    
    //=============================================================================
    // 禁用默认战斗消息
    //=============================================================================
    
    const _BattleManager_displayStartMessages = BattleManager.displayStartMessages;
    BattleManager.displayStartMessages = function() {
        if (isAutoScamBattle) {
            // 不显示默认的战斗开始消息
            return;
        }
        _BattleManager_displayStartMessages.call(this);
    };
    
    const _BattleManager_startTurn = BattleManager.startTurn;
    BattleManager.startTurn = function() {
        if (isAutoScamBattle) {
            // 防诈骗战斗不使用回合制
            return;
        }
        _BattleManager_startTurn.call(this);
    };
    
    const _Game_Battler_performAction = Game_Battler.prototype.performAction;
    Game_Battler.prototype.performAction = function(action) {
        if (isAutoScamBattle) {
            // 不显示动作动画
            return;
        }
        _Game_Battler_performAction.call(this, action);
    };
    
    //=============================================================================
    // 战斗结束清理
    //=============================================================================
    
    const _Scene_Battle_terminate = Scene_Battle.prototype.terminate;
    Scene_Battle.prototype.terminate = function() {
        if (isAutoScamBattle) {
            console.log('自动战斗结束，清理状态');
            isAutoScamBattle = false;
            currentRound = 0;
            sessionId = null;
            dialogueHistory = [];
            
            // 轮换骗局类型
            if (window.RotatingScamSystem) {
                window.RotatingScamSystem.rotateScam(battleNpcId);
            }
        }
        
        _Scene_Battle_terminate.call(this);
    };
    
})();
