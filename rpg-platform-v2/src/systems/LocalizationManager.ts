export type AppLanguage = 'zh-HK' | 'zh-CN' | 'en-US' | 'ja-JP';

const LANGUAGE_OPTIONS: Array<{ code: AppLanguage; label: string }> = [
  { code: 'zh-HK', label: '繁體' },
  { code: 'zh-CN', label: '简体' },
  { code: 'en-US', label: 'EN' },
  { code: 'ja-JP', label: '日本語' }
];

const DICTIONARY: Record<AppLanguage, Record<string, string>> = {
  'zh-HK': {
    title: '🛡️ AI 防詐騙訓練',
    subtitle: '互動式 RPG 平台',
    chooseRole: '選擇你的角色',
    autoMode: '🤖 自動訓練模式',
    backHome: '🏠 返回主頁',
    currentRole: '當前角色',
    controls: '⌨️ 操作提示',
    controlsBody: '方向鍵/WASD - 移動\nE - 互動 | H - 說明 | F1/F2/F3 - 切換角色',
    guideTitle: '🎮 遊戲指南',
    guideSubtitle: '香港反詐騙 AI 模擬對話系統',
    noNpc: '附近沒有可互動的NPC',
    battleBack: '← 返回地圖',
    battleInputPlaceholder: '輸入你的回應... (Enter 發送)',
    trustPanel: '📊 信任度分析',
    ttsOn: '🔊 語音開',
    ttsOff: '🔈 語音關',
    ttsTitleOn: '已開啟自動語音播放',
    ttsTitleOff: '點擊開啟自動語音播放',
    ttsFailed: '⚠️ TTS失敗：',
    voiceError: '⚠️ 語音識別錯誤：',
    roleVictim: '受害者',
    roleScammer: '騙徒',
    roleExpert: '防詐專家',
    roleDescVictim: '防禦詐騙攻擊，識別危險信號',
    roleDescScammer: '使用心理戰術操縱受害者',
    roleDescExpert: '介入詐騙並教育受害者',
    infoConnecting: '🔄 正在連接 AI 系統...',
    infoReady: '✅ AI 系統已就緒',
    infoFailed: '⚠️ 無法連接 AI 系統',
    gameGuideStart: '開始遊戲 (H)',
    autoTitle: '🤖 自動訓練模式',
    autoSubtitle: 'AI 自動運行訓練模擬',
    autoStart: '▶️ 開始模擬',
    autoStop: '⏸️ 停止模擬',
    autoInfo: '💡 自動模式將持續運行模擬，AI 控制角色自動導航並與 NPC 互動',
    gameGoal: '遊戲目標',
    gameGoalDesc: '與 NPC 互動，學習識別和防範各種詐騙手法',
    gameControls: '操作說明',
    gameControlsDesc: 'E 鍵 - 與 NPC 互動\nH 鍵 - 顯示/隱藏說明\nF1/F2/F3 - 切換角色（受害者/騙徒/專家）',
    gameTips: '遊戲提示',
    gameTipsDesc: '靠近 NPC 會顯示互動提示\n不同角色有不同的對話選項\n完成對話可獲得訓練數據',
    learningPoints: '💡 學習要點',
    successSummary: '✅ 你成功識破了騙局！保持警覺，繼續學習防詐技巧。',
    failSummary: '⚠️ 這次被騙了，記住騙徒的手法，下次要更加小心！',
    neutralSummary: '📚 繼續學習不同的詐騙手法，提高防範意識。',
    returnMap: '🏠 返回地圖',
    tryAgain: '🔄 再試一次',
  },
  'zh-CN': {
    title: '🛡️ AI 防诈骗训练',
    subtitle: '互动式 RPG 平台',
    chooseRole: '选择你的角色',
    autoMode: '🤖 自动训练模式',
    backHome: '🏠 返回主页',
    currentRole: '当前角色',
    controls: '⌨️ 操作提示',
    controlsBody: '方向键/WASD - 移动\nE - 互动 | H - 说明 | F1/F2/F3 - 切换角色',
    guideTitle: '🎮 游戏指南',
    guideSubtitle: '反诈骗 AI 模拟对话系统',
    noNpc: '附近没有可互动的NPC',
    battleBack: '← 返回地图',
    battleInputPlaceholder: '输入你的回复... (Enter 发送)',
    trustPanel: '📊 信任度分析',
    ttsOn: '🔊 语音开',
    ttsOff: '🔈 语音关',
    ttsTitleOn: '已开启自动语音播放',
    ttsTitleOff: '点击开启自动语音播放',
    ttsFailed: '⚠️ TTS失败：',
    voiceError: '⚠️ 语音识别错误：',
    roleVictim: '受害者',
    roleScammer: '骗子',
    roleExpert: '防诈专家',
    roleDescVictim: '防御诈骗攻击，识别危险信号',
    roleDescScammer: '使用心理战术操纵受害者',
    roleDescExpert: '介入诈骗并教育受害者',
    infoConnecting: '🔄 正在连接 AI 系统...',
    infoReady: '✅ AI 系统已就绪',
    infoFailed: '⚠️ 无法连接 AI 系统',
    gameGuideStart: '开始游戏 (H)',
    autoTitle: '🤖 自动训练模式',
    autoSubtitle: 'AI 自动运行训练模拟',
    autoStart: '▶️ 开始模拟',
    autoStop: '⏸️ 停止模拟',
    autoInfo: '💡 自动模式将持续运行模拟，AI 控制角色自动导航并与 NPC 互动',
    gameGoal: '游戏目标',
    gameGoalDesc: '与 NPC 互动，学习识别和防范各种诈骗手法',
    gameControls: '操作说明',
    gameControlsDesc: 'E 键 - 与 NPC 互动\nH 键 - 显示/隐藏说明\nF1/F2/F3 - 切换角色（受害者/骗子/专家）',
    gameTips: '游戏提示',
    gameTipsDesc: '靠近 NPC 会显示互动提示\n不同角色有不同对话选项\n完成对话可获得训练数据',
    learningPoints: '💡 学习要点',
    successSummary: '✅ 你成功识破骗局！继续保持警觉。',
    failSummary: '⚠️ 这次被骗了，记住骗子手法，下次要更小心！',
    neutralSummary: '📚 继续学习不同诈骗手法，提高防范意识。',
    returnMap: '🏠 返回地图',
    tryAgain: '🔄 再试一次',
  },
  'en-US': {
    title: '🛡️ AI Anti-Scam Training',
    subtitle: 'Interactive RPG Platform',
    chooseRole: 'Choose Your Role',
    autoMode: '🤖 Auto Training Mode',
    backHome: '🏠 Back Home',
    currentRole: 'Current Role',
    controls: '⌨️ Controls',
    controlsBody: 'Arrow/WASD - Move\nE - Interact | H - Guide | F1/F2/F3 - Switch Role',
    guideTitle: '🎮 Game Guide',
    guideSubtitle: 'AI Anti-Scam Simulation',
    noNpc: 'No NPC nearby to interact',
    battleBack: '← Back to Map',
    battleInputPlaceholder: 'Type your response... (Enter to send)',
    trustPanel: '📊 Trust Metrics',
    ttsOn: '🔊 Voice On',
    ttsOff: '🔈 Voice Off',
    ttsTitleOn: 'Auto voice playback enabled',
    ttsTitleOff: 'Click to enable auto voice playback',
    ttsFailed: '⚠️ TTS failed: ',
    voiceError: '⚠️ Speech recognition error: ',
    roleVictim: 'Victim',
    roleScammer: 'Scammer',
    roleExpert: 'Expert',
    roleDescVictim: 'Defend against scam attempts and identify red flags',
    roleDescScammer: 'Manipulate victims using psychological tactics',
    roleDescExpert: 'Intervene in scams and educate victims',
    infoConnecting: '🔄 Connecting to AI system...',
    infoReady: '✅ AI system ready',
    infoFailed: '⚠️ Unable to connect AI system',
    gameGuideStart: 'Start (H)',
    autoTitle: '🤖 Auto Training Mode',
    autoSubtitle: 'Autonomous AI simulation',
    autoStart: '▶️ Start',
    autoStop: '⏸️ Stop',
    autoInfo: '💡 Auto mode keeps simulations running with AI-controlled interactions.',
    gameGoal: 'Mission',
    gameGoalDesc: 'Interact with NPCs and learn how to detect scam tactics.',
    gameControls: 'Controls',
    gameControlsDesc: 'E - Interact\nH - Show/Hide guide\nF1/F2/F3 - Switch roles',
    gameTips: 'Tips',
    gameTipsDesc: 'Move close to NPCs to interact\nEach role has unique dialogue options\nComplete conversations to train awareness',
    learningPoints: '💡 Key Takeaways',
    successSummary: '✅ Great job! You detected the scam and stayed alert.',
    failSummary: '⚠️ You were tricked this time. Learn the pattern and try again.',
    neutralSummary: '📚 Keep training with different scam scenarios.',
    returnMap: '🏠 Back to Map',
    tryAgain: '🔄 Try Again',
  },
  'ja-JP': {
    title: '🛡️ AI 詐欺対策トレーニング',
    subtitle: 'インタラクティブRPG',
    chooseRole: 'ロールを選択',
    autoMode: '🤖 自動トレーニング',
    backHome: '🏠 ホームへ戻る',
    currentRole: '現在のロール',
    controls: '⌨️ 操作ガイド',
    controlsBody: '方向キー/WASD - 移動\nE - 会話 | H - ガイド | F1/F2/F3 - ロール切替',
    guideTitle: '🎮 ゲームガイド',
    guideSubtitle: 'AI 詐欺対策シミュレーション',
    noNpc: '近くに会話できるNPCがいません',
    battleBack: '← マップへ戻る',
    battleInputPlaceholder: 'メッセージを入力... (Enterで送信)',
    trustPanel: '📊 信頼度メーター',
    ttsOn: '🔊 音声ON',
    ttsOff: '🔈 音声OFF',
    ttsTitleOn: '自動音声再生が有効です',
    ttsTitleOff: 'クリックで自動音声再生',
    ttsFailed: '⚠️ TTS失敗: ',
    voiceError: '⚠️ 音声認識エラー: ',
    roleVictim: '被害者',
    roleScammer: '詐欺師',
    roleExpert: '対策専門家',
    roleDescVictim: '詐欺の手口を見抜き、自分を守る',
    roleDescScammer: '心理戦術で被害者を誘導する',
    roleDescExpert: '介入して被害者に防犯知識を伝える',
    infoConnecting: '🔄 AIシステム接続中...',
    infoReady: '✅ AIシステム準備完了',
    infoFailed: '⚠️ AIシステムに接続できません',
    gameGuideStart: '開始 (H)',
    autoTitle: '🤖 自動トレーニング',
    autoSubtitle: 'AI 自動シミュレーション',
    autoStart: '▶️ 開始',
    autoStop: '⏸️ 停止',
    autoInfo: '💡 自動モードではAIが継続的に会話シミュレーションを行います。',
    gameGoal: 'ゲーム目標',
    gameGoalDesc: 'NPCと会話し、詐欺手口を見抜く力を鍛える。',
    gameControls: '操作方法',
    gameControlsDesc: 'E - 会話\nH - ガイド表示/非表示\nF1/F2/F3 - ロール切替',
    gameTips: 'ヒント',
    gameTipsDesc: 'NPCに近づくと会話可能\nロールごとに選択肢が変化\n会話を重ねて防犯力を強化',
    learningPoints: '💡 学習ポイント',
    successSummary: '✅ 詐欺を見抜きました！その調子で警戒を維持しましょう。',
    failSummary: '⚠️ 今回は騙されました。手口を覚えて次に活かしましょう。',
    neutralSummary: '📚 さまざまな詐欺シナリオで訓練を続けましょう。',
    returnMap: '🏠 マップへ戻る',
    tryAgain: '🔄 もう一度',
  }
};

