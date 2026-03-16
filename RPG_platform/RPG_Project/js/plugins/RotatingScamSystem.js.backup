/*:
 * @plugindesc 輪換詐騙系統 - 6個NPC輪流使用10種不同騙局
 * @author AI-Agent Team
 * 
 * @param API_URL
 * @desc AI後台API地址
 * @default http://localhost:8000
 * 
 * @help
 * ============================================================================
 * 功能說明
 * ============================================================================
 * 
 * 6個NPC騙徒，每個NPC會輪流使用10種不同的騙局：
 * 
 * NPC 1 (EV012): 起始騙局1 → 騙局2 → 騙局3 → ... → 騙局10 → 循環
 * NPC 2 (EV013): 起始騙局2 → 騙局3 → 騙局4 → ... → 騙局1 → 循環
 * NPC 3 (EV014): 起始騙局3 → 騙局4 → 騙局5 → ... → 騙局2 → 循環
 * NPC 4 (EV015): 起始騙局4 → 騙局5 → 騙局6 → ... → 騙局3 → 循環
 * NPC 5 (EV016): 起始騙局5 → 騙局6 → 騙局7 → ... → 騙局4 → 循環
 * NPC 6 (EV017): 起始騙局6 → 騙局7 → 騙局8 → ... → 騙局5 → 循環
 * 
 * 每個NPC都會經歷完整的10種騙局循環！
 * 
 * ============================================================================
 * 插件命令
 * ============================================================================
 * 
 * StartRotatingMode       - 啟動輪換模式（初始化系統）
 * StartAutoMode           - 啟動自動模式（自動與6個NPC依次對話）
 * StopAutoMode            - 停止自動模式
 * TalkToScammer 12        - 與NPC對話（會使用當前騙局）
 * CheckScamType 12        - 查看NPC當前使用的騙局
 * ResetRotation           - 重置所有NPC的騙局輪換
 * ShowStats               - 顯示統計數據
 * 
 * ============================================================================
 * 自動模式說明
 * ============================================================================
 * 
 * 啟動自動模式後，系統將：
 * 1. 自動移動玩家到每個NPC處
 * 2. 自動與NPC對話（8輪對話）
 * 3. 對話完成後自動移動到下一個NPC
 * 4. 完成6個NPC後自動開始下一輪
 * 5. 使用StopAutoMode可隨時停止
 * 
 * ============================================================================
 * 變量配置
 * ============================================================================
 * 
 * 變量 11: NPC1當前騙局 (1-10)
 * 變量 12: NPC2當前騙局 (1-10)
 * 變量 13: NPC3當前騙局 (1-10)
 * 變量 14: NPC4當前騙局 (1-10)
 * 變量 15: NPC5當前騙局 (1-10)
 * 變量 16: NPC6當前騙局 (1-10)
 * 變量 20: 總對話次數
 * 變量 21: 當前會話ID
 * 變量 22: 當前人設 (A/B/C/D - 會自動輪換)
 * 變量 23: 對話記錄
 * 變量 24: 評分結果
 * 變量 25: 當前人設索引 (0-3，用於輪換)
 */

