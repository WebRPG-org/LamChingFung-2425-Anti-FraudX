import Phaser from 'phaser';
import { Role } from '../systems/RoleManager';
import { localization, AppLanguage } from '../systems/LocalizationManager';
import { ScamType } from '../types/ScamTypes';
import { BackendClient, ThreeWayMessageResponse, TTSResponse } from '../services/BackendClient';
import { TrustSystem } from '../systems/TrustSystem';

// ─── Types ────────────────────────────────────────────────────────────────────
interface BattleSceneData {
  scamType: string;
  scamTypeInfo: ScamType;
  playerRole: Role;
  language?: AppLanguage;
}
interface ChatMessage {
  speaker: string;
  text: string;
  color: string;
  side: 'left' | 'right' | 'system';
  emoji: string;
}
interface SavedState {
  sessionId: string | null;
  scamType: string;
  messages: ChatMessage[];
  trust: { s: number; e: number; a: number };
  rounds: number;
  ttsEnabled?: boolean;
  language?: AppLanguage;
}

const STORAGE_KEY = 'rpgv2_battle_state';

// ─── Styles (injected once) ───────────────────────────────────────────────────
const CSS = [
  '#battle-overlay{position:fixed;inset:0;z-index:900;display:flex;flex-direction:column;',
  'font-family:"Noto Sans TC",Rajdhani,sans-serif;background:rgba(10,14,39,.40);',
  'backdrop-filter:blur(6px);}',
  '#bo-header{display:flex;align-items:center;gap:12px;padding:10px 20px;',
  'background:rgba(22,33,62,.92);border-bottom:1.5px solid rgba(8,217,214,.35);flex-shrink:0;}',
  '#bo-back-btn{background:rgba(255,46,99,.85);border:1.5px solid #ff6b9d;color:#fff;',
  'padding:8px 20px;border-radius:7px;cursor:pointer;font-size:17px;font-weight:700;}',
  '#bo-back-btn:hover{background:#ff2e63;}',
  '#bo-title{flex:1;text-align:center;font-size:24px;font-weight:800;color:#08D9D6;',
  'text-shadow:0 0 8px rgba(8,217,214,.4);}',
  '#bo-body{display:flex;flex:1;min-height:0;}',
  '#bo-chat-wrap{flex:1;display:flex;flex-direction:column;min-width:0;}',
  '#bo-messages{flex:1;overflow-y:auto;padding:16px 20px 8px;display:flex;',
  'flex-direction:column;gap:10px;scrollbar-width:thin;scrollbar-color:rgba(8,217,214,.4) transparent;}',
  '#bo-messages::-webkit-scrollbar{width:5px;}',
  '#bo-messages::-webkit-scrollbar-thumb{background:rgba(8,217,214,.4);border-radius:3px;}',
  '.bo-bubble{display:flex;gap:10px;max-width:72%;animation:bIn .25s ease;}',
  '@keyframes bIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}',
  '.bo-bubble.right{flex-direction:row-reverse;align-self:flex-end;}',
  '.bo-bubble.left{align-self:flex-start;}',
  '.bo-bubble.system{align-self:center;max-width:90%;}',
  '.bo-avatar{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;',
  'justify-content:center;font-size:18px;flex-shrink:0;',
  'border:1.5px solid rgba(255,255,255,.2);background:rgba(22,33,62,.8);}',
  '.bo-content{display:flex;flex-direction:column;gap:3px;}',
  '.bo-speaker{font-size:14px;font-weight:700;margin-bottom:2px;}',
  '.bo-text{padding:12px 18px;border-radius:14px;font-size:17px;line-height:1.8;',
  'word-break:break-word;border:1px solid rgba(255,255,255,.08);color:#e8eaf6;}',
  '.bo-bubble.left .bo-text{background:rgba(22,33,62,.85);border-radius:4px 14px 14px 14px;}',
  '.bo-bubble.right .bo-text{border-radius:14px 4px 14px 14px;}',
  '.bo-bubble.system .bo-text{background:rgba(255,217,61,.12);border:1px solid rgba(255,217,61,.3);',
  'color:#FFD93D;border-radius:10px;font-size:16px;text-align:center;}',
  '.bo-typing .bo-text{display:flex;gap:4px;align-items:center;padding:12px 18px;}',
  '.bo-dot{width:7px;height:7px;border-radius:50%;background:#08D9D6;animation:db 1.2s infinite;}',
  '.bo-dot:nth-child(2){animation-delay:.2s}.bo-dot:nth-child(3){animation-delay:.4s}',
  '@keyframes db{0%,80%,100%{transform:scale(.8);opacity:.5}40%{transform:scale(1.2);opacity:1}}',
  '#bo-input-bar{padding:12px 20px;display:flex;gap:10px;align-items:center;',
  'background:rgba(22,33,62,.92);border-top:1.5px solid rgba(255,46,99,.3);flex-shrink:0;}',
  '#bo-input{flex:1;background:rgba(10,14,39,.8);border:1.5px solid rgba(8,217,214,.4);',
  'border-radius:24px;padding:12px 20px;font-size:17px;color:#fff;outline:none;',
  'font-family:inherit;transition:border-color .2s,box-shadow .2s;}',
  '#bo-input:focus{border-color:#08D9D6;box-shadow:0 0 14px rgba(8,217,214,.25);}',
  '#bo-input::placeholder{color:rgba(255,255,255,.3);}',
  '#bo-input:disabled{opacity:.5;cursor:not-allowed;}',
  '.bo-btn{border:none;border-radius:50%;width:44px;height:44px;display:flex;',
  'align-items:center;justify-content:center;font-size:20px;cursor:pointer;',
  'transition:transform .15s,opacity .15s;flex-shrink:0;}',
  '.bo-btn:hover{transform:scale(1.08)}.bo-btn:disabled{opacity:.4;cursor:not-allowed;}',
  '#bo-send-btn{background:#08D9D6;color:#0A0E27;}',
  '#bo-voice-btn{background:rgba(255,46,99,.2);border:1.5px solid rgba(255,46,99,.5);color:#FF2E63;}',
  '#bo-tts-btn{background:rgba(8,217,214,.15);border:1.5px solid rgba(8,217,214,.45);',
  'color:#aefcff;padding:7px 12px;border-radius:18px;cursor:pointer;font-size:13px;font-weight:700;}',
  '#bo-tts-btn.on{background:rgba(8,217,214,.35);color:#fff;border-color:#08D9D6;box-shadow:0 0 12px rgba(8,217,214,.22);}',
  '#bo-tts-btn:disabled{opacity:.45;cursor:not-allowed;}',
  '#bo-voice-btn.recording{background:#FF2E63;color:#fff;animation:vp .8s infinite;}',
  '@keyframes vp{0%,100%{box-shadow:0 0 0 0 rgba(255,46,99,.4)}50%{box-shadow:0 0 0 8px rgba(255,46,99,0)}}',
  '#bo-trust-panel{width:220px;flex-shrink:0;background:rgba(22,33,62,.88);',
  'border-left:1.5px solid rgba(8,217,214,.25);padding:18px 16px;',
  'display:flex;flex-direction:column;gap:18px;overflow-y:auto;}',
  '#bo-trust-panel h4{margin:0;font-size:16px;color:#08D9D6;font-weight:800;',
  'text-align:center;border-bottom:1px solid rgba(8,217,214,.2);padding-bottom:8px;}',
  '.bo-ti{display:flex;flex-direction:column;gap:5px;}',
  '.bo-tl{display:flex;justify-content:space-between;font-size:14px;',
  'color:rgba(255,255,255,.8);font-weight:600;}',
  '.bo-tt{height:10px;border-radius:5px;background:rgba(255,255,255,.1);overflow:hidden;}',
  '.bo-tf{height:100%;border-radius:5px;transition:width .5s ease;width:50%;}',
  '#bo-sf{background:linear-gradient(90deg,#FF2E63,#ff6b9d);}',
  '#bo-ef{background:linear-gradient(90deg,#08D9D6,#0bc9bf);}',
  '#bo-af{background:linear-gradient(90deg,#FFD700,#ffa500);}',
  '#bo-info{padding:12px 14px;border-radius:8px;background:rgba(8,217,214,.07);',
  'border:1px solid rgba(8,217,214,.18);font-size:14px;line-height:2.0;',
  'color:rgba(255,255,255,.85);}',
  '#bo-info .bo-info-row{display:flex;align-items:flex-start;gap:6px;white-space:pre-wrap;}',
  '#bo-info .bo-info-status{margin-top:6px;padding-top:6px;',
  'border-top:1px solid rgba(8,217,214,.15);color:#08D9D6;font-weight:700;font-size:14px;}',
  '#bo-hints{margin-top:auto;padding-top:12px;border-top:1px solid rgba(255,255,255,.08);',
  'font-size:13px;color:rgba(255,255,255,.5);text-align:center;line-height:2.0;}',
  '@media(max-width:700px){#bo-trust-panel{display:none}.bo-bubble{max-width:90%}}',
].join('');

