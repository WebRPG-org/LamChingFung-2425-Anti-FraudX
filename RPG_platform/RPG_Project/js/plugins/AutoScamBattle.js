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
    const USE_MOCK_DATA = false; // ✅ 改為 false 以使用真實 AI 對話
    
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
        // 🔧 考慮更大行間距重新計算（36px 行高 + 8px 間距 = 44px 總高度）
        this._maxVisibleLines = Math.floor((height - 72) / 44);
        this.opacity = 255;
        this.refresh();
    };
    
    Window_ScamDialogue.prototype.addLine = function(text) {
        // 🔧 限制每行最多28個字，自動換行
        const maxCharsPerLine = 28;
        const wrappedLines = this.wrapText(text, maxCharsPerLine);
        
        wrappedLines.forEach(line => {
            this._lines.push(line);
        });
        
        // 🔧 自動滾動：當行數超過可見範圍時滾動
        if (this._lines.length > this._maxVisibleLines) {
            this._scrollY = this._lines.length - this._maxVisibleLines;
        }
        
        this.refresh();
    };
    
    // 🔧 新增：文字自動換行函數（改進版，正確處理控制碼、原始換行和強制換行）
    Window_ScamDialogue.prototype.wrapText = function(text, maxChars) {
        const lines = [];
        let currentLine = '';
        let currentLength = 0;
        let controlCodes = ''; // 儲存當前有效的控制碼
        
        let i = 0;
        while (i < text.length) {
            const char = text[i];
            
            // 🔧 關鍵修正：檢測原始換行符號 \n，但不產生空行
            if (char === '\n') {
                // 遇到換行符號，保存當前行（如果有內容）
                if (currentLine.trim() || currentLength > 0) {
                    if (controlCodes) {
                        currentLine += '\\C[0]';
                    }
                    lines.push(currentLine);
                }
                
                // 重置新行，但保留顏色控制碼，不添加空行
                currentLine = controlCodes || '';
                currentLength = 0;
                i++;
                continue;
            }
            
            // 檢查是否為控制字符
            if (char === '\\' && i + 1 < text.length) {
                const nextChar = text[i + 1];
                
                // 處理 \C[xx] 顏色控制碼
                if (nextChar === 'C' && text[i + 2] === '[') {
                    const endBracket = text.indexOf(']', i + 3);
                    if (endBracket !== -1) {
                        const controlCode = text.substring(i, endBracket + 1);
                        currentLine += controlCode;
                        
                        // 如果是重置顏色 \C[0]，清除控制碼記錄
                        if (controlCode === '\\C[0]') {
                            controlCodes = '';
                        } else {
                            controlCodes = controlCode; // 記錄當前顏色
                        }
                        
                        i = endBracket + 1;
                        continue;
                    }
                }
            }
            
            // 普通字符
            currentLine += char;
            currentLength++;
            i++;
            
            // 檢查是否達到最大字符數需要換行
            if (currentLength >= maxChars) {
                // 如果當前有顏色控制碼，在行尾重置顏色
                if (controlCodes) {
                    currentLine += '\\C[0]';
                }
                lines.push(currentLine);
                
                // 新行開始時，如果之前有顏色控制碼，在行首重新應用
                currentLine = controlCodes || '';
                currentLength = 0;
            }
        }
        
        // 添加最後一行（如果有內容）
        if (currentLine.trim() || currentLength > 0) {
            lines.push(currentLine);
        }
        
        return lines.length > 0 ? lines : [''];
    };
    
    // 🔧 新增：手動滾動功能
    Window_ScamDialogue.prototype.update = function() {
        Window_Base.prototype.update.call(this);
        
        // 方向鍵上下滾動
        if (this._lines.length > this._maxVisibleLines) {
            if (Input.isRepeated('up')) {
                this.scrollUp();
            } else if (Input.isRepeated('down')) {
                this.scrollDown();
            }
        }
    };
    
    Window_ScamDialogue.prototype.scrollUp = function() {
        if (this._scrollY > 0) {
            this._scrollY--;
            this.refresh();
        }
    };
    
    Window_ScamDialogue.prototype.scrollDown = function() {
        const maxScroll = Math.max(0, this._lines.length - this._maxVisibleLines);
        if (this._scrollY < maxScroll) {
            this._scrollY++;
            this.refresh();
        }
    };
    
    Window_ScamDialogue.prototype.clear = function() {
        this._lines = [];
        this._scrollY = 0;
        this.refresh();
    };
    
    Window_ScamDialogue.prototype.refresh = function() {
        this.contents.clear();
        const lineHeight = 36; // 行高
        const lineSpacing = 2;  // 🔧 增加行間距至 2px，確保不重疊
        let y = 0;
        
        // 🔧 從滾動位置開始顯示，確保顯示最新內容
        const startIndex = Math.max(0, this._scrollY);
        const endIndex = Math.min(this._lines.length, startIndex + this._maxVisibleLines);
        
        for (let i = startIndex; i < endIndex; i++) {
            // 🔧 每次繪製前重置字體設定，避免殘留
            this.resetFontSettings();
            this.drawTextEx(this._lines[i], 0, y);
            y += lineHeight + lineSpacing; // 使用行高加間距
        }
        
        // 🔧 顯示滾動指示器（位置調整，避免與文字重疊）
        if (this._lines.length > this._maxVisibleLines) {
            const scrollPercent = Math.round((this._scrollY / (this._lines.length - this._maxVisibleLines)) * 100);
            const indicatorY = this.contents.height - lineHeight - 10;
            this.drawText(`▼ ${scrollPercent}%`, this.contents.width - 100, indicatorY, 100, 'right');
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
        console.log(`NPC ID: ${npcId}, 骗局类型ID: ${scamTypeId}`);
        
        battleNpcId = npcId;
        
        // 获取骗局信息
        currentScamType = getScamTypeInfo(scamTypeId);
        console.log(`骗局信息: ${currentScamType.name} - ${currentScamType.role}`);
        
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
    // 获取骗局信息（與 RotatingScamSystem.js 的 SCAM_TYPES 對應）
    //=============================================================================
    
    function getScamTypeInfo(scamTypeId) {
        const scamTypes = {
            1: { name: '投資詐騙', role: '投資顧問' },
            2: { name: '假警察詐騙', role: '刑警' },
            3: { name: '交友詐騙', role: '網友' },
            4: { name: '網購詐騙', role: '賣家' },
            5: { name: '假中獎詐騙', role: '客服人員' },
            6: { name: '假貸款詐騙', role: '貸款專員' },
            7: { name: '假客服詐騙', role: '客服專員' },
            8: { name: '刷單兼職詐騙', role: '招聘人員' },
            9: { name: '虛假招聘詐騙', role: '人資主管' },
            10: { name: '假冒親友詐騙', role: '你的朋友' }
        };
        return scamTypes[scamTypeId] || scamTypes[1];
    }
    
    //=============================================================================
    // 修改战斗开始
    //=============================================================================
    
    const _Scene_Battle_start = Scene_Battle.prototype.start;
    Scene_Battle.prototype.start = function() {
        _Scene_Battle_start.call(this);
        
        // 🔧 優先從 BattleManager 讀取（場景切換時不會被重置）
        const scamTypeId = BattleManager._scamTypeId || $gameVariables.value(30);
        
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            console.log('[AutoScamBattle] 偵測到詐騙戰鬥，scamTypeId =', scamTypeId);
            isAutoScamBattle = true;
            
            // 從變量或 BattleManager 獲取騙局信息
            currentScamType = getScamTypeInfo(scamTypeId);
            console.log(`[AutoScamBattle] 騙局: ${currentScamType.name}, 角色: ${currentScamType.role}`);
            
            // 初始化会话
            initializeScamSession();
        } else {
            console.log('[AutoScamBattle] 非詐騙戰鬥，scamTypeId =', scamTypeId);
        }
    };
    
    //=============================================================================
    // 初始化会话
    //=============================================================================
    
    function initializeScamSession() {
        // 🔧 優先從 BattleManager 讀取 session_id（由 RotatingScamSystem 設置）
        const existingSessionId = BattleManager._scamSessionId || $gameVariables.value(21);
        
        if (existingSessionId && existingSessionId !== '' && existingSessionId !== 0) {
            // 使用已存在的 session
            sessionId = existingSessionId;
            console.log(`[AutoScamBattle] 使用現有會話: ${sessionId}`);
            console.log(`[AutoScamBattle] 來源: ${BattleManager._scamSessionId ? 'BattleManager' : '$gameVariables'}`);
            
            // 顯示開場並開始對話
            displayOpeningAndStart();
            return;
        }
        
        // 如果沒有現有 session，才創建新的
        console.log(`[AutoScamBattle] 沒有現有會話，創建新會話...`);
        
        // 動態選擇受害者角色（從變數22讀取，如果沒有則隨機選擇）
        let personaType = $gameVariables.value(22);
        
        // 如果沒有設定，根據NPC ID輪換角色
        if (!personaType || personaType === '') {
            const npcIndex = battleNpcId ? (battleNpcId % 3) : 0;
            const personas = ['elderly', 'average', 'overconfident'];
            personaType = personas[npcIndex];
            
            console.log(`[AutoScamBattle] 自動選擇受害者角色: ${personaType} (基於NPC ID: ${battleNpcId})`);
        }
        
        // 儲存當前角色類型到變數
        $gameVariables.setValue(22, personaType);
        
        if (USE_MOCK_DATA) {
            // 使用模拟数据
            sessionId = 'mock_session_' + Date.now();
            $gameVariables.setValue(21, sessionId);
            console.log(`[測試模式] 使用模擬會話: ${sessionId}`);
            
            displayOpeningAndStart();
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
            console.log(`[AutoScamBattle] 會話創建成功: ${sessionId}`);
            
            displayOpeningAndStart();
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
    // 顯示開場文字並開始對話（提取為獨立函數）
    //=============================================================================
    
    function displayOpeningAndStart() {
        const personaType = $gameVariables.value(22) || 'A';
        const personaNames = {
            'A': '陳老伯（長者）',
            'B': '林小姐（一般市民）',
            'C': '王先生（過度自信者）',
            'D': '李同學（年輕學生）',
            'elderly': '陳婆婆（長者）',
            'average': '一般市民',
            'overconfident': '過度自信者'
        };
        const personaName = personaNames[personaType] || personaType;
        
        // 显示开场介绍
        setTimeout(() => {
            console.log('[AutoScamBattle] 準備顯示開場文字...');
            if (customDialogueWindow) {
                console.log('[AutoScamBattle] 自定義窗口存在，添加文字...');
                console.log('  - 窗口可見:', customDialogueWindow.visible);
                console.log('  - 窗口不透明度:', customDialogueWindow.opacity);
                
                customDialogueWindow.clear();
                customDialogueWindow.addLine(`\\C[14]╔══════════════════════════╗\\C[0]`);
                customDialogueWindow.addLine(`\\C[14]║   防詐騙實戰訓練   ║\\C[0]`);
                customDialogueWindow.addLine(`\\C[14]╚══════════════════════════╝\\C[0]`);
                customDialogueWindow.addLine('');
                customDialogueWindow.addLine(`\\C[11]騙局類型：${currentScamType.name}\\C[0]`);
                customDialogueWindow.addLine(`\\C[11]騙徒角色：${currentScamType.role}\\C[0]`);
                customDialogueWindow.addLine(`\\C[3]受害者角色：${personaName}\\C[0]`);
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
            
            // 延遲後開始對話
            setTimeout(() => {
                startAutoDialogue();
            }, USE_MOCK_DATA ? OPENING_DELAY : 2000);
        }, 500);
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
        
        // 🔧 使用與 RotatingScamSystem 相同的 API 格式
        const personaType = $gameVariables.value(22) || 'A';
        const history = dialogueHistory || [];
        const lastScammerMsg = history.length > 0 ? history[history.length - 1].scammer : currentScamType.name;
        const victimPrompt = `騙徒剛剧說：「${lastScammerMsg}」\n\n請以你的角色身份自然回應。注意：這是一個${currentScamType.name}的騙局，但你現在可能還不確定是否為詐騙。請根據你的人設特點來回應。`;
        
        console.log(`[AutoScamBattle] 發送受害者訊息 (session: ${sessionId})`);
        
        fetch(`${API_URL}/api/game/message`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                message: victimPrompt,
                target_ai: "AI-A",  // 使用受害者AI
                persona_type: personaType
            })
        })
        .then(response => response.json())
        .then(data => {
            const reply = data.reply || "我考慮一下...";
            console.log(`[AutoScamBattle] 受害者回應: ${reply.substring(0, 30)}...`);
            callback(reply);
        })
        .catch(error => {
            console.error("生成受害人回应失败:", error);
            const fallbacks = {
                'A': '呃...我唔太明白，你可唔可以講清楚啲？',
                'B': '等等，我需要確認一下這個資訊...',
                'C': '我知道啦，但我想先了解清楚細節。',
                'D': '這個...聽起來有點奇怪，你能證明嗎？'
            };
            callback(fallbacks[personaType] || "無法回應...");
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
        
        // 🔧 使用與 RotatingScamSystem 相同的 API 格式
        const personaType = $gameVariables.value(22) || 'A';
        
        // 構建騙徒 prompt
        const scammerPrompt = `受害者剛剛說：「${victimMsg}」\n\n你是${currentScamType.role}，正在進行${currentScamType.name}。\n\n請根據受害者的回應，繼續你的詐騙行為。記住要保持角色一致性，不要暴露自己是騙徒。用廣東話回應，保持真實感。`;
        
        console.log(`[AutoScamBattle] 發送騙子訊息 (session: ${sessionId})`);
        
        fetch(`${API_URL}/api/game/message`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId,
                message: scammerPrompt,
                target_ai: "AI-D",  // 使用詐騙者AI
                persona_type: personaType
            })
        })
        .then(response => response.json())
        .then(data => {
            const reply = data.reply || "那你再考慮看看...";
            console.log(`[AutoScamBattle] 騙子回應: ${reply.substring(0, 30)}...`);
            callback(reply);
        })
        .catch(error => {
            console.error("生成骗子回应失败:", error);
            callback('那你再考慮看看...');
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
            // 評分顯示後，processVictory 會在 displayScore 內部的 setTimeout 中調用（10秒後）
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
            // displayScore 內部會在10秒後自動關閉對話框
            
            // 根據評分判定勝負（但不立即執行，讓玩家有時間閱讀）
            const score = data.score || 50;
            if (score >= 70) {
                // processVictory 會在 displayScore 的 setTimeout 中執行
                console.log('評分 >= 70，將在對話框關閉後判定勝利');
            } else {
                // 如果需要失敗處理，也在 setTimeout 後執行
                console.log('評分 < 70，將在對話框關閉後判定失敗');
            }
        })
        .catch(error => {
            console.error("获取评分失败:", error);
            if (customDialogueWindow) {
                customDialogueWindow.addLine(`\\C[2]評分系統錯誤\\C[0]`);
                customDialogueWindow.addLine(`\\C[6]旁白：訓練結束，返回地圖...\\C[0]`);
            }
            // 錯誤情況下也要10秒後關閉
            setTimeout(() => {
                console.log('錯誤處理：10秒後關閉對話框');
                if (customDialogueWindow) {
                    customDialogueWindow.close();
                }
                if (SceneManager._scene instanceof Scene_Battle) {
                    SceneManager._scene.terminate();
                    SceneManager.pop();
                }
            }, 10000);
        });
    }
    
    //=============================================================================
    // 显示评分
    //=============================================================================
    
    function displayScore(scoreData) {
        if (!customDialogueWindow) return;
        
        customDialogueWindow.addLine('');
        customDialogueWindow.addLine(`\\C[14]╔══════════════════════════╗\\C[0]`);
        customDialogueWindow.addLine(`\\C[14]║      訓練結果評分      ║\\C[0]`);
        customDialogueWindow.addLine(`\\C[14]╚══════════════════════════╝\\C[0]`);
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
        
        // 10秒後自動關閉對話框
        setTimeout(() => {
            console.log('10秒已到，準備關閉對話框並返回地圖');
            if (customDialogueWindow) {
                customDialogueWindow.close();
            }
            // 確保戰鬥正確結束
            if (SceneManager._scene instanceof Scene_Battle) {
                SceneManager._scene.terminate();
                SceneManager.pop();
            }
        }, 10000);
    }
    
    //=============================================================================
    // 修改战斗界面（最早觸發點）
    //=============================================================================
    
    const _Scene_Battle_create = Scene_Battle.prototype.create;
    Scene_Battle.prototype.create = function() {
        // 🔧 **優先從 BattleManager 讀取**（場景切換時不會被重置）
        const scamTypeId = BattleManager._scamTypeId || $gameVariables.value(30);
        console.log('[AutoScamBattle] Scene_Battle.create - BattleManager._scamTypeId =', BattleManager._scamTypeId);
        console.log('[AutoScamBattle] Scene_Battle.create - 變量30 =', $gameVariables.value(30));
        console.log('[AutoScamBattle] Scene_Battle.create - 最終使用 scamTypeId =', scamTypeId);
        
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            console.log('[AutoScamBattle] ✅ 確認為詐騙戰鬥，準備攔截默認介面');
            isAutoScamBattle = true;
            currentScamType = getScamTypeInfo(scamTypeId);
            
            // 從 BattleManager 恢復 session 數據
            if (BattleManager._scamSessionId) {
                sessionId = BattleManager._scamSessionId;
                console.log('[AutoScamBattle] 從 BattleManager 恢復 session:', sessionId);
            }
        }
        
        _Scene_Battle_create.call(this);
    };
    
    const _Scene_Battle_createAllWindows = Scene_Battle.prototype.createAllWindows;
    Scene_Battle.prototype.createAllWindows = function() {
        _Scene_Battle_createAllWindows.call(this);
        
        const scamTypeId = $gameVariables.value(30);
        console.log('[AutoScamBattle] createAllWindows - 變量30 =', scamTypeId, ', isAutoScamBattle =', isAutoScamBattle);
        
        if (isAutoScamBattle) {
            console.log('[AutoScamBattle] 設置自定義戰鬥窗口...');
            
            // 隐藏所有默认窗口
            if (this._partyCommandWindow) {
                this._partyCommandWindow.deactivate();
                this._partyCommandWindow.visible = false;
                this._partyCommandWindow.close();
            }
            
            if (this._actorCommandWindow) {
                this._actorCommandWindow.deactivate();
                this._actorCommandWindow.visible = false;
                this._actorCommandWindow.close();
            }
            
            if (this._statusWindow) {
                this._statusWindow.visible = false;
                this._statusWindow.close();
            }
            
            // 🔧 完全隱藏 log 窗口（這個顯示 "BAT EMERGED"）
            if (this._logWindow) {
                this._logWindow.visible = false;
                this._logWindow.opacity = 0;
                this._logWindow.close();
                this._logWindow.clear();
                console.log('[AutoScamBattle] Log 窗口已完全隱藏');
            }
            
            // 创建自定义对话窗口
            customDialogueWindow = new Window_ScamDialogue();
            this.addWindow(customDialogueWindow);
            
            console.log('[AutoScamBattle] 自定義對話窗口創建完成');
            console.log('  - 窗口存在:', !!customDialogueWindow);
            console.log('  - 窗口可見:', customDialogueWindow.visible);
        } else {
            console.log('[AutoScamBattle] ❌ 非詐騙戰鬥，使用默認戰鬥介面');
        }
    };
    
    //=============================================================================
    // 禁用默认战斗消息（更早攔截）
    //=============================================================================
    
    const _BattleManager_displayStartMessages = BattleManager.displayStartMessages;
    BattleManager.displayStartMessages = function() {
        // 🔧 檢查變量30判斷是否為詐騙戰鬥
        const scamTypeId = $gameVariables.value(30);
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            console.log('[AutoScamBattle] 攔截默認戰鬥訊息 (變量30 =', scamTypeId, ')');
            // 不显示默认的战斗开始消息
            return;
        }
        _BattleManager_displayStartMessages.call(this);
    };
    
    const _BattleManager_startTurn = BattleManager.startTurn;
    BattleManager.startTurn = function() {
        // 🔧 檢查變量30判斷是否為詐騙戰鬥
        const scamTypeId = $gameVariables.value(30);
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            // 防诈骗战斗不使用回合制
            return;
        }
        _BattleManager_startTurn.call(this);
    };
    
    const _Game_Battler_performAction = Game_Battler.prototype.performAction;
    Game_Battler.prototype.performAction = function(action) {
        // 🔧 檢查變量30判斷是否為詐騙戰鬥
        const scamTypeId = $gameVariables.value(30);
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            // 不显示动作动画
            return;
        }
        _Game_Battler_performAction.call(this, action);
    };
    
    //=============================================================================
    // 攔截戰鬥訊息窗口（隱藏 "BAT EMERGED"）
    //=============================================================================
    
    const _Window_BattleLog_displayAction = Window_BattleLog.prototype.displayAction;
    Window_BattleLog.prototype.displayAction = function(subject, item) {
        const scamTypeId = $gameVariables.value(30);
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            console.log('[AutoScamBattle] 攔截戰鬥動作訊息');
            return;
        }
        _Window_BattleLog_displayAction.call(this, subject, item);
    };
    
    const _Window_BattleLog_startTurn = Window_BattleLog.prototype.startTurn;
    Window_BattleLog.prototype.startTurn = function() {
        const scamTypeId = $gameVariables.value(30);
        if (scamTypeId && scamTypeId >= 1 && scamTypeId <= 10) {
            console.log('[AutoScamBattle] 攔截回合開始訊息');
            return;
        }
        _Window_BattleLog_startTurn.call(this);
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
            
            // 🔧 隱藏並清理 log 窗口（防止返回地圖時顯示 "BAT EMERGED"）
            if (this._logWindow) {
                this._logWindow.visible = false;
                this._logWindow.opacity = 0;
                this._logWindow.close();
                this._logWindow.clear();
                console.log('[AutoScamBattle] 戰鬥結束，Log 窗口已隱藏');
            }
            
            // 🔧 隱藏自定義對話窗口
            if (customDialogueWindow) {
                customDialogueWindow.visible = false;
                customDialogueWindow.close();
                customDialogueWindow = null;
                console.log('[AutoScamBattle] 戰鬥結束，自定義對話窗口已關閉');
            }
            
            // 轮换骗局类型
            if (window.RotatingScamSystem) {
                window.RotatingScamSystem.rotateScam(battleNpcId);
            }
        }
        
        _Scene_Battle_terminate.call(this);
    };
    
})();