(function() {
    'use strict';

    const parameters = PluginManager.parameters('RotatingScamSystem');
    const API_URL = String(parameters['API_URL'] || 'http://localhost:8000');
    
    // ============================================================================
    // 人設配置 (A/B/C/D 輪換)
    // ============================================================================
    
    const PERSONAS = ['A', 'B', 'C', 'D'];
    const PERSONA_NAMES = {
        'A': '陳老伯（長者）',
        'B': '林小姐（一般市民）',
        'C': '王先生（過度自信者）',
        'D': '李同學（年輕學生）'
    };
    
    // ============================================================================
    // 🔧 全局变量 - 解決 RPG Maker $gameVariables 在 async 回調中失效的問題
    // ============================================================================
    let currentSessionId = null;
    
    // ============================================================================
    // 10種騙局配置
    // ============================================================================
    
    const SCAM_TYPES = {
        1: {
            name: "投資詐騙",
            role: "投資顧問",
            description: "虛擬貨幣投資，保證高收益30%",
            opening: "你好！我是專業投資顧問，有個千載難逢的投資機會...",
            keywords: ["投資", "虛擬貨幣", "保證收益", "月收益30%", "加LINE"],
            tactics: [
                "承諾不切實際的高回報",
                "製造緊迫感",
                "要求快速決定",
                "用專業術語迷惑",
                "要求私下交易"
            ]
        },
        2: {
            name: "假警察詐騙",
            role: "刑警",
            description: "冒充警察，聲稱涉嫌洗錢",
            opening: "你好，我是刑事警察局的王大明，你的帳戶涉嫌洗錢案件...",
            keywords: ["警察", "洗錢", "安全帳戶", "配合調查", "保密"],
            tactics: [
                "冒充公權力機關",
                "製造恐慌和壓力",
                "要求轉帳到安全帳戶",
                "禁止告訴他人",
                "威脅法律後果"
            ]
        },
        3: {
            name: "交友詐騙",
            role: "網友",
            description: "網路戀愛後借錢",
            opening: "嗨～我們在網上聊了這麼久，我真的很喜歡你...",
            keywords: ["喜歡", "愛", "家人生病", "借錢", "急用"],
            tactics: [
                "建立虛假感情",
                "製造急迫情況",
                "利用同情心",
                "承諾很快還錢",
                "感情勒索"
            ]
        },
        4: {
            name: "網購詐騙",
            role: "賣家",
            description: "超低價商品，只能轉帳",
            opening: "超便宜iPhone 15 Pro只要5000元！全新未拆封...",
            keywords: ["超低價", "只能轉帳", "不能超商", "特殊管道", "最後幾個"],
            tactics: [
                "價格遠低於市場",
                "拒絕安全付款方式",
                "製造稀缺性",
                "限時優惠壓力",
                "要求先付款"
            ]
        },
        5: {
            name: "假中獎詐騙",
            role: "客服人員",
            description: "中大獎但需先付稅金",
            opening: "恭喜您！您中獎了！獲得購物網站週年慶大獎50萬元...",
            keywords: ["中獎", "50萬", "稅金", "手續費", "24小時內"],
            tactics: [
                "突如其來的好運",
                "要求先付費用",
                "設定時限壓力",
                "不合理的中獎通知",
                "威脅取消獎金"
            ]
        },
        6: {
            name: "假貸款詐騙",
            role: "貸款專員",
            description: "免擔保貸款但需先付費",
            opening: "您好，我是XX銀行的貸款專員，核准您貸款30萬...",
            keywords: ["貸款", "免擔保", "開辦費", "代辦費", "馬上撥款"],
            tactics: [
                "主動提供貸款",
                "條件過於優惠",
                "要求先付各種費用",
                "承諾快速撥款",
                "不需實質審核"
            ]
        },
        7: {
            name: "假客服詐騙",
            role: "客服專員",
            description: "退款或解除分期付款設定",
            opening: "您好，我是購物平台客服，您的訂單被誤設為分期付款...",
            keywords: ["客服", "退款", "分期付款", "操作ATM", "解除設定"],
            tactics: [
                "冒充官方客服",
                "製造緊急問題",
                "要求操作ATM",
                "利用專業術語混淆",
                "聲稱不處理會扣款"
            ]
        },
        8: {
            name: "刷單兼職詐騙",
            role: "招聘人員",
            description: "網路刷單賺佣金，需先墊付",
            opening: "您好！我們在招聘網路刷單人員，每單賺50-200元...",
            keywords: ["刷單", "兼職", "墊付", "佣金", "輕鬆賺錢"],
            tactics: [
                "承諾輕鬆賺錢",
                "要求先墊付款項",
                "用小額收益建立信任",
                "逐步增加墊付金額",
                "最後消失不還錢"
            ]
        },
        9: {
            name: "虛假招聘詐騙",
            role: "人資主管",
            description: "高薪工作機會，需先繳費",
            opening: "恭喜您！您的履歷通過審核，月薪8萬的職位等著您...",
            keywords: ["高薪", "招聘", "培訓費", "保證金", "內定"],
            tactics: [
                "承諾高薪職位",
                "要求繳納各種費用",
                "製造稀缺性",
                "聲稱內部保證錄取",
                "收費後失聯"
            ]
        },
        10: {
            name: "假冒親友詐騙",
            role: "你的朋友",
            description: "冒充親友急需借錢",
            opening: "救命！我是小明，手機掉了用朋友的，現在急需用錢...",
            keywords: ["我是XX", "手機掉了", "急用", "先轉帳", "明天還"],
            tactics: [
                "冒充熟人身份",
                "製造緊急情況",
                "避免語音視頻",
                "要求快速轉帳",
                "承諾很快歸還"
            ]
        }
    };
    
    // NPC對應的事件ID
    const NPC_IDS = [17, 16, 12, 13, 14, 15];
    
    // NPC位置
    const NPC_POSITIONS = {
        12: {x: 19, y: 23},
        13: {x: 20, y: 31},
        14: {x: 8, y: 32},
        15: {x: 8, y: 25},
        16: {x: 35, y: 20},
        17: {x: 18, y: 9}
    };
    
    // NPC路径点配置（从训练助理出发的完整路径）
    const NPC_ROUTES = {
        17: [{x: 18, y: 10}],  // EV017: (10,9) -> (18,10) -> (18,9)
        16: [{x: 20, y: 10}, {x: 20, y: 20}, {x: 34, y: 20}],  // EV016: -> (20,10) -> (20,20) -> (34,20) -> (35,20)
        12: [{x: 20, y: 20}, {x: 20, y: 23}],  // EV012: -> (20,20) -> (20,23) -> (19,23)
        13: [{x: 20, y: 30}],  // EV013: -> (20,30) -> (20,31)
        14: [{x: 19, y: 30}, {x: 19, y: 34}, {x: 9, y: 34}, {x: 9, y: 32}],  // EV014: -> (19,30) -> (19,34) -> (9,34) -> (9,32) -> (8,32)
        15: [{x: 9, y: 25}]  // EV015: -> (9,25) -> (8,25)
    };
    
    // ============================================================================
    // 初始化系統
    // ============================================================================
    
    function initializeSystem() {
        // 設定每個NPC的起始騙局
        for (let i = 0; i < NPC_IDS.length; i++) {
            const npcId = NPC_IDS[i];
            const varId = 11 + i; // 變量11-16
            
            // 如果還沒初始化，設定起始騙局
            if (!$gameVariables.value(varId)) {
                const startingScam = i + 1; // NPC1用騙局1, NPC2用騙局2...
                $gameVariables.setValue(varId, startingScam);
                console.log(`NPC${i+1} (ID:${npcId}) 初始化為騙局${startingScam}`);
            }
        }
        
        // 初始化統計
        if (!$gameVariables.value(20)) {
            $gameVariables.setValue(20, 0); // 總對話次數
        }
        
        // 初始化人設輪換
        if (!$gameVariables.value(25)) {
            $gameVariables.setValue(25, 0); // 人設索引，從0開始
            $gameVariables.setValue(22, 'A'); // 當前人設，從A開始
        }
    }
    
    // ============================================================================
    // 獲取NPC當前使用的騙局
    // ============================================================================
    
    function getCurrentScam(npcId) {
        const index = NPC_IDS.indexOf(npcId);
        if (index === -1) return null;
        
        const varId = 11 + index;
        const scamType = $gameVariables.value(varId) || (index + 1);
        
        return SCAM_TYPES[scamType];
    }
    
    // ============================================================================
    // 切換到下一個騙局
    // ============================================================================
    
    function rotateToNextScam(npcId) {
        const index = NPC_IDS.indexOf(npcId);
        if (index === -1) return;
        
        const varId = 11 + index;
        let currentScam = $gameVariables.value(varId) || (index + 1);
        
        console.log(`[輪換前] NPC${index+1} (ID:${npcId}) - 變數${varId} = 騙局${currentScam}`);
        
        // 切換到下一個騙局（1-10循環）
        currentScam = (currentScam % 10) + 1;
        $gameVariables.setValue(varId, currentScam);
        
        console.log(`[輪換後] NPC${index+1} (ID:${npcId}) - 變數${varId} = 騙局${currentScam}: ${SCAM_TYPES[currentScam].name}`);
    }
    
    // ============================================================================
    // 切換到下一個人設
    // ============================================================================
    
    function rotateToNextPersona() {
        let currentIndex = $gameVariables.value(25) || 0;
        
        console.log(`[人設輪換前] 索引 = ${currentIndex}, 人設 = ${PERSONAS[currentIndex]}`);
        
        // 切換到下一個人設（0-3循環）
        currentIndex = (currentIndex + 1) % PERSONAS.length;
        const newPersona = PERSONAS[currentIndex];
        
        $gameVariables.setValue(25, currentIndex);
        $gameVariables.setValue(22, newPersona);
        
        console.log(`[人設輪換後] 索引 = ${currentIndex}, 人設 = ${newPersona} (${PERSONA_NAMES[newPersona]})`);
        
        return newPersona;
    }
    
    // ============================================================================
    // 自動模式變量
    // ============================================================================
    
    let autoModeActive = false;
    let currentAutoNpcIndex = 0;
    let isMovingToNpc = false;
    let isInBattle = false;
    
    // ============================================================================
    // 插件命令處理
    // ============================================================================
    
    const _Game_Interpreter_pluginCommand = Game_Interpreter.prototype.pluginCommand;
    Game_Interpreter.prototype.pluginCommand = function(command, args) {
        _Game_Interpreter_pluginCommand.call(this, command, args);
        
        switch(command) {
            case 'StartRotatingMode':
                startRotatingMode();
                break;
            case 'StartAutoMode':
                startAutoMode();
                break;
            case 'StopAutoMode':
                stopAutoMode();
                break;
            case 'TalkToScammer':
                talkToScammer(parseInt(args[0]));
                break;
            case 'CheckScamType':
                checkScamType(parseInt(args[0]));
                break;
            case 'ResetRotation':
                resetRotation();
                break;
            case 'ShowStats':
                showStats();
                break;
        }
    };
    
    // ============================================================================
    // 啟動輪換模式
    // ============================================================================
    
    function startRotatingMode() {
        initializeSystem();
        
        $gameMessage.add("========== 輪換詐騙系統 ==========");
        $gameMessage.add("6個NPC騙徒已就位");
        $gameMessage.add("每個NPC會輪流使用10種不同的騙局");
        $gameMessage.add("騙局會在每次對話後自動切換");
        $gameMessage.add("");
        
        // 顯示當前狀態
        $gameMessage.add("【當前騙局狀態】");
        for (let i = 0; i < NPC_IDS.length; i++) {
            const npcId = NPC_IDS[i];
            const scam = getCurrentScam(npcId);
            $gameMessage.add(`NPC${i+1}: ${scam.name}`);
        }
        
        $gameMessage.add("========================");
        $gameMessage.add("請走到NPC處開始對話訓練");
    }
    
    // ============================================================================
    // 與騙徒對話
    // ============================================================================
    
    function talkToScammer(npcId) {
        initializeSystem();
        
        const scam = getCurrentScam(npcId);
        if (!scam) {
            $gameMessage.add("錯誤：無效的NPC ID");
            return;
        }
        
        const currentPersona = $gameVariables.value(22) || 'A';
        const personaName = PERSONA_NAMES[currentPersona];
        
        const index = NPC_IDS.indexOf(npcId);
        $gameMessage.add(`========== NPC${index+1} ==========`);
        $gameMessage.add(`當前騙局：${scam.name}`);
        $gameMessage.add(`騙徒角色：${scam.role}`);
        $gameMessage.add(`您的人設：${personaName}`);
        $gameMessage.add("");
        $gameMessage.add(`${scam.role}：${scam.opening}`);
        $gameMessage.add("========================");
        
        // 開始AI對話
        startAIBattle(npcId, scam);
    }
    
    // ============================================================================
    // 開始AI戰鬥
    // ============================================================================
    
    function startAIBattle(npcId, scam, isAutoMode) {
        const personaType = $gameVariables.value(22) || 'A';
        const personaName = PERSONA_NAMES[personaType];
        
        console.log(`[開始對話] 騙局：${scam.name}, 人設：${personaType} (${personaName})`);
        
        // 創建遊戲會話
        fetch(`${API_URL}/api/game/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                persona_type: personaType,
                scam_type: scam.name
            })
        })
        .then(response => response.json())
        .then(data => {
            const sessionId = data.session_id;
            
            // 🔧 双重保存：全局变量 + 游戏变量
            currentSessionId = sessionId;  // JavaScript 全局变量（可靠）
            $gameVariables.setValue(21, sessionId);  // RPG Maker 游戏变量（可能失效）
            
            console.log(`✅ 會話創建：${sessionId}`);
            console.log(`✅ 驗證變量21 = ${$gameVariables.value(21)}`);
            console.log(`✅ 驗證全局變量 currentSessionId = ${currentSessionId}`);
            
            // 開始對話輪次，直接传递 currentSessionId
            startDialogueLoop(npcId, scam, 0, isAutoMode, currentSessionId);
        })
        .catch(error => {
            console.error("創建會話失敗:", error);
            $gameMessage.add("錯誤：無法連接AI服務");
            
            if (isAutoMode && autoModeActive) {
                isInBattle = false;
                currentAutoNpcIndex++;
                setTimeout(() => moveToNextNpc(), 1000);
            }
        });
    }
    
    // ============================================================================
    // 對話循環
    // ============================================================================
    
    function startDialogueLoop(npcId, scam, round, isAutoMode, overrideSessionId) {
        if (round >= 8) {
            // 達到輪數上限
            endBattle(npcId, scam, isAutoMode);
            return;
        }
        
        console.log(`第 ${round + 1} 輪對話`);
        
        // 生成受騙人回應
        generateVictimResponse(scam, overrideSessionId, (victimMsg) => {
            // 生成騙子回應
            generateScammerResponse(scam, victimMsg, overrideSessionId, (scammerMsg) => {
                // 🔧 顯示對話（自動模式也要顯示）
                console.log(`📢 顯示對話 - 受騙人: ${victimMsg.substring(0, 30)}...`);
                console.log(`📢 顯示對話 - ${scam.role}: ${scammerMsg.substring(0, 30)}...`);
                
                $gameMessage.add(`受騙人：${victimMsg}`);
                $gameMessage.add(`${scam.role}：${scammerMsg}`);
                
                // 記錄對話
                recordDialogue(victimMsg, scammerMsg);
                
                // 檢查是否結束
                if (shouldEndDialogue(victimMsg, scammerMsg)) {
                    endBattle(npcId, scam, isAutoMode);
                } else {
                    // 繼續下一輪，继续传递 overrideSessionId
                    // 🔧 自動模式下延遲更長，讓玩家能看到對話
                    const delay = isAutoMode ? 4000 : 2000;
                    setTimeout(() => {
                        startDialogueLoop(npcId, scam, round + 1, isAutoMode, overrideSessionId);
                    }, delay);
                }
            });
        });
    }
    
    function generateVictimResponse(scam, overrideSessionId, callback) {
        // 🔧 优先链：参数 > 全局变量 > 游戏变量
        const sessionId = overrideSessionId || currentSessionId || $gameVariables.value(21);
        const personaType = $gameVariables.value(22) || 'A';
        const history = $gameVariables.value(23) || [];
        
        // 🔧 檢查 session_id 是否有效
        if (!sessionId || sessionId === 0 || sessionId === "0") {
            console.error("❌ 無效的 session_id:", sessionId);
            console.log("提示：請先創建遊戲會話 (/api/game/start)");
            const fallbacks = {
                'A': '呃...我唔太明白，你可唔可以講清楚啲？',
                'B': '等等，我需要確認一下這個資訊...',
                'C': '我知道啦，但我想先了解清楚細節。',
                'D': '這個...聽起來有點奇怪，你能證明嗎？'
            };
            callback(fallbacks[personaType] || "嗯...");
            return;
        }
        
        // 構建受害者的prompt，包含騙局資訊
        const lastScammerMsg = history.length > 0 ? history[history.length - 1].scammer : scam.opening;
        const victimPrompt = `騙徒剛剛說：「${lastScammerMsg}」\n\n請以你的角色身份自然回應。注意：這是一個${scam.name}的騙局，但你現在可能還不確定是否為詐騙。請根據你的人設特點來回應。`;
        
        // 使用 /api/game/message API，自動應用人設
        console.log(`✅ 使用 session_id: ${sessionId} 發送受害者訊息`);
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
            console.log(`[受害者回應 - 人設${personaType}]: ${reply}`);
            callback(reply);
        })
        .catch(error => {
            console.error("生成受害者回應失敗:", error);
            // Fallback: 根據人設返回不同的預設回應
            const fallbacks = {
                'A': '呃...我唔太明白，你可唔可以講清楚啲？',
                'B': '等等，我需要確認一下這個資訊...',
                'C': '我知道啦，但我想先了解清楚細節。',
                'D': '這個...聽起來有點奇怪，你能證明嗎？'
            };
            callback(fallbacks[personaType] || "嗯...");
        });
    }
    
    function generateScammerResponse(scam, victimMsg, overrideSessionId, callback) {
        // 🔧 优先链：参数 > 全局变量 > 游戏变量
        const sessionId = overrideSessionId || currentSessionId || $gameVariables.value(21);
        const personaType = $gameVariables.value(22) || 'A';
        
        // 使用騙局的tactics構建詳細的騙徒prompt
        const tactics = scam.tactics.join('、');
        const scammerPrompt = `受害者剛剛說：「${victimMsg}」\n\n你是${scam.role}，正在進行${scam.name}。你的詐騙手法包括：${tactics}。\n\n請根據受害者的回應，繼續你的詐騙行為。記住要保持角色一致性，不要暴露自己是騙徒。用廣東話回應，保持真實感。`;
        
        // 使用 /api/game/message API
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
            console.log(`[騙徒回應 - ${scam.role}]: ${reply}`);
            callback(reply);
        })
        .catch(error => {
            console.error("生成騙徒回應失敗:", error);
            // Fallback: 根據騙局類型返回預設回應
            const fallbacks = {
                '電話詐騙': '陳先生，你嘅銀行戶口真係有問題，你唔配合我哋就要凍結戶口。',
                '投資詐騙': '呢個投資機會真係千載難逢，你而家唔入場就太遲啦。',
                '網購詐騙': '你嘅訂單有問題，需要你提供銀行資料先可以退款。',
                '釣魚詐騙': '請你立即登入呢個連結更新你嘅資料，否則帳戶會被封鎖。',
                '愛情詐騙': '我真係好需要你嘅幫助，可唔可以借啲錢畀我應急？'
            };
            callback(fallbacks[scam.name] || "那你再考慮看看...");
        });
    }
    
    function recordDialogue(victimMsg, scammerMsg) {
        const history = $gameVariables.value(23) || [];
        history.push({victim: victimMsg, scammer: scammerMsg});
        $gameVariables.setValue(23, history);
    }
    
    function shouldEndDialogue(victimMsg, scammerMsg) {
        const endKeywords = ["不了", "報警", "謝謝", "再見", "不要", "拒絕"];
        return endKeywords.some(k => victimMsg.includes(k));
    }
    
    // ============================================================================
    // 結束戰鬥並評分
    // ============================================================================
    
    function endBattle(npcId, scam) {
        console.log("對話結束，開始評分");
        
        $gameMessage.add("========== 對話結束 ==========");
        $gameMessage.add("正在分析您的表現...");
        
        // 獲取對話歷史
        const history = $gameVariables.value(23) || [];
        const dialogueText = history.map(h => 
            `受騙人：${h.victim}\n${scam.role}：${h.scammer}`
        ).join('\n\n');
        
        // AI評分
        fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                role: `你是防詐騙評分專家。請評估受騙人在面對${scam.name}時的表現。
                      評分標準：警覺性30分、判斷力30分、應對25分、防範意識15分。
                      給出總分（0-100）、分析和建議。`,
                message: `騙局類型：${scam.name}\n詐騙手法：${scam.tactics.join('、')}\n\n對話記錄：\n${dialogueText}`,
                history: []
            })
        })
        .then(response => response.json())
        .then(data => {
            const scoreResult = data.reply;
            $gameVariables.setValue(24, scoreResult);
            
            // 顯示評分
            displayScore(scoreResult, scam);
            
            // 切換到下一個騙局
            rotateToNextScam(npcId);
            
            // 切換到下一個人設
            const newPersona = rotateToNextPersona();
            
            // 更新統計
            const totalTalks = $gameVariables.value(20) || 0;
            $gameVariables.setValue(20, totalTalks + 1);
            
            // 清空對話記錄
            $gameVariables.setValue(23, []);
            
            const index = NPC_IDS.indexOf(npcId);
            const nextScam = getCurrentScam(npcId);
            $gameMessage.add("");
            $gameMessage.add(`NPC${index+1} 下次將使用：${nextScam.name}`);
            $gameMessage.add(`下次人設：${PERSONA_NAMES[newPersona]}`);
        })
        .catch(error => {
            console.error("評分失敗:", error);
            $gameMessage.add("評分系統錯誤");
        });
    }
    
    function displayScore(scoreResult, scam) {
        $gameMessage.add("========== 評分結果 ==========");
        $gameMessage.add(`騙局類型：${scam.name}`);
        
        // 解析分數
        const scoreMatch = scoreResult.match(/(\d+)分/);
        const score = scoreMatch ? parseInt(scoreMatch[1]) : 50;
        
        $gameMessage.add(`得分：${score}分`);
        $gameMessage.add("");
        
        // 分段顯示
        const lines = scoreResult.split('\n');
        lines.slice(0, 5).forEach(line => {
            if (line.trim()) {
                $gameMessage.add(line);
            }
        });
        
        $gameMessage.add("========================");
    }
    
    // ============================================================================
    // 查看騙局類型
    // ============================================================================
    
    function checkScamType(npcId) {
        const scam = getCurrentScam(npcId);
        if (!scam) {
            $gameMessage.add("錯誤：無效的NPC ID");
            return;
        }
        
        const index = NPC_IDS.indexOf(npcId);
        
        $gameMessage.add(`========== NPC${index+1}信息 ==========`);
        $gameMessage.add(`當前騙局：${scam.name}`);
        $gameMessage.add(`角色：${scam.role}`);
        $gameMessage.add(`描述：${scam.description}`);
        $gameMessage.add("");
        $gameMessage.add("詐騙手法：");
        scam.tactics.forEach(tactic => {
            $gameMessage.add(`  • ${tactic}`);
        });
        $gameMessage.add("========================");
    }
    
    // ============================================================================
    // 重置輪換
    // ============================================================================
    
    function resetRotation() {
        for (let i = 0; i < NPC_IDS.length; i++) {
            const varId = 11 + i;
            const startingScam = i + 1;
            $gameVariables.setValue(varId, startingScam);
        }
        
        $gameVariables.setValue(20, 0);
        $gameVariables.setValue(21, null);
        $gameVariables.setValue(23, []);
        $gameVariables.setValue(24, null);
        
        $gameMessage.add("系統已重置");
        $gameMessage.add("所有NPC恢復初始騙局");
    }
    
    // ============================================================================
    // 顯示統計
    // ============================================================================
    
    function showStats() {
        $gameMessage.add("========== 系統統計 ==========");
        $gameMessage.add(`總對話次數：${$gameVariables.value(20) || 0}`);
        $gameMessage.add("");
        $gameMessage.add("各NPC當前騙局：");
        
        for (let i = 0; i < NPC_IDS.length; i++) {
            const npcId = NPC_IDS[i];
            const scam = getCurrentScam(npcId);
            $gameMessage.add(`  NPC${i+1}: ${scam.name}`);
        }
        
        $gameMessage.add("========================");
    }
    
    // ============================================================================
    // 自動模式功能
    // ============================================================================
    
    function startAutoMode() {
        initializeSystem();
        
        autoModeActive = true;
        currentAutoNpcIndex = 0;
        isInBattle = false;
        
        // 不使用消息框（需要玩家按确认），直接在Console显示
        console.log("========== 自動模式啟動 ==========");
        console.log("系統將自動與6個NPC依次對話");
        console.log("體驗不同的騙局類型");
        console.log("按Esc可隨時停止");
        console.log("================================");
        
        // 等待当前事件完全结束
        const waitForEventEnd = () => {
            // 检查消息框和事件状态
            if ($gameMessage.isBusy() || $gameMap.isEventRunning()) {
                console.log("  等待事件和消息完全结束...");
                setTimeout(waitForEventEnd, 300);
                return;
            }
            
            // 额外等待一帧，确保事件完全释放
            setTimeout(() => {
                console.log("  事件已结束，开始自动移动序列");
                moveToNextNpc();
            }, 500);
        };
        
        // 开始等待
        waitForEventEnd();
    }
    
    function stopAutoMode() {
        autoModeActive = false;
        isMovingToNpc = false;
        isInBattle = false;
        
        // 清除所有正在进行的移动
        if ($gamePlayer.isMoveRouteForcing()) {
            $gamePlayer._moveRouteForcing = false;
            $gamePlayer._moveRoute = null;
            $gamePlayer._moveRouteIndex = 0;
        }
        
        $gameMessage.add("========== 自動模式已停止 ==========");
        $gameMessage.add("您已恢復控制權");
        $gameMessage.add("可以自由移動了");
        
        console.log("自動模式已停止，玩家控制權已恢復");
    }
    
    function moveToNextNpc() {
        if (!autoModeActive || isInBattle) return;
        
        // 檢查是否完成一輪
        if (currentAutoNpcIndex >= NPC_IDS.length) {
            $gameMessage.add("========== 一輪訓練完成 ==========");
            $gameMessage.add(`已與所有${NPC_IDS.length}個NPC對話完畢`);
            $gameMessage.add("");
            $gameMessage.add("繼續下一輪？");
            $gameMessage.add("  是：系統將自動繼續");
            $gameMessage.add("  否：使用StopAutoMode停止");
            
            // 重置並繼續
            currentAutoNpcIndex = 0;
            setTimeout(() => {
                if (autoModeActive) {
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
        
        console.log(`自動移動到NPC${currentAutoNpcIndex + 1} (ID:${npcId}) 位置:(${npcPos.x},${npcPos.y})`);
        console.log(`  路径点: ${route.length}个`);
        
        isMovingToNpc = true;
        
        // 移动到最后一个路径点（NPC旁边），不需要移动到NPC精确位置
        // 因为NPC占据了那个格子，玩家无法进入
        // "玩家接触"触发器会在玩家接触NPC边缘时自动触发
        const finalTarget = route.length > 0 ? route[route.length - 1] : npcPos;
        
        console.log(`  最终目标: (${finalTarget.x}, ${finalTarget.y}) - NPC旁边`);
        
        movePlayerViaRoute(route, finalTarget.x, finalTarget.y, () => {
            isMovingToNpc = false;
            console.log(`  ✓ 到达NPC旁边，等待触发对话...`);
            
            // 等待一小段时间，让"玩家接触"触发器生效
            setTimeout(() => {
                // 如果还没有触发对话，手动触发
                if (autoModeActive && !isInBattle) {
                    console.log(`  手动触发NPC对话`);
                    startAutoTalk(npcId);
                }
            }, 500);
        });
    }
    
    function movePlayerViaRoute(waypoints, finalX, finalY, callback) {
        if (waypoints.length === 0) {
            // 没有路径点，直接移动到目标
            movePlayerToPosition(finalX, finalY, callback);
            return;
        }
        
        console.log(`  使用路径点移动，共${waypoints.length}个中转点`);
        
        let currentWaypointIndex = 0;
        
        function moveToNextWaypoint() {
            if (!autoModeActive) {
                // 如果被停止，立即结束
                if (callback) callback();
                return;
            }
            
            if (currentWaypointIndex < waypoints.length) {
                const waypoint = waypoints[currentWaypointIndex];
                console.log(`  -> 移动到路径点${currentWaypointIndex + 1}: (${waypoint.x}, ${waypoint.y})`);
                
                movePlayerToPosition(waypoint.x, waypoint.y, () => {
                    currentWaypointIndex++;
                    setTimeout(moveToNextWaypoint, 100); // 短暂停顿
                });
            } else {
                // 所有路径点完成
                const player = $gamePlayer;
                
                // 检查是否已经在最终目标
                if (player.x === finalX && player.y === finalY) {
                    console.log(`  ✓ 已在最终目标位置`);
                    if (callback) callback();
                } else {
                    // 移动到最终目标
                    console.log(`  -> 移动到最终目标: (${finalX}, ${finalY})`);
                    movePlayerToPosition(finalX, finalY, callback);
                }
            }
        }
        
        moveToNextWaypoint();
    }
    
    function movePlayerToPosition(targetX, targetY, callback) {
        const player = $gamePlayer;
        
        // 等待消息框完全关闭
        if ($gameMessage.isBusy()) {
            console.log("  等待消息框关闭...");
            setTimeout(() => {
                movePlayerToPosition(targetX, targetY, callback);
            }, 500);
            return;
        }
        
        // 检查是否还在事件处理中
        if ($gameMap.isEventRunning()) {
            console.log("  等待事件完成...");
            setTimeout(() => {
                movePlayerToPosition(targetX, targetY, callback);
            }, 500);
            return;
        }
        
        
        
        console.log(`移动玩家: 当前位置(${player.x},${player.y}) -> 目标位置(${targetX},${targetY})`);
        
        // 如果已经在目标位置，直接回调
        if (player.x === targetX && player.y === targetY) {
            console.log("  已在目标位置");
            if (callback) setTimeout(callback, 100);
            return;
        }
        
        // 检查玩家状态
        console.log(`  玩家状态: moving=${player.isMoving()}, jumping=${player.isJumping()}`);
        console.log(`  强制移动: ${player.isMoveRouteForcing()}`);
        
        // 如果正在强制移动，先清除
        if (player.isMoveRouteForcing()) {
            console.log("  清除旧的移动路线");
            player._moveRouteForcing = false;
            player._moveRoute = null;
        }
        
        // 计算路径
        const dx = targetX - player.x;
        const dy = targetY - player.y;
        
        console.log(`  需要移动: dx=${dx}, dy=${dy}`);
        
        // 检查目标位置通行性
        const canPassTarget = $gameMap.isPassable(targetX, targetY, 2);
        console.log(`  目标位置(${targetX},${targetY})可通行: ${canPassTarget}`);
        
        // 检查起始位置移动方向
        if (dx > 0) {
            const canMove = $gameMap.isPassable(player.x, player.y, 6);
            console.log(`  当前位置(${player.x},${player.y})可向右: ${canMove}`);
        } else if (dx < 0) {
            const canMove = $gameMap.isPassable(player.x, player.y, 4);
            console.log(`  当前位置(${player.x},${player.y})可向左: ${canMove}`);
        }
        
        if (dy > 0) {
            const canMove = $gameMap.isPassable(player.x, player.y, 2);
            console.log(`  当前位置(${player.x},${player.y})可向下: ${canMove}`);
        } else if (dy < 0) {
            const canMove = $gameMap.isPassable(player.x, player.y, 8);
            console.log(`  当前位置(${player.x},${player.y})可向上: ${canMove}`);
        }
        
        // 使用Game_Character的移动方法
        const moveCommands = [];
        
        // X方向移动
        if (dx > 0) {
            for (let i = 0; i < dx; i++) {
                moveCommands.push({code: 6}); // 右
            }
        } else if (dx < 0) {
            for (let i = 0; i < Math.abs(dx); i++) {
                moveCommands.push({code: 4}); // 左
            }
        }
        
        // Y方向移动
        if (dy > 0) {
            for (let i = 0; i < dy; i++) {
                moveCommands.push({code: 2}); // 下
            }
        } else if (dy < 0) {
            for (let i = 0; i < Math.abs(dy); i++) {
                moveCommands.push({code: 8}); // 上
            }
        }
        
        // 结束命令
        moveCommands.push({code: 0});
        
        console.log(`  生成移动命令: ${moveCommands.length}个`);
        
        // 设置移动路线
        const route = {
            list: moveCommands,
            repeat: false,
            skippable: false,
            wait: false
        };
        
        // 确保清除旧的移动状态和解锁玩家
        console.log(`  检查玩家锁定状态: locked=${player._locked}, transparent=${player._transparent}`);
        
        // 强制解锁玩家
        if (player._locked) {
            console.log("  解锁玩家");
            player._locked = false;
        }
        
        // 确保玩家可见
        if (player._transparent) {
            console.log("  恢复玩家可见性");
            player._transparent = false;
        }
        
        // 清除旧的移动路线
        if (player._moveRouteForcing) {
            console.log("  清除旧的强制移动");
            player._moveRouteForcing = false;
            player._moveRoute = null;
            player._moveRouteIndex = 0;
        }
        
        // 停止当前的所有移动（使用RPG Maker MV的正确方法）
        player._realX = player._x;
        player._realY = player._y;
        
        // 确保玩家状态正常
        player.setMoveSpeed(5);
        player._through = false;
        
        console.log("  玩家状态已重置");
        console.log(`  使用逐步移动方式（绕过canMove检查）`);
        
        // 使用定时器逐步移动（不使用forceMoveRoute）
        let moveStepIndex = 0;
        let moveCheckCount = 0;
        const maxAttempts = 300; // 30秒超时
        
        const executeNextMove = () => {
            moveCheckCount++;
            
            // 超时保护
            if (moveCheckCount > maxAttempts) {
                console.error(`  ✗ 移动超时！当前位置:(${player.x},${player.y}), 目标:(${targetX},${targetY})`);
                if (callback) callback();
                return;
            }
            
            // 检查是否到达目标
            if (player.x === targetX && player.y === targetY) {
                console.log(`  ✓ 到达目标！位置:(${player.x},${player.y})`);
                if (callback) setTimeout(callback, 200);
                return;
            }
            
            // 如果正在移动，等待移动完成
            if (player.isMoving()) {
                setTimeout(executeNextMove, 100);
                return;
            }
            
            // 执行下一步移动
            if (moveStepIndex < moveCommands.length - 1) { // -1 因为最后一个是结束命令{code:0}
                const cmd = moveCommands[moveStepIndex];
                if (cmd.code !== 0) {
                    // 显示当前步骤
                    if (moveStepIndex % 2 === 0 || moveCommands.length <= 3) {
                        console.log(`  -> 执行第${moveStepIndex + 1}/${moveCommands.length - 1}步 (${player.x},${player.y})`);
                    }
                    
                    // 执行移动命令
                    switch(cmd.code) {
                        case 2: player.moveStraight(2); break; // 下
                        case 4: player.moveStraight(4); break; // 左
                        case 6: player.moveStraight(6); break; // 右
                        case 8: player.moveStraight(8); break; // 上
                    }
                    
                    moveStepIndex++;
                }
                // 等待这一步的移动动画完成
                setTimeout(executeNextMove, 200); // 增加到200ms，让移动有足够时间
            } else {
                // 所有步骤完成，继续检查是否真的到达了
                setTimeout(executeNextMove, 150);
            }
        };
        
        // 开始执行移动
        console.log(`  开始逐步移动，共${moveCommands.length - 1}步`);
        executeNextMove();
    }
    
    function startAutoTalk(npcId) {
        if (!autoModeActive || isInBattle) return;
        
        const scam = getCurrentScam(npcId);
        const index = NPC_IDS.indexOf(npcId);
        
        // 从游戏变量获取骗局类型ID
        const varId = 11 + index;
        const scamTypeId = $gameVariables.value(varId) || (index + 1);
        
        console.log(`========== 触发战斗 ==========`);
        console.log(`NPC${index+1} (ID:${npcId})`);
        console.log(`骗局：${scam.name} (Type ${scamTypeId})`);
        console.log(`角色：${scam.role}`);
        
        // 🔧 標記進入戰鬥狀態
        isInBattle = true;
        
        // 🔧 設置人設（用於 AutoScamBattle）
        const currentPersona = $gameVariables.value(22) || 'A';
        console.log(`當前人設: ${currentPersona}`);
        
        // 🎮 先創建 Session，再觸發戰鬥場景
        console.log(`[RotatingScamSystem] 創建遊戲會話...`);
        
        fetch(`${API_URL}/api/game/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                persona_type: currentPersona,
                scam_type: scam.name
            })
        })
        .then(response => response.json())
        .then(data => {
            const sessionId = data.session_id;
            
            // 🔧 **關鍵修復**: 必須在觸發戰鬥前先設置所有變數！
            // 先設置騙局相關變數（AutoScamBattle 依賴這些）
            $gameVariables.setValue(30, scamTypeId);  // 當前騙局類型 ⚠️ 必須最先設置！
            $gameVariables.setValue(31, 0);           // 當前回合
            $gameVariables.setValue(32, '');          // 對話歷史
            
            // 再保存 session_id
            currentSessionId = sessionId;
            $gameVariables.setValue(21, sessionId);
            
            // 🔧 **終極修復**: 使用 BattleManager 傳遞數據（不會被場景切換重置）
            BattleManager._scamTypeId = scamTypeId;
            BattleManager._scamSessionId = sessionId;
            BattleManager._scamPersona = currentPersona;
            
            console.log(`✅ 會話創建成功: ${sessionId}`);
            console.log(`✅ 已儲存到變量21和全局變量`);
            console.log(`✅ 變量30已設置為: ${scamTypeId} (騙局類型)`);
            console.log(`✅ BattleManager 數據已設置 - scamTypeId: ${BattleManager._scamTypeId}`);
            
            // 🔧 **關鍵修復**: 使用 setTimeout 確保變數完全寫入後再觸發戰鬥
            // RPG Maker 的變數系統需要一幀時間才能同步到新場景
            setTimeout(() => {
                // 再次驗證變數已設置
                const verify30 = $gameVariables.value(30);
                const verify21 = $gameVariables.value(21);
                console.log(`🔍 延遲後驗證 - 變量30: ${verify30}, 變量21: ${verify21}`);
                
                // 計算敵人ID (5-14對應騙局1-10)
                const enemyId = 4 + scamTypeId;
                
                console.log(`觸發戰鬥場景: Enemy ID ${enemyId}`);
                
                // 設置戰鬥
                BattleManager.setup(1, false, false);  // troopId=1
                BattleManager._troopId = enemyId;
                $gamePlayer.makeEncounterCount();
                
                // 切換到戰鬥場景（此時變數已全部設置完畢）
                SceneManager.push(Scene_Battle);
                
                console.log(`✅ 戰鬥場景已啟動 (NPC: ${npcId}, 騙局: ${scamTypeId}, Session: ${sessionId})`);
            }, 100); // 100ms 延遲，確保變數寫入完成
        })
        .catch(error => {
            console.error("❌ 創建會話失敗:", error);
            console.log("嘗試使用模擬模式或檢查後端是否運行");
            
            // 失敗時清除戰鬥狀態，繼續下一個NPC
            isInBattle = false;
            if (autoModeActive) {
                currentAutoNpcIndex++;
                setTimeout(() => moveToNextNpc(), 2000);
            }
        });
    }
    
    // 修改endBattle以支持自動模式
    const originalEndBattle = endBattle;
    endBattle = function(npcId, scam, isAutoMode) {
        console.log("對話結束，開始評分");
        
        $gameMessage.add("========== 對話結束 ==========");
        $gameMessage.add("正在分析您的表現...");
        
        // 獲取對話歷史
        const history = $gameVariables.value(23) || [];
        const dialogueText = history.map(h => 
            `受騙人：${h.victim}\n${scam.role}：${h.scammer}`
        ).join('\n\n');
        
        // AI評分
        fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                role: `你是防詐騙評分專家。請評估受騙人在面對${scam.name}時的表現。
                      評分標準：警覺性30分、判斷力30分、應對25分、防範意識15分。
                      給出總分（0-100）、分析和建議。`,
                message: `騙局類型：${scam.name}\n詐騙手法：${scam.tactics.join('、')}\n\n對話記錄：\n${dialogueText}`,
                history: []
            })
        })
        .then(response => response.json())
        .then(data => {
            const scoreResult = data.reply;
            $gameVariables.setValue(24, scoreResult);
            
            // 顯示評分
            displayScore(scoreResult, scam);
            
            // 切換到下一個騙局
            rotateToNextScam(npcId);
            
            // 切換到下一個人設
            const newPersona = rotateToNextPersona();
            
            // 更新統計
            const totalTalks = $gameVariables.value(20) || 0;
            $gameVariables.setValue(20, totalTalks + 1);
            
            // 清空對話記錄
            $gameVariables.setValue(23, []);
            
            const index = NPC_IDS.indexOf(npcId);
            const nextScam = getCurrentScam(npcId);
            const nextPersonaName = PERSONA_NAMES[newPersona] || newPersona;
            $gameMessage.add("");
            $gameMessage.add(`NPC${index+1} 下次將使用：${nextScam.name}`);
            $gameMessage.add(`下次人設：${nextPersonaName}`);
            
            // 如果是自動模式，繼續下一個NPC
            if (isAutoMode && autoModeActive) {
                isInBattle = false;
                currentAutoNpcIndex++;
                
                // 顯示提示訊息
                $gameMessage.add("");
                $gameMessage.add("【按ESC或走到停止事件可中斷】");
                $gameMessage.add("3秒後前往下一個NPC...");
                
                setTimeout(() => {
                    if (autoModeActive) {  // 再次檢查，防止被停止
                        moveToNextNpc();
                    }
                }, 3000);  // 改為3秒，給玩家更多時間
            } else {
                isInBattle = false;
            }
        })
        .catch(error => {
            console.error("評分失敗:", error);
            $gameMessage.add("評分系統錯誤");
            
            if (isAutoMode && autoModeActive) {
                isInBattle = false;
                currentAutoNpcIndex++;
                setTimeout(() => {
                    moveToNextNpc();
                }, 1000);
            } else {
                isInBattle = false;
            }
        });
    };
    
    // 更新Map刷新邏輯以支持自動模式
    const _Scene_Map_update = Scene_Map.prototype.update;
    Scene_Map.prototype.update = function() {
        _Scene_Map_update.call(this);
        
        // 檢測ESC鍵停止自動模式
        if (autoModeActive && Input.isTriggered('cancel')) {
            stopAutoMode();
        }
        
        // 自動模式邏輯
        if (autoModeActive && !isMovingToNpc && !isInBattle && !$gameMessage.isBusy()) {
            // 檢查是否需要繼續
            // 這裡可以添加自動繼續的邏輯
        }
    };
    
    // 頁面加載時初始化
    const _Scene_Map_onMapLoaded = Scene_Map.prototype.onMapLoaded;
    Scene_Map.prototype.onMapLoaded = function() {
        _Scene_Map_onMapLoaded.call(this);
        if ($gameMap.mapId() === 2) { // Forest Town
            initializeSystem();
        }
    };
    
    // 暴露给AutoScamBattle插件使用的接口
    window.RotatingScamSystem = {
        rotateScam: function(npcId) {
            console.log(`轮换骗局: NPC ${npcId}`);
            rotateToNextScam(npcId);
            
            // 战斗结束后继续自动模式
            if (autoModeActive) {
                isInBattle = false;
                currentAutoNpcIndex++;
                
                console.log(`准备移动到下一个NPC (${currentAutoNpcIndex + 1}/${NPC_IDS.length})`);
                
                // 延迟移动，让玩家从战斗场景返回
                setTimeout(() => {
                    moveToNextNpc();
                }, 1000);
            }
        },
        
        getCurrentScam: function(npcId) {
            return getCurrentScam(npcId);
        },
        
        isAutoModeActive: function() {
            return autoModeActive;
        }
    };
    
})();