export class BattleScene extends Phaser.Scene {
  private sceneData!: BattleSceneData;
  private backendClient!: BackendClient;
  private trustSystem!: TrustSystem;
  private isWaitingForAI = false;
  private roundCount = 0;
  private messages: ChatMessage[] = [];

  // DOM refs
  private overlay!: HTMLDivElement;
  private chatEl!: HTMLDivElement;
  private inputEl!: HTMLInputElement;
  private sendBtn!: HTMLButtonElement;
  private voiceBtn!: HTMLButtonElement;
  private ttsBtn!: HTMLButtonElement;
  private sfEl!: HTMLDivElement;  // scammer fill
  private efEl!: HTMLDivElement;  // expert fill
  private afEl!: HTMLDivElement;  // alertness fill
  private spEl!: HTMLSpanElement; // scammer pct
  private epEl!: HTMLSpanElement; // expert pct
  private apEl!: HTMLSpanElement; // alertness pct
  private infoEl!: HTMLDivElement; // info panel

  // Voice
  private recognition: any = null;
  private isRecording = false;
  private finalTranscript = '';
  private silenceTimer: any = null;
  private ttsEnabled = false;
  private ttsSupported = false;
  private speechQueue: Array<{ role: 'scammer' | 'victim' | 'expert'; text: string }> = [];
  private isSpeakingTTS = false;
  private currentAudio: HTMLAudioElement | null = null;
  private currentPlayerRole: 'victim' | 'expert' | 'scammer' | 'auto' | 'observer' = 'victim';
  private currentLanguage: AppLanguage = 'zh-HK';

  constructor() { super({ key: 'BattleScene' }); }

  init(data: BattleSceneData): void {
    this.sceneData = data;
    if (data.language) {
      localization.setLanguage(data.language);
    }
    this.currentLanguage = localization.getLanguage();
    this.roundCount = 0;
    this.isWaitingForAI = false;
    this.messages = [];
    this.ttsEnabled = false;
    this.ttsSupported = typeof window !== 'undefined' && !!window.Audio;
    this.speechQueue = [];
    this.isSpeakingTTS = false;
    this.currentAudio = null;
    this.currentPlayerRole = (((data.playerRole?.id as string) ?? 'victim').toLowerCase() as 'victim' | 'expert' | 'scammer' | 'auto' | 'observer');
    this.backendClient = new BackendClient();
    this.trustSystem = new TrustSystem();
  }

  create(): void {
    const restored = this.tryRestoreState();
    this.injectCSS();
    this.buildDOM();
    this.initVoice();
    this.initTTS();
    this.setupKeys();
    if (restored) {
      this.messages.forEach(m => this.renderBubble(m));
      this.updateTrustBars();
      this.addSystemBubble('🔄 已恢復上次對話狀態');
    } else {
      this.startSession();
    }
  }