const STORAGE_LANG_KEY = 'rpgv2_language';

class LocalizationManager {
  private static instance: LocalizationManager;
  private currentLanguage: AppLanguage = 'zh-HK';
  private listeners: Set<(language: AppLanguage) => void> = new Set();

  static getInstance(): LocalizationManager {
    if (!LocalizationManager.instance) {
      LocalizationManager.instance = new LocalizationManager();
      // 從 localStorage 恢復上次語言設定
      try {
        const saved = localStorage.getItem(STORAGE_LANG_KEY) as AppLanguage | null;
        const valid: AppLanguage[] = ['zh-HK', 'zh-CN', 'en-US', 'ja-JP'];
        if (saved && valid.includes(saved)) {
          LocalizationManager.instance.currentLanguage = saved;
        }
      } catch (_) {}
    }
    return LocalizationManager.instance;
  }

  getLanguage(): AppLanguage {
    return this.currentLanguage;
  }

  setLanguage(language: AppLanguage): void {
    if (language === this.currentLanguage) return;
    this.currentLanguage = language;
    // 持久化到 localStorage
    try { localStorage.setItem(STORAGE_LANG_KEY, language); } catch (_) {}
    this.listeners.forEach((listener) => listener(language));
  }

  getLanguageOptions(): Array<{ code: AppLanguage; label: string }> {
    return LANGUAGE_OPTIONS;
  }

  t(key: string): string {
    return DICTIONARY[this.currentLanguage][key] ?? DICTIONARY['zh-HK'][key] ?? key;
  }

  getRoleLabel(roleId: 'victim' | 'scammer' | 'expert'): string {
    if (roleId === 'victim') return this.t('roleVictim');
    if (roleId === 'scammer') return this.t('roleScammer');
    return this.t('roleExpert');
  }

  getSpeechRecognitionLanguage(): string {
    if (this.currentLanguage === 'zh-CN') return 'zh-CN';
    if (this.currentLanguage === 'en-US') return 'en-US';
    if (this.currentLanguage === 'ja-JP') return 'ja-JP';
    return 'yue-Hant-HK';
  }

  onLanguageChange(listener: (language: AppLanguage) => void): void {
    this.listeners.add(listener);
  }

  offLanguageChange(listener: (language: AppLanguage) => void): void {
    this.listeners.delete(listener);
  }
}

export const localization = LocalizationManager.getInstance();