  // ─── CSS ──────────────────────────────────────────────────────────────────
  private injectCSS(): void {
    if (document.getElementById('bo-css')) return;
    const s = document.createElement('style');
    s.id = 'bo-css';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  // ─── DOM ──────────────────────────────────────────────────────────────────
  private buildDOM(): void {
    const info   = this.sceneData.scamTypeInfo;
    const role   = this.sceneData.playerRole;
    const rColor = (role as any)?.colorHex ?? (role as any)?.color ?? '#08D9D6';
    const rIcon  = (role as any)?.icon ?? '👤';

    // 根據語言選擇角色名字
    const getRoleName = () => {
      const lang = localization.getLanguage();
      if (!role) return localization.t('roleVictim');
      if (lang === 'en-US') return role.name ?? role.nameZh;
      if (lang === 'ja-JP') {
        const jaMap: Record<string, string> = { victim: '被害者', scammer: '詐欺師', expert: '専門家' };
        return jaMap[role.id] ?? role.nameZh;
      }
      if (lang === 'zh-CN') {
        const cnMap: Record<string, string> = { victim: '受害者', scammer: '骗徒', expert: '防诈专家' };
        return cnMap[role.id] ?? role.nameZh;
      }
      return role.nameZh;
    };
    const rName = getRoleName();

    // 根據語言選擇標題
    const getTitle = () => {
      const lang = localization.getLanguage();
      const icon = (info as any)?.icon ?? '⚔️';
      if (!info) return this.sceneData.scamType;
      if (lang === 'zh-CN') return `${icon} ${info.nameZhCN ?? info.nameZh}`;
      if (lang === 'en-US') return `${icon} ${info.nameEn ?? info.nameZh}`;
      if (lang === 'ja-JP') return `${icon} ${info.nameJa ?? info.nameZh}`;
      return `${icon} ${info.nameZh}`;
    };
    const title = getTitle();

    this.overlay = document.createElement('div');
    this.overlay.id = 'battle-overlay';

    // Header
    const header = this.el('div', '#bo-header');
    const backBtn = this.el('button', '#bo-back-btn') as HTMLButtonElement;
    backBtn.textContent = localization.t('battleBack');
    backBtn.addEventListener('click', () => this.closeBattle());
    const titleEl = this.el('div', '#bo-title');
    titleEl.textContent = title;
    const headerRight = this.el('div', '');
    headerRight.style.cssText = 'display:flex;align-items:center;gap:10px;';
    this.ttsBtn = this.el('button', '#bo-tts-btn') as HTMLButtonElement;
    this.ttsBtn.textContent = '🔈 語音播放';
    this.ttsBtn.title = '開啟/關閉自動語音播放';
    this.ttsBtn.addEventListener('click', () => this.toggleTTS());
    const badge = this.el('div', '');
    badge.style.cssText = `border:1.5px solid ${rColor};color:${rColor};background:rgba(22,33,62,.85);border-radius:20px;padding:4px 14px;font-size:14px;font-weight:700;`;
    badge.textContent = `${rIcon} ${rName}`;
    // Language switcher dropdown
    const langSelect = document.createElement('select');
    langSelect.style.cssText = 'background:rgba(22,33,62,.9);border:1.5px solid rgba(8,217,214,.5);color:#fff;border-radius:8px;padding:5px 10px;font-size:13px;font-weight:700;cursor:pointer;outline:none;';
    localization.getLanguageOptions().forEach(opt => {
      const option = document.createElement('option');
      option.value = opt.code;
      option.textContent = opt.label;
      option.selected = opt.code === this.currentLanguage;
      langSelect.appendChild(option);
    });
    // 監聽外部語言變化（例如從地圖切換後進入對戰）
    const syncLangSelect = (lang: AppLanguage) => {
      langSelect.value = lang;
      this.currentLanguage = lang;
    };
    localization.onLanguageChange(syncLangSelect);
    langSelect.addEventListener('change', () => {
      const newLang = langSelect.value as AppLanguage;
      this.currentLanguage = newLang;
      localization.setLanguage(newLang);
      // 即時更新所有 DOM 文字
      (this.inputEl as HTMLInputElement).placeholder = localization.t('battleInputPlaceholder');
      backBtn.textContent = localization.t('battleBack');
      titleEl.textContent = getTitle();
      ph4.textContent = localization.t('trustPanel');
      hints.innerHTML = localization.getLanguage() === 'en-US'
        ? 'F1 Victim · F2 Scammer · F3 Expert<br>ESC Back to Map'
        : localization.getLanguage() === 'ja-JP'
        ? 'F1 被害者 · F2 詐欺師 · F3 専門家<br>ESC マップへ戻る'
        : localization.getLanguage() === 'zh-CN'
        ? 'F1 受害者 · F2 骗子 · F3 专家<br>ESC 返回地图'
        : 'F1 受害人 · F2 騙徒 · F3 專家<br>ESC 返回地圖';
      this.updateTTSButton();
      // 更新信任面板 label
      scammerLabelEl.childNodes[0].textContent = localization.getLanguage() === 'en-US' ? '🎭 Scammer Trust'
        : localization.getLanguage() === 'ja-JP' ? '🎭 詐欺師への信頼'
        : localization.getLanguage() === 'zh-CN' ? '🎭 骗徒信任'
        : '🎭 騙徒信任';
      expertLabelEl.childNodes[0].textContent = localization.getLanguage() === 'en-US' ? '🛡️ Expert Trust'
        : localization.getLanguage() === 'ja-JP' ? '🛡️ 専門家への信頼'
        : localization.getLanguage() === 'zh-CN' ? '🛡️ 专家信任'
        : '🛡️ 專家信任';
      alertLabelEl.childNodes[0].textContent = localization.getLanguage() === 'en-US' ? '⚠️ Alertness'
        : localization.getLanguage() === 'ja-JP' ? '⚠️ 警戒度'
        : localization.getLanguage() === 'zh-CN' ? '⚠️ 警觉性'
        : '⚠️ 警覺性';
    });
    // 場景關閉時移除監聽器
    this.events.once('shutdown', () => localization.offLanguageChange(syncLangSelect));
    this.events.once('destroy', () => localization.offLanguageChange(syncLangSelect));
    headerRight.append(langSelect, this.ttsBtn, badge);
    header.append(backBtn, titleEl, headerRight);

    // Body
    const body = this.el('div', '#bo-body');
    const chatWrap = this.el('div', '#bo-chat-wrap');
    this.chatEl = this.el('div', '#bo-messages') as HTMLDivElement;

    // Input bar
    const inputBar = this.el('div', '#bo-input-bar');
    this.voiceBtn = this.el('button', '#bo-voice-btn') as HTMLButtonElement;
    this.voiceBtn.className = 'bo-btn';
    this.voiceBtn.title = '語音輸入';
    this.voiceBtn.textContent = '🎤';
    this.voiceBtn.addEventListener('click', () => this.toggleVoice());
    this.inputEl = this.el('input', '#bo-input') as HTMLInputElement;
    (this.inputEl as HTMLInputElement).type = 'text';
    (this.inputEl as HTMLInputElement).placeholder = localization.t('battleInputPlaceholder');
    this.sendBtn = this.el('button', '#bo-send-btn') as HTMLButtonElement;
    this.sendBtn.className = 'bo-btn';
    this.sendBtn.title = '發送';
    this.sendBtn.textContent = '▶';
    this.sendBtn.addEventListener('click', () => this.sendMessage());
    this.inputEl.addEventListener('keydown', (e: KeyboardEvent) => { if (e.key === 'Enter') this.sendMessage(); });
    inputBar.append(this.voiceBtn, this.inputEl, this.sendBtn);
    chatWrap.append(this.chatEl, inputBar);

    // Trust panel
    const panel = this.el('div', '#bo-trust-panel');
    const ph4 = document.createElement('h4');
    ph4.textContent = localization.t('trustPanel');
    panel.appendChild(ph4);

    // 根據當前語言初始化標籤
    const _lang = localization.getLanguage();
    const _scammerLabel = _lang === 'en-US' ? '🎭 Scammer Trust'
      : _lang === 'ja-JP' ? '🎭 詐欺師への信頼'
      : _lang === 'zh-CN' ? '🎭 骗徒信任'
      : '🎭 騙徒信任';
    const _expertLabel = _lang === 'en-US' ? '🛡️ Expert Trust'
      : _lang === 'ja-JP' ? '🛡️ 専門家への信頼'
      : _lang === 'zh-CN' ? '🛡️ 专家信任'
      : '🛡️ 專家信任';
    const _alertLabel = _lang === 'en-US' ? '⚠️ Alertness'
      : _lang === 'ja-JP' ? '⚠️ 警戒度'
      : _lang === 'zh-CN' ? '⚠️ 警觉性'
      : '⚠️ 警覺性';

    const scammerItem = this.makeTrustItem(_scammerLabel, 'bo-sf', 'bo-sp');
    const expertItem = this.makeTrustItem(_expertLabel, 'bo-ef', 'bo-ep');
    const alertItem = this.makeTrustItem(_alertLabel, 'bo-af', 'bo-ap');
    // 保存 label span 引用以便語言切換時更新
    const scammerLabelEl = scammerItem.querySelector('.bo-tl') as HTMLElement;
    const expertLabelEl = expertItem.querySelector('.bo-tl') as HTMLElement;
    const alertLabelEl = alertItem.querySelector('.bo-tl') as HTMLElement;
    panel.appendChild(scammerItem);
    panel.appendChild(expertItem);
    panel.appendChild(alertItem);
    const hints = this.el('div', '#bo-hints');
    hints.innerHTML = 'F1 受害人 · F2 騙徒 · F3 專家<br>ESC 返回地圖';
    const infoBox = this.el('div', '#bo-info') as HTMLDivElement;
    infoBox.innerHTML = '<div class="bo-info-status">等待連接...</div>';
    this.infoEl = infoBox;  // 直接綁定，不依賴 getElementById
    panel.appendChild(infoBox);
    panel.appendChild(hints);
    body.append(chatWrap, panel);

    this.overlay.append(header, body);
    document.body.appendChild(this.overlay);

    // bind trust bar refs by id
    this.sfEl = document.getElementById('bo-sf') as HTMLDivElement;
    this.efEl = document.getElementById('bo-ef') as HTMLDivElement;
    this.afEl = document.getElementById('bo-af') as HTMLDivElement;
    this.spEl = document.getElementById('bo-sp') as HTMLSpanElement;
    this.epEl = document.getElementById('bo-ep') as HTMLSpanElement;
    this.apEl = document.getElementById('bo-ap') as HTMLSpanElement;
    // infoEl 已在 buildDOM 中直接綁定

    this.inputEl.focus();
  }

  private el(tag: string, id: string): HTMLElement {
    const e = document.createElement(tag);
    if (id.startsWith('#')) e.id = id.slice(1);
    return e;
  }

  private makeTrustItem(label: string, fillId: string, pctId: string): HTMLElement {
    const item = document.createElement('div');
    item.className = 'bo-ti';
    const lrow = document.createElement('div');
    lrow.className = 'bo-tl';
    const lspan = document.createElement('span');
    lspan.textContent = label;
    const pspan = document.createElement('span');
    pspan.id = pctId;
    pspan.textContent = '50%';
    lrow.append(lspan, pspan);
    const track = document.createElement('div');
    track.className = 'bo-tt';
    const fill = document.createElement('div');
    fill.id = fillId;
    fill.className = 'bo-tf';
    track.appendChild(fill);
    item.append(lrow, track);
    return item;
  }

  // ─── Keyboard shortcuts ────────────────────────────────────────────────────
  private setupKeys(): void {
    this.input.keyboard?.on('keydown-ESC', () => this.closeBattle());
    this.input.keyboard?.on('keydown-F1',  () => this.switchRole('victim'));
    this.input.keyboard?.on('keydown-F2',  () => this.switchRole('scammer'));
    this.input.keyboard?.on('keydown-F3',  () => this.switchRole('expert'));

    // 阻止 Phaser 攔截 input 內的鍵盤事件（WASD 等字母鍵正常輸入）
    this.inputEl.addEventListener('keydown', (e: KeyboardEvent) => {
      e.stopPropagation();
    });
    this.inputEl.addEventListener('keyup', (e: KeyboardEvent) => {
      e.stopPropagation();
    });
    this.inputEl.addEventListener('keypress', (e: KeyboardEvent) => {
      e.stopPropagation();
    });
  }

  private async switchRole(newRole: 'victim' | 'expert' | 'scammer'): Promise<void> {
    if (this.isWaitingForAI) return;
    const names = {
      victim: localization.t('roleVictim'),
      expert: localization.t('roleExpert'),
      scammer: localization.t('roleScammer')
    };
    try {
      const result = await this.backendClient.switchRole(newRole, this.currentLanguage);
      if (result.success) {
        this.currentPlayerRole = newRole;
        const switchMsg = localization.getLanguage() === 'en-US' ? `🔄 Switched to ${names[newRole]} mode`
          : localization.getLanguage() === 'ja-JP' ? `🔄 ${names[newRole]}モードに切り替えました`
          : localization.getLanguage() === 'zh-CN' ? `🔄 已切换到 ${names[newRole]} 模式`
          : `🔄 已切換到 ${names[newRole]} 模式`;
        this.addSystemBubble(switchMsg);
      }
    } catch (e) {
      this.addSystemBubble('❌ 角色切換失敗');
    }
  }

  // ─── Session ───────────────────────────────────────────────────────────────
  private async startSession(): Promise<void> {
    const info = this.sceneData.scamTypeInfo;
    const _lang = localization.getLanguage();
    const roleZh = (() => {
      const r = this.sceneData.playerRole;
      if (!r) return _lang === 'en-US' ? 'Victim' : _lang === 'ja-JP' ? '被害者' : '受害者';
      if (_lang === 'en-US') return r.name ?? r.nameZh;
      if (_lang === 'ja-JP') return ({ victim: '被害者', scammer: '詐欺師', expert: '専門家' }[r.id] ?? r.nameZh);
      if (_lang === 'zh-CN') return ({ victim: '受害者', scammer: '骗徒', expert: '防诈专家' }[r.id] ?? r.nameZh);
      return r.nameZh;
    })();
    const scamZh = (() => {
      if (!info) return this.sceneData.scamType;
      if (_lang === 'en-US') return info.nameEn ?? info.nameZh;
      if (_lang === 'ja-JP') return (info as any).nameJa ?? info.nameZh;
      if (_lang === 'zh-CN') return (info as any).nameZhCN ?? info.nameZh;
      return info.nameZh;
    })();

    // 在信任度面板下方顯示遊戲資訊（不佔用聊天區）
    const setInfo = (status: string) => {
      if (!this.infoEl) return;
      this.infoEl.innerHTML =
        `<div class="bo-info-row">🎯 <span>${scamZh}</span></div>` +
        `<div class="bo-info-row">👤 <span>${roleZh}</span></div>` +
        `<div class="bo-info-status">${status}</div>`;
    };

    setInfo(localization.t('infoConnecting'));

    const connected = await this.backendClient.checkConnection();
    if (!connected) {
      setInfo(localization.t('infoFailed'));
      return;
    }
    try {
      const result = await this.backendClient.startThreeWaySession({
        scamType: this.sceneData.scamType,
        playerRole: (this.sceneData.playerRole?.id as any) ?? 'victim',
        language: this.currentLanguage,
        victimPersona: 'average'
      });
      setInfo(localization.t('infoReady'));
      if (result.openingMessages?.length) {
        for (const msg of result.openingMessages) {
          await this.delay(400);
          this.addAIBubble(msg.role, msg.content);
        }
      }
      this.saveState();
    } catch (err) {
      console.error('[BattleScene] startSession error:', err);
      if (this.infoEl) {
        const s = this.infoEl.querySelector('.bo-info-status');
        if (s) s.textContent = '❌ ' + localization.t('infoFailed').replace('⚠️ ', '') + '，請重試';
      }
    }
  }

  // ─── Send message ──────────────────────────────────────────────────────────
  private async sendMessage(): Promise<void> {
    const text = this.inputEl.value.trim();
    if (!text || this.isWaitingForAI) return;
    
      this.isWaitingForAI = true;
      this.roundCount++;
    this.inputEl.value = '';
    this.setInputEnabled(false);

    const role = this.sceneData.playerRole;
    const lang = localization.getLanguage();
    const playerName = role ? (
      lang === 'en-US' ? (role.name ?? role.nameZh) :
      lang === 'ja-JP' ? ({ victim: '被害者', scammer: '詐欺師', expert: '専門家' }[role.id] ?? role.nameZh) :
      lang === 'zh-CN' ? ({ victim: '受害者', scammer: '骗徒', expert: '防诈专家' }[role.id] ?? role.nameZh) :
      role.nameZh
    ) : (lang === 'en-US' ? 'You' : lang === 'ja-JP' ? 'あなた' : lang === 'zh-CN' ? '你' : '你');
    this.addBubble({
      speaker: playerName,
      text,
      color: (role as any)?.color ?? '#08D9D6',
      side: 'right',
      emoji: (role as any)?.icon ?? '👤'
    });

    const typingEl = this.addTypingIndicator();

    try {
      let response: ThreeWayMessageResponse;
      try {
        response = await this.backendClient.sendThreeWayMessage(text, this.currentLanguage);
      } catch (fetchErr: any) {
        // 404 = session expired (e.g. backend restarted). Clear stale state and re-init.
        if (fetchErr?.message?.includes('404')) {
          typingEl.remove();
          this.clearState();
          this.addSystemBubble('⚠️ ' + (localization.getLanguage() === 'en-US' ? 'Session expired, reconnecting...' : localization.getLanguage() === 'ja-JP' ? 'セッションが切れました。再接続中...' : localization.getLanguage() === 'zh-CN' ? '会话已过期，正在重新连接...' : '會話已過期，正在重新連接...'));
          this.isWaitingForAI = false;
          this.setInputEnabled(true);
          await this.startSession();
          return;
        }
        throw fetchErr;
      }
      typingEl.remove();

      if (response.success && response.replies) {
          for (let i = 0; i < response.replies.length; i++) {
          if (i > 0) await this.delay(500);
          const r = response.replies[i];
          this.addAIBubble(r.speaker, r.message);
        }
          if (response.trust_data) {
            this.trustSystem.updateTrustDirect(
              response.trust_data.trust_in_scammer,
              response.trust_data.trust_in_expert,
              response.trust_data.alertness
            );
          this.updateTrustBars();
        }
        if (response.game_status?.game_over) {
          const gs = response.game_status;
          console.log('[BattleScene] 遊戲結束，game_status:', gs);

          const playerMode = (this.sceneData.playerRole?.id ?? 'victim') as 'victim' | 'expert' | 'scammer';
          const trust = response.trust_data ?? gs.final_trust;
          const trustScammer = trust?.trust_in_scammer ?? 50;
          const trustExpert = trust?.trust_in_expert ?? 50;
          const alertness = trust?.alertness ?? 50;

          let outcome: 'expert_win' | 'scammer_win';
          let msg: string;

          // 先用前端當前信任度作最終裁決（100 分規則）
          const localTrust = this.trustSystem.getAllTrustData();
          if (localTrust.trustInExpert >= 100 && localTrust.trustInScammer < 100) {
            outcome = 'expert_win';
          } else if (localTrust.trustInScammer >= 100 && localTrust.trustInExpert < 100) {
            outcome = 'scammer_win';
          } else if (trustExpert >= 100 && trustScammer < 100) {
            outcome = 'expert_win';
          } else if (trustScammer >= 100 && trustExpert < 100) {
            outcome = 'scammer_win';
          }
          // 再吃後端明確 outcome/winner 訊號
          else if ((gs as any).outcome === 'expert_win' || gs.winner === 'expert_win' || gs.winner === 'expert') {
            outcome = 'expert_win';
          } else if ((gs as any).outcome === 'scammer_win' || gs.winner === 'scammer_win' || gs.winner === 'scammer') {
            outcome = 'scammer_win';
          } else if ((gs.reason ?? '').includes('專家勝')) {
            outcome = 'expert_win';
          } else if ((gs.reason ?? '').includes('騙徒勝') || (gs.reason ?? '').includes('被騙')) {
            outcome = 'scammer_win';
          } else if (gs.winner === 'player') {
            outcome = playerMode === 'scammer' ? 'scammer_win' : 'expert_win';
          } else if (gs.winner === 'ai') {
            outcome = playerMode === 'scammer' ? 'expert_win' : 'scammer_win';
          } else {
            outcome = trustScammer >= 70 ? 'scammer_win' : 'expert_win';
          }

          console.log('[BattleScene] outcome debug', {
            backendOutcome: (gs as any).outcome,
            winner: gs.winner,
            reason: gs.reason,
            trustScammer,
            trustExpert,
            alertness,
            localTrust,
            resolvedOutcome: outcome,
          });

          if (outcome === 'expert_win') {
            msg = `🎉 專家陣營勝利！${gs.reason ?? ''}`;
          } else {
            msg = `💀 騙徒陣營勝利！${gs.reason ?? ''}`;
          }

          console.log('[BattleScene] 決定的 outcome:', outcome, {
            winner: gs.winner,
            trustScammer,
            trustExpert,
            alertness,
          });
          this.addSystemBubble(msg);
          this.setInputEnabled(false);
          this.clearState();
          await this.delay(2000);
          this.endBattle(outcome);
          return;
        }
      }
      this.saveState();
    } catch (err) {
      typingEl.remove();
      console.error('[BattleScene] sendMessage error:', err);
      this.addSystemBubble('❌ ' + (localization.getLanguage() === 'en-US' ? 'Send failed, please retry' : localization.getLanguage() === 'ja-JP' ? '送信失敗、再試行してください' : localization.getLanguage() === 'zh-CN' ? '发送失败，请重试' : '發送失敗，請重試'));
    } finally {
            this.isWaitingForAI = false;
      this.setInputEnabled(true);
      this.inputEl.focus();
    }
  }

  // ─── Bubble helpers ────────────────────────────────────────────────────────
  private addAIBubble(speakerRole: string, text: string): void {
    const rawRole = (speakerRole ?? '').toLowerCase().trim();
    const roleAlias: Record<string, 'scammer' | 'expert' | 'victim'> = {
      'ai-d': 'scammer',
      'aid': 'scammer',
      '騙徒': 'scammer',
      '骗徒': 'scammer',
      'scammer': 'scammer',
      'ai-c': 'expert',
      'aic': 'expert',
      '專家': 'expert',
      '专家': 'expert',
      '防詐專家': 'expert',
      '防诈专家': 'expert',
      'expert': 'expert',
      'ai-b': 'victim',
      'aib': 'victim',
      '受害者': 'victim',
      'victim': 'victim',
    };
    const normalizedRole = roleAlias[rawRole] ?? rawRole;

    const lang = localization.getLanguage();
    const getRoleName = (role: string) => {
      if (role === 'scammer') {
        return lang === 'en-US' ? 'Scammer' : lang === 'ja-JP' ? '詐欺師' : lang === 'zh-CN' ? '骗徒' : '騙徒';
      }
      if (role === 'expert') {
        return lang === 'en-US' ? 'Expert' : lang === 'ja-JP' ? '専門家' : lang === 'zh-CN' ? '防诈专家' : '防詐專家';
      }
      if (role === 'victim') {
        return lang === 'en-US' ? 'Victim' : lang === 'ja-JP' ? '被害者' : lang === 'zh-CN' ? '受害者' : '受害者';
      }
      return speakerRole;
    };

    const map: Record<string, { name: string; color: string; emoji: string }> = {
      scammer: { name: getRoleName('scammer'), color: '#FF2E63', emoji: '🎭' },
      expert:  { name: getRoleName('expert'),  color: '#08D9D6', emoji: '🛡️' },
      victim:  { name: getRoleName('victim'),  color: '#FFD93D', emoji: '👤' }
    };
    const info = map[normalizedRole] ?? { name: speakerRole, color: '#aaa', emoji: '🤖' };
    this.addBubble({ speaker: info.name, text, color: info.color, side: 'left', emoji: info.emoji });
    this.speakTextForRole(normalizedRole, text);
  }

  private addBubble(msg: ChatMessage): void {
    this.messages.push(msg);
    this.renderBubble(msg);
  }

  private renderBubble(msg: ChatMessage): void {
    if (msg.side === 'system') { this.addSystemBubble(msg.text); return; }

    const wrap = document.createElement('div');
    wrap.className = `bo-bubble ${msg.side}`;

    const avatar = document.createElement('div');
    avatar.className = 'bo-avatar';
    avatar.style.borderColor = msg.color + '80';
    avatar.textContent = msg.emoji;

    const content = document.createElement('div');
    content.className = 'bo-content';

    const speaker = document.createElement('div');
    speaker.className = 'bo-speaker';
    speaker.style.color = msg.color;
    speaker.textContent = msg.speaker;

    const bubble = document.createElement('div');
    bubble.className = 'bo-text';
    if (msg.side === 'right') {
      bubble.style.background = `linear-gradient(135deg,${msg.color}22,${msg.color}11)`;
      bubble.style.borderColor = msg.color + '40';
    }
    bubble.textContent = msg.text;

    content.append(speaker, bubble);
    wrap.append(msg.side === 'left' ? avatar : content, msg.side === 'left' ? content : avatar);
    this.chatEl.appendChild(wrap);
    this.scrollBottom();
  }

  private addSystemBubble(text: string): void {
    const wrap = document.createElement('div');
    wrap.className = 'bo-bubble system';
    const b = document.createElement('div');
    b.className = 'bo-text';
    b.textContent = text;
    wrap.appendChild(b);
    this.chatEl?.appendChild(wrap);
    this.scrollBottom();
  }

  private addTypingIndicator(): HTMLElement {
    const wrap = document.createElement('div');
    wrap.className = 'bo-bubble left bo-typing';
    const av = document.createElement('div'); av.className = 'bo-avatar'; av.textContent = '🤖';
    const co = document.createElement('div'); co.className = 'bo-content';
    const tx = document.createElement('div'); tx.className = 'bo-text';
    [0,1,2].forEach(() => { const d = document.createElement('div'); d.className = 'bo-dot'; tx.appendChild(d); });
    co.appendChild(tx); wrap.append(av, co);
    this.chatEl.appendChild(wrap);
    this.scrollBottom();
    return wrap;
  }

  private scrollBottom(): void {
    if (this.chatEl) this.chatEl.scrollTop = this.chatEl.scrollHeight;
  }

  // ─── Trust bars ────────────────────────────────────────────────────────────
  private updateTrustBars(): void {
    const td = this.trustSystem.getAllTrustData();
    const set = (fill: HTMLDivElement, pct: HTMLSpanElement, val: number) => {
      const v = Math.round(Math.max(0, Math.min(100, val)));
      fill.style.width = `${v}%`;
      pct.textContent  = `${v}%`;
    };
    set(this.sfEl, this.spEl, td.trustInScammer);
    set(this.efEl, this.epEl, td.trustInExpert);
    set(this.afEl, this.apEl, td.alertness);
  }

  // ─── Voice ─────────────────────────────────────────────────────────────────
  private initVoice(): void {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    this.recognition = new SR();
    this.recognition.lang = localization.getSpeechRecognitionLanguage();
    this.recognition.continuous = true;
    this.recognition.interimResults = true;

    this.recognition.onresult = (ev: any) => {
      if (this.silenceTimer) clearTimeout(this.silenceTimer);
      let interim = '', current = '';
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const t = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) current += t; else interim += t;
      }
      if (current) this.finalTranscript += current;
      this.inputEl.value = this.finalTranscript + interim;
      this.silenceTimer = setTimeout(() => { if (this.isRecording) this.recognition.stop(); }, 2000);
    };
    this.recognition.onerror = (ev: any) => {
      if (ev.error !== 'aborted') this.addSystemBubble(`${localization.t('voiceError')}${ev.error}`);
      this.stopRecording();
    };
    this.recognition.onend = () => {
      if (this.silenceTimer) clearTimeout(this.silenceTimer);
      if (this.finalTranscript) this.inputEl.value = this.finalTranscript;
      this.stopRecording();
    };
  }

  private toggleVoice(): void {
    if (!this.recognition) { alert(localization.getLanguage() === 'en-US' ? 'Your browser does not support voice input. Please use Chrome / Edge.' : localization.getLanguage() === 'ja-JP' ? 'お使いのブラウザは音声入力に対応していません。Chrome / Edgeをご利用ください。' : localization.getLanguage() === 'zh-CN' ? '你的浏览器不支持语音输入，请使用 Chrome / Edge' : '你的瀏覽器不支持語音輸入，請使用 Chrome / Edge'); return; }
    if (this.isRecording) {
      this.recognition.stop();
      } else {
      this.finalTranscript = '';
      try {
        this.recognition.start();
        this.isRecording = true;
        this.voiceBtn.classList.add('recording');
        this.voiceBtn.title = '停止錄音（2秒無聲自動停止）';
      } catch (_) { this.addSystemBubble('⚠️ 無法啟動語音輸入'); }
    }
  }

  private stopRecording(): void {
    this.isRecording = false;
    this.voiceBtn?.classList.remove('recording');
    if (this.voiceBtn) this.voiceBtn.title = '語音輸入';
  }

  private initTTS(): void {
    this.ttsSupported = typeof window !== 'undefined' && !!window.Audio;
    if (!this.ttsSupported) {
      this.ttsEnabled = false;
    }
    this.updateTTSButton();
  }

  private toggleTTS(): void {
    if (!this.ttsSupported) {
      this.addSystemBubble('⚠️ 你的瀏覽器不支持語音播放');
      return;
    }
    this.ttsEnabled = !this.ttsEnabled;
    if (!this.ttsEnabled) {
      this.speechQueue = [];
      this.isSpeakingTTS = false;
      if (this.currentAudio) {
        this.currentAudio.pause();
        this.currentAudio = null;
      }
    }
    this.updateTTSButton();
    this.saveState();
  }

  private updateTTSButton(): void {
    if (!this.ttsBtn) return;

    if (!this.ttsSupported) {
      this.ttsBtn.disabled = true;
      this.ttsBtn.classList.remove('on');
      this.ttsBtn.textContent = '🔇 無語音';
      this.ttsBtn.title = '瀏覽器不支持語音播放';
      return;
    }

    this.ttsBtn.disabled = false;
    this.ttsBtn.classList.toggle('on', this.ttsEnabled);
    this.ttsBtn.textContent = this.ttsEnabled ? localization.t('ttsOn') : localization.t('ttsOff');
    this.ttsBtn.title = this.ttsEnabled
      ? localization.t('ttsTitleOn')
      : localization.t('ttsTitleOff');
  }

  private speakTextForRole(speakerRole: string, text: string): void {
    if (!this.shouldSpeakRole(speakerRole)) return;

    const role = speakerRole as 'scammer' | 'victim' | 'expert';
    this.enqueueSpeech(role, text);

    if ((window as any).__BATTLE_TTS_DEBUG__) {
      this.addSystemBubble(`🔊 TTS排隊：${role} (${text.slice(0, 16)}...)`);
    }
  }

  private shouldSpeakRole(speakerRole: string): boolean {
    if (!this.ttsEnabled || !this.ttsSupported) return false;

    if (this.currentPlayerRole === 'auto' || this.currentPlayerRole === 'observer') {
      return speakerRole === 'scammer' || speakerRole === 'victim' || speakerRole === 'expert';
    }

    if (this.currentPlayerRole === 'victim') {
      return speakerRole === 'scammer' || speakerRole === 'expert';
    }
    if (this.currentPlayerRole === 'expert') {
      return speakerRole === 'scammer' || speakerRole === 'victim';
    }
    if (this.currentPlayerRole === 'scammer') {
      return speakerRole === 'victim' || speakerRole === 'expert';
    }

    return false;
  }

  private enqueueSpeech(role: 'scammer' | 'victim' | 'expert', text: string): void {
    const clean = text?.trim();
    if (!clean) return;

    this.speechQueue.push({ role, text: clean });
    this.playNextSpeech();
  }

  private async playNextSpeech(): Promise<void> {
    if (this.isSpeakingTTS || !this.ttsEnabled || !this.ttsSupported) return;

    const next = this.speechQueue.shift();
    if (!next) return;

    this.isSpeakingTTS = true;

    try {
      const ttsResult: TTSResponse = await this.backendClient.synthesizeTTS(
        next.role,
        next.text,
        this.currentLanguage
      );
      const audio = new Audio(`data:${ttsResult.mime_type};base64,${ttsResult.audio_base64}`);
      this.currentAudio = audio;

      if ((window as any).__BATTLE_TTS_DEBUG__) {
        this.addSystemBubble(`🎧 TTS播放：${next.role} · ${ttsResult.voice_name}`);
      }

      audio.onended = () => {
        this.currentAudio = null;
        this.isSpeakingTTS = false;
        this.playNextSpeech();
      };
      audio.onerror = () => {
        this.currentAudio = null;
        this.isSpeakingTTS = false;
        this.addSystemBubble('⚠️ TTS音頻播放失敗');
        this.playNextSpeech();
      };

      await audio.play();
    } catch (error) {
      const msg = error instanceof Error ? error.message : '未知錯誤';
      console.warn('[BattleScene] TTS playback failed:', error);
      // 區分常見錯誤類型，提示更清晰
      let hint = '';
      if (msg.includes('403') || msg.toLowerCase().includes('permission') || msg.toLowerCase().includes('iam')) {
        hint = '（Cloud Run 服務帳號缺少 roles/cloudtts.user 權限）';
      } else if (msg.includes('404') || msg.toLowerCase().includes('voice')) {
        hint = '（聲音包不可用，請確認 yue-HK 粵語包已啟用）';
      } else if (msg.includes('500')) {
        hint = '（後端 TTS 服務錯誤，請檢查 /api/tts/test）';
      }
      this.addSystemBubble(`⚠️ TTS語音失敗${hint}`);
      this.currentAudio = null;
      this.isSpeakingTTS = false;
      this.playNextSpeech();
    }
  }

  // ─── Persistence ───────────────────────────────────────────────────────────
  private saveState(): void {
    const td = this.trustSystem.getAllTrustData();
    const state: SavedState = {
      sessionId: this.backendClient.getSessionId(),
      scamType: this.sceneData.scamType,
      messages: this.messages,
      trust: { s: td.trustInScammer, e: td.trustInExpert, a: td.alertness },
      rounds: this.roundCount,
      ttsEnabled: this.ttsEnabled,
      language: this.currentLanguage
    };
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (_) {}
  }

  private tryRestoreState(): boolean {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return false;
      const state: SavedState = JSON.parse(raw);
      if (state.scamType !== this.sceneData.scamType) return false;
      this.messages = state.messages ?? [];
      this.roundCount = state.rounds ?? 0;
      this.ttsEnabled = !!state.ttsEnabled;
      if (state.language) {
        this.currentLanguage = state.language;
        localization.setLanguage(state.language);
      }
      this.trustSystem.updateTrustDirect(state.trust.s, state.trust.e, state.trust.a);
      if (state.sessionId) (this.backendClient as any).sessionId = state.sessionId;
      return true;
    } catch (_) { return false; }
  }

  private clearState(): void { sessionStorage.removeItem(STORAGE_KEY); }

  // ─── Lifecycle ──────────────────────────────────────────────────────────────
  private setInputEnabled(on: boolean): void {
    this.inputEl.disabled  = !on;
    this.sendBtn.disabled  = !on;
    this.voiceBtn.disabled = !on;
    if (this.ttsBtn) this.ttsBtn.disabled = !this.ttsSupported;
  }

  private endBattle(outcome: string): void {
    this.scene.start('ResultScene', {
      outcome,
      playerRole: this.currentPlayerRole,
      scamType: this.sceneData.scamTypeInfo,
      trustData: this.trustSystem.getAllTrustData(),
      roundCount: this.roundCount,
      analysis: {
        success: true,
        session_id: '',
        analysis: {
          scammer_score: 0,
          expert_score: 0,
          outcome: outcome
        },
        conversation_count: this.roundCount
      }
    });
    this.destroyDOM();
  }

  private closeBattle(): void {
    this.saveState();
    try { this.backendClient.endSession(); } catch (_) {}
    this.destroyDOM();
    // Restart WorldMapScene to pick up new language setting
    this.scene.stop('BattleScene');
    this.scene.stop('WorldMapScene');
    this.scene.start('WorldMapScene');
  }

  private destroyDOM(): void {
    if (this.recognition) { try { this.recognition.abort(); } catch (_) {} }
    if (this.currentAudio) {
      try { this.currentAudio.pause(); } catch (_) {}
      this.currentAudio = null;
    }
    this.speechQueue = [];
    this.isSpeakingTTS = false;
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    if (this.overlay?.parentNode) this.overlay.parentNode.removeChild(this.overlay);
  }

  private delay(ms: number): Promise<void> { return new Promise(r => setTimeout(r, ms)); }

  shutdown(): void {
    this.destroyDOM();
    this.input.keyboard?.removeAllListeners();
  }
}
