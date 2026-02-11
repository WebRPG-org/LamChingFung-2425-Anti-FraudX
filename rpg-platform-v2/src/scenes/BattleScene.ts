import Phaser from 'phaser';
import { Role } from '../systems/RoleManager';
import { ScamType } from '../types/ScamTypes';
import { BackendClient } from '../services/BackendClient';
import { TrustSystem } from '../systems/TrustSystem';

interface BattleSceneData {
  scamType: string;           // 騙案類型 ID
  scamTypeInfo: ScamType;     // 完整騙案類型資訊
  playerRole: Role;           // 玩家角色
}

export class BattleScene extends Phaser.Scene {
  private data!: BattleSceneData;
  private messages: Array<{ speaker: string; text: string; color: string }> = [];
  private messageContainer!: Phaser.GameObjects.Container;
  private inputField!: HTMLInputElement;
  private inputContainer!: Phaser.GameObjects.Container;
  
  // Backend 整合
  private backendClient!: BackendClient;
  private trustSystem!: TrustSystem;
  private isWaitingForAI: boolean = false;
  private roundCount: number = 0;
  
  // 信任度 UI
  private trustMeters!: Phaser.GameObjects.Container;
  private scammerTrustBar!: Phaser.GameObjects.Rectangle;
  private expertTrustBar!: Phaser.GameObjects.Rectangle;
  private alertnessBar!: Phaser.GameObjects.Rectangle;
  private scammerTrustText!: Phaser.GameObjects.Text;
  private expertTrustText!: Phaser.GameObjects.Text;
  private alertnessText!: Phaser.GameObjects.Text;
  
  // 滾動條相關
  private scrollBar!: Phaser.GameObjects.Rectangle;
  private scrollThumb!: Phaser.GameObjects.Rectangle;
  private messageAreaHeight!: number;
  private scrollOffset: number = 0;
  private maxScrollOffset: number = 0;
  private isDraggingScroll: boolean = false;
  private messageAreaMask!: Phaser.GameObjects.Graphics;

  constructor() {
    super({ key: 'BattleScene' });
  }

  async init(data: BattleSceneData): Promise<void> {
    this.data = data;
    this.messages = [];
    this.roundCount = 0;
    this.isWaitingForAI = false;
    this.scrollOffset = 0;
    this.maxScrollOffset = 0;
    this.isDraggingScroll = false;
    
    // 初始化 Backend 客戶端
    this.backendClient = new BackendClient();
    this.trustSystem = new TrustSystem();
    
    console.log('[BattleScene] 初始化對話場景:', this.data.scamTypeInfo.nameZh);
  }

  async create(): Promise<void> {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Modern gradient background
    this.createModernBackground();

    // Header with glass morphism
    this.createModernHeader();

    // 創建信任度計量表
    this.createTrustMeters();

    // Message area with modern design
    this.createModernMessageArea();

    // Input area with modern styling
    this.createModernInputArea();

    // 設置鍵盤快捷鍵（1, 2, 3 切換角色）
    this.setupKeyboardShortcuts();

    // 初始化 Backend 會話
    await this.initializeBackendSession();

    // Initial messages with animation
    this.addSystemMessage(`🎯 遭遇：${this.data.scamTypeInfo.nameZh}`);
    this.addSystemMessage(`📋 描述：${this.data.scamTypeInfo.description}`);
    this.addSystemMessage(`⚠️ 危險等級：${'⭐'.repeat(this.data.scamTypeInfo.dangerLevel)}`);
    this.addSystemMessage(`👤 你的角色：${this.data.playerRole.nameZh}`);
    this.addSystemMessage(`💡 提示：按 F1=受害人, F2=騙徒, F3=專家 切換角色`);
    
    // 顯示開場消息（根據角色決定）
    await this.showOpeningMessages();
  }

  /**
   * 設置鍵盤快捷鍵
   */
  private setupKeyboardShortcuts(): void {
    // 按鍵 F1: 切換到受害人模式
    this.input.keyboard?.on('keydown-F1', () => {
      this.switchToRole('victim');
    });

    // 按鍵 F2: 切換到騙徒模式
    this.input.keyboard?.on('keydown-F2', () => {
      this.switchToRole('scammer');
    });

    // 按鍵 F3: 切換到專家模式
    this.input.keyboard?.on('keydown-F3', () => {
      this.switchToRole('expert');
    });

    console.log('[BattleScene] 鍵盤快捷鍵已設置 (F1=受害人, F2=騙徒, F3=專家)');
  }

  /**
   * 切換角色
   */
  private async switchToRole(newRole: 'victim' | 'expert' | 'scammer'): Promise<void> {
    try {
      // 防止重複切換
      if (this.isWaitingForAI) {
        this.addSystemMessage('⚠️ 請等待 AI 回應完成後再切換角色');
        return;
      }

      const roleNames = {
        victim: '受害人',
        expert: '專家',
        scammer: '騙徒'
      };

      this.addSystemMessage(`🔄 正在切換到 ${roleNames[newRole]} 模式...`);

      const result = await this.backendClient.switchRole(newRole);

      if (result.success) {
        this.data.playerRole = {
          id: newRole,
          nameZh: roleNames[newRole],
          nameEn: newRole.charAt(0).toUpperCase() + newRole.slice(1),
          description: result.mode_info.description
        };

        this.addSystemMessage(`✅ ${result.message}`);
        this.addSystemMessage(`👤 你現在是：${roleNames[newRole]}`);
        
        console.log('[BattleScene] 角色切換成功:', result);
      } else {
        this.addSystemMessage('❌ 角色切換失敗');
      }
    } catch (error) {
      console.error('[BattleScene] 角色切換失敗:', error);
      this.addSystemMessage('❌ 角色切換失敗，請稍後再試');
    }
  }

  /**
   * 初始化 Backend 會話（三方對話模式）
   */
  private async initializeBackendSession(): Promise<Array<{role: string, content: string}>> {
    try {
      this.addSystemMessage('🔄 正在連接 AI 系統...');
      
      // 檢查連接
      const isConnected = await this.backendClient.checkConnection();
      if (!isConnected) {
        this.addSystemMessage('⚠️ 無法連接到 AI 系統，將使用模擬模式');
        return [];
      }
      
      // 🔥 修復：使用實際的玩家角色，而不是硬編碼
      const result = await this.backendClient.startThreeWaySession({
        scamType: this.data.scamType,
        playerRole: this.data.playerRole.id,  // 使用實際的玩家角色
        victimPersona: 'average'
      });
      
      this.addSystemMessage('✅ AI 系統已就緒');
      console.log('[BattleScene] 三方對話會話已初始化，玩家角色:', this.data.playerRole.id);
      
      // 返回開場消息數組（從後端獲取）
      return result.openingMessages || [];
    } catch (error) {
      console.error('[BattleScene] 初始化 Backend 失敗:', error);
      this.addSystemMessage('❌ AI 系統初始化失敗，將使用模擬模式');
      return [];
    }
  }

  /**
   * 顯示開場消息（根據玩家角色決定）
   */
  private async showOpeningMessages(): Promise<void> {
    try {
      this.addSystemMessage('💬 正在生成開場對話...');
      
      // 從初始化會話中獲取開場消息數組
      const openingMessages = await this.initializeBackendSession();
      
      if (openingMessages && openingMessages.length > 0) {
        // 清除 "正在生成開場對話..." 的系統消息
        if (this.messages.length > 0 && this.messages[this.messages.length - 1].text === '💬 正在生成開場對話...') {
          this.messages.pop();
        }
        
        // 逐個顯示開場消息
        for (const msg of openingMessages) {
          if (msg.role === 'scammer') {
            this.addMessage('🎭 騙徒', msg.content, '#FF2E63');
          } else if (msg.role === 'expert') {
            this.addMessage('🛡️ 防詐專家', msg.content, '#08D9D6');
          } else if (msg.role === 'victim') {
            this.addMessage('👤 受害者', msg.content, '#FFD93D');
          }
          
          // 短暫延遲，讓對話更自然
          await this.delay(500);
        }
      } else {
        // 騙徒模式沒有開場消息，玩家先發起對話
        if (this.data.playerRole.id === 'scammer') {
          // 清除 "正在生成開場對話..." 的系統消息
          if (this.messages.length > 0 && this.messages[this.messages.length - 1].text === '💬 正在生成開場對話...') {
            this.messages.pop();
          }
          this.addSystemMessage('💡 你是騙徒，請開始你的詐騙對話...');
        } else {
          // 其他模式回退到默認開場白
          this.addMessage('🎭 騙徒', '你好，我有一個很好的機會想跟你分享...', '#FF2E63');
        }
      }
    } catch (error) {
      console.error('[BattleScene] 顯示開場消息失敗:', error);
      if (this.data.playerRole.id !== 'scammer') {
        this.addMessage('🎭 騙徒', '你好，我有一個很好的機會想跟你分享...', '#FF2E63');
      }
    }
  }

  private createModernBackground(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Base gradient
    const bg = this.add.rectangle(0, 0, width, height, 0x0A0E27).setOrigin(0, 0);

    // Animated gradient overlay
    const graphics = this.add.graphics();
    graphics.fillGradientStyle(0xFF2E63, 0xFF2E63, 0x08D9D6, 0x08D9D6, 0.03, 0.03, 0.08, 0.08);
    graphics.fillRect(0, 0, width, height);

    // Decorative circles
    const circle1 = this.add.circle(width * 0.15, height * 0.2, 150, 0xFF2E63, 0.08);
    const circle2 = this.add.circle(width * 0.85, height * 0.8, 200, 0x08D9D6, 0.08);

    this.tweens.add({
      targets: [circle1, circle2],
      scale: { from: 1, to: 1.2 },
      alpha: { from: 0.08, to: 0.04 },
      duration: 4000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
  }

  private createModernHeader(): void {
    const width = this.cameras.main.width;

    const header = this.add.container(0, 0);
    
    // Glass background
    const bg = this.add.rectangle(0, 0, width, 90, 0x16213E, 0.9).setOrigin(0, 0);
    bg.setStrokeStyle(2, 0x08D9D6, 0.3);
    
    // Back button with modern design - FIXED: Use centered origin
    const backButton = this.add.container(90, 45);
    const backBg = this.add.rectangle(0, 0, 140, 50, 0xFF2E63, 0.9);
    backBg.setOrigin(0.5);
    backBg.setStrokeStyle(2, 0xFF6B9D, 0.8);
    const backText = this.add.text(0, 0, '← 返回', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '20px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    backText.setOrigin(0.5);
    backButton.add([backBg, backText]);
    
    // FIXED: Make backBg interactive (simpler and more reliable)
    backBg.setInteractive({ useHandCursor: true });
    
    backBg.on('pointerdown', () => this.returnToWorld());
    backBg.on('pointerover', () => {
      this.tweens.add({
        targets: backButton,
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
      backBg.setFillStyle(0xFF2E63, 1);
    });
    backBg.on('pointerout', () => {
      this.tweens.add({
        targets: backButton,
        scale: 1,
        duration: 200
      });
      backBg.setFillStyle(0xFF2E63, 0.9);
    });

    // Title with glow - 顯示騙案類型而非人名
    const title = this.add.text(width / 2, 45, `${this.data.scamTypeInfo.icon} ${this.data.scamTypeInfo.nameZh}`, {
      fontFamily: 'Orbitron, sans-serif',
      fontSize: '28px',
      color: '#08D9D6',
      fontStyle: 'bold',
      stroke: '#08D9D6',
      strokeThickness: 1
    });
    title.setOrigin(0.5);

    // Role badge - FIXED: Adjusted position to stay in bounds
    const roleBadge = this.add.container(width - 110, 45);
    const roleBg = this.add.rectangle(0, 0, 180, 50, 0x16213E, 0.8);
    roleBg.setOrigin(1, 0.5);
    roleBg.setStrokeStyle(2, this.data.playerRole.colorHex, 0.8);
    
    const roleText = this.add.text(-15, 0, 
      `${this.data.playerRole.icon} ${this.data.playerRole.nameZh}`, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '18px',
      color: this.data.playerRole.color,
      fontStyle: 'bold'
    });
    roleText.setOrigin(1, 0.5);
    
    roleBadge.add([roleBg, roleText]);

    header.add([bg, backButton, title, roleBadge]);

    // Entrance animation
    header.setAlpha(0);
    header.setY(-20);
    this.tweens.add({
      targets: header,
      alpha: 1,
      y: 0,
      duration: 500,
      ease: 'Back.easeOut'
    });
  }

  /**
   * 創建信任度計量表
   */
  private createTrustMeters(): void {
    const width = this.cameras.main.width;
    
    this.trustMeters = this.add.container(width - 280, 110);
    this.trustMeters.setDepth(50);

    // 背景面板
    const panelBg = this.add.rectangle(0, 0, 260, 200, 0x16213E, 0.9);
    panelBg.setOrigin(0, 0);
    panelBg.setStrokeStyle(2, 0x08D9D6, 0.5);
    this.trustMeters.add(panelBg);

    // 標題
    const title = this.add.text(130, 15, '📊 信任度分析', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#08D9D6',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5, 0);
    this.trustMeters.add(title);

    // 騙徒信任度
    this.createTrustBar(20, 50, '🎭 騙徒', '#FF2E63', 'scammer');
    
    // 專家信任度
    this.createTrustBar(20, 100, '🛡️ 專家', '#08D9D6', 'expert');
    
    // 警覺性
    this.createTrustBar(20, 150, '⚠️ 警覺', '#FFD700', 'alertness');

    // 入場動畫
    this.trustMeters.setAlpha(0);
    this.trustMeters.setX(width - 260);
    this.tweens.add({
      targets: this.trustMeters,
      alpha: 1,
      x: width - 280,
      duration: 500,
      delay: 200,
      ease: 'Back.easeOut'
    });
  }

  /**
   * 創建單個信任度條
   */
  private createTrustBar(x: number, y: number, label: string, color: string, type: 'scammer' | 'expert' | 'alertness'): void {
    // 標籤
    const labelText = this.add.text(x, y, label, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '14px',
      color: '#FFFFFF'
    });
    this.trustMeters.add(labelText);

    // 背景條
    const bgBar = this.add.rectangle(x + 70, y + 7, 150, 16, 0x333333);
    bgBar.setOrigin(0, 0.5);
    this.trustMeters.add(bgBar);

    // 進度條
    const colorHex = parseInt(color.replace('#', '0x'));
    const bar = this.add.rectangle(x + 70, y + 7, 0, 16, colorHex);
    bar.setOrigin(0, 0.5);
    this.trustMeters.add(bar);

    // 數值文字
    const valueText = this.add.text(x + 230, y + 7, '50%', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '14px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    valueText.setOrigin(1, 0.5);
    this.trustMeters.add(valueText);

    // 保存引用
    if (type === 'scammer') {
      this.scammerTrustBar = bar;
      this.scammerTrustText = valueText;
    } else if (type === 'expert') {
      this.expertTrustBar = bar;
      this.expertTrustText = valueText;
    } else if (type === 'alertness') {
      this.alertnessBar = bar;
      this.alertnessText = valueText;
    }
  }

  /**
   * 更新信任度計量表
   */
  private updateTrustMeters(): void {
    const trustData = this.trustSystem.getAllTrustData();

    // 更新騙徒信任度
    this.tweens.add({
      targets: this.scammerTrustBar,
      width: (trustData.trustInScammer / 100) * 150,
      duration: 500,
      ease: 'Power2'
    });
    this.scammerTrustText.setText(`${Math.round(trustData.trustInScammer)}%`);

    // 更新專家信任度
    this.tweens.add({
      targets: this.expertTrustBar,
      width: (trustData.trustInExpert / 100) * 150,
      duration: 500,
      ease: 'Power2'
    });
    this.expertTrustText.setText(`${Math.round(trustData.trustInExpert)}%`);

    // 更新警覺性
    this.tweens.add({
      targets: this.alertnessBar,
      width: (trustData.alertness / 100) * 150,
      duration: 500,
      ease: 'Power2'
    });
    this.alertnessText.setText(`${Math.round(trustData.alertness)}%`);

    // 顯示風險等級
    const riskLevel = this.trustSystem.getRiskLevel();
    console.log(`[BattleScene] 風險等級: ${riskLevel}`, trustData);
  }

  private createModernMessageArea(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // 計算消息區域尺寸
    const messageAreaX = 40;
    const messageAreaY = 110;
    const messageAreaWidth = width - 380; // 留出右側信任度面板的空間 (280寬度 + 60邊距 + 40左邊距)
    this.messageAreaHeight = height - 280;

    // Message container background with glass effect
    const messageBg = this.add.rectangle(
      messageAreaX + messageAreaWidth / 2, 
      messageAreaY + this.messageAreaHeight / 2, 
      messageAreaWidth, 
      this.messageAreaHeight, 
      0x16213E,
      0.5
    );
    messageBg.setStrokeStyle(2, 0x08D9D6, 0.3);

    // 創建遮罩以裁剪消息區域
    this.messageAreaMask = this.make.graphics({});
    this.messageAreaMask.fillStyle(0xffffff);
    this.messageAreaMask.fillRect(messageAreaX, messageAreaY, messageAreaWidth - 30, this.messageAreaHeight);

    // Scrollable message container
    this.messageContainer = this.add.container(messageAreaX, messageAreaY);
    this.messageContainer.setMask(this.messageAreaMask.createGeometryMask());

    // 創建滾動條
    this.createScrollBar(messageAreaX + messageAreaWidth - 20, messageAreaY);

    // 添加滾輪事件
    this.input.on('wheel', (pointer: Phaser.Input.Pointer, gameObjects: any[], deltaX: number, deltaY: number) => {
      this.handleScroll(deltaY);
    });
  }

  /**
   * 創建滾動條
   */
  private createScrollBar(x: number, y: number): void {
    // 滾動條背景
    this.scrollBar = this.add.rectangle(x, y, 12, this.messageAreaHeight, 0x16213E, 0.6);
    this.scrollBar.setOrigin(0, 0);
    this.scrollBar.setStrokeStyle(1, 0x08D9D6, 0.3);
    this.scrollBar.setDepth(100);

    // 滾動條滑塊
    this.scrollThumb = this.add.rectangle(x + 1, y + 1, 10, 50, 0x08D9D6, 0.8);
    this.scrollThumb.setOrigin(0, 0);
    this.scrollThumb.setDepth(101);
    this.scrollThumb.setInteractive({ useHandCursor: true, draggable: true });

    // 滑塊拖動事件
    this.scrollThumb.on('drag', (pointer: Phaser.Input.Pointer, dragX: number, dragY: number) => {
      this.isDraggingScroll = true;
      const minY = y + 1;
      const maxY = y + this.messageAreaHeight - this.scrollThumb.height - 1;
      const newY = Phaser.Math.Clamp(dragY, minY, maxY);
      
      this.scrollThumb.y = newY;
      
      // 根據滑塊位置更新滾動偏移
      const scrollRatio = (newY - minY) / (maxY - minY);
      this.scrollOffset = scrollRatio * this.maxScrollOffset;
      this.updateMessagePositions();
    });

    this.scrollThumb.on('dragend', () => {
      this.isDraggingScroll = false;
    });

    // 滑塊懸停效果
    this.scrollThumb.on('pointerover', () => {
      this.scrollThumb.setFillStyle(0x08D9D6, 1);
    });

    this.scrollThumb.on('pointerout', () => {
      this.scrollThumb.setFillStyle(0x08D9D6, 0.8);
    });

    // 點擊滾動條背景跳轉
    this.scrollBar.setInteractive();
    this.scrollBar.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      const localY = pointer.y - y;
      const scrollRatio = localY / this.messageAreaHeight;
      this.scrollOffset = Phaser.Math.Clamp(scrollRatio * this.maxScrollOffset, 0, this.maxScrollOffset);
      this.updateScrollThumb();
      this.updateMessagePositions();
    });
  }

  /**
   * 處理滾輪滾動
   */
  private handleScroll(deltaY: number): void {
    const scrollSpeed = 30;
    this.scrollOffset += deltaY * scrollSpeed / 100;
    this.scrollOffset = Phaser.Math.Clamp(this.scrollOffset, 0, this.maxScrollOffset);
    
    this.updateScrollThumb();
    this.updateMessagePositions();
  }

  /**
   * 更新滾動條滑塊位置
   */
  private updateScrollThumb(): void {
    if (this.isDraggingScroll || this.maxScrollOffset === 0) return;

    const scrollBarY = this.scrollBar.y;
    const scrollRatio = this.scrollOffset / this.maxScrollOffset;
    const maxThumbY = this.messageAreaHeight - this.scrollThumb.height - 2;
    
    this.scrollThumb.y = scrollBarY + 1 + scrollRatio * maxThumbY;
  }

  /**
   * 更新消息位置（應用滾動偏移）
   */
  private updateMessagePositions(): void {
    this.messageContainer.y = 110 - this.scrollOffset;
  }

  private createModernInputArea(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    this.inputContainer = this.add.container(0, height - 100);

    // Glass background
    const inputBg = this.add.rectangle(
      width / 2,
      50,
      width - 60,
      90,
      0x16213E,
      0.9
    );
    inputBg.setStrokeStyle(2, 0xFF2E63, 0.5);

    this.inputContainer.add(inputBg);

    // FIXED: Create input field with proper positioning that updates on resize
    const inputFieldWidth = width - 220;
    const inputFieldLeft = 50;

    this.inputField = document.createElement('input');
    this.inputField.type = 'text';
    this.inputField.placeholder = '輸入你的回應...';
    
    // Function to update input position
    const updateInputPosition = () => {
      const canvas = this.game.canvas;
      const rect = canvas.getBoundingClientRect();
      const scale = this.cameras.main.zoom;
      
      // Calculate position relative to canvas
      const canvasInputY = height - 100 + 50; // container Y + offset
      const screenY = rect.top + (canvasInputY * rect.height / height);
      
      this.inputField.style.cssText = `
        position: fixed;
        left: ${rect.left + (inputFieldLeft * rect.width / width)}px;
        top: ${screenY - 25}px;
        width: ${inputFieldWidth * rect.width / width}px;
        height: 50px;
        font-family: 'Noto Sans TC', sans-serif;
        font-size: 16px;
        padding: 0 20px;
        background: rgba(22, 33, 62, 0.8);
        color: #FFFFFF;
        border: 2px solid rgba(8, 217, 214, 0.5);
        border-radius: 8px;
        outline: none;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
        z-index: 1000;
        box-sizing: border-box;
      `;
    };

    updateInputPosition();

    // Store the update function for cleanup
    const resizeHandler = () => updateInputPosition();
    window.addEventListener('resize', resizeHandler);
    
    // Store handler for cleanup
    (this.inputField as any)._resizeHandler = resizeHandler;

    // Focus effects
    this.inputField.addEventListener('focus', () => {
      this.inputField.style.borderColor = 'rgba(8, 217, 214, 1)';
      this.inputField.style.boxShadow = '0 0 20px rgba(8, 217, 214, 0.3)';
    });

    this.inputField.addEventListener('blur', () => {
      this.inputField.style.borderColor = 'rgba(8, 217, 214, 0.5)';
      this.inputField.style.boxShadow = 'none';
    });

    document.body.appendChild(this.inputField);

    // Modern send button - FIXED: Use centered origin
    const sendButton = this.add.container(width - 100, 50);
    const sendBg = this.add.rectangle(0, 0, 100, 50, 0x08D9D6, 0.9);
    sendBg.setOrigin(0.5);
    sendBg.setStrokeStyle(2, 0x0BC9BF, 0.8);
    const sendText = this.add.text(0, 0, '發送', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '20px',
      color: '#0A0E27',
      fontStyle: 'bold'
    });
    sendText.setOrigin(0.5);
    sendButton.add([sendBg, sendText]);

    // FIXED: Make sendBg interactive (simpler and more reliable)
    sendBg.setInteractive({ useHandCursor: true });
    sendBg.on('pointerdown', () => this.sendMessage());
    sendBg.on('pointerover', () => {
      this.tweens.add({
        targets: sendButton,
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
      sendBg.setFillStyle(0x08D9D6, 1);
    });
    sendBg.on('pointerout', () => {
      this.tweens.add({
        targets: sendButton,
        scale: 1,
        duration: 200
      });
      sendBg.setFillStyle(0x08D9D6, 0.9);
    });

    this.inputContainer.add(sendButton);

    // Enter key to send
    this.inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.sendMessage();
      }
    });

    this.inputField.focus();

    // Entrance animation
    this.inputContainer.setAlpha(0);
    this.inputContainer.setY(height - 80);
    this.tweens.add({
      targets: this.inputContainer,
      alpha: 1,
      y: height - 100,
      duration: 500,
      delay: 300,
      ease: 'Back.easeOut'
    });
  }

  private async sendMessage(): Promise<void> {
    const message = this.inputField.value.trim();
    
    if (message && !this.isWaitingForAI) {
      this.isWaitingForAI = true;
      this.roundCount++;
      
      // 顯示玩家消息
      this.addMessage(
        `👤 ${this.data.playerRole.nameZh}`,
        message,
        this.data.playerRole.color
      );
      
      this.inputField.value = '';
      this.inputField.disabled = true;
      
      try {
        // 使用三方對話 API - 一次獲取騙徒和專家的回應
        this.addSystemMessage('🤖 AI 正在思考...');
        
        const response = await this.backendClient.sendThreeWayMessage(message);
        
        console.log('[BattleScene] 收到後端回應:', response);
        console.log('[BattleScene] AI回應數量:', response.replies?.length);
        
        if (response.success && response.replies) {
          // 清除 "AI 正在思考..." 的系統消息
          if (this.messages.length > 0 && this.messages[this.messages.length - 1].text === '🤖 AI 正在思考...') {
            this.messages.pop();
          }
          
          // 檢查回應格式
          response.replies.forEach((reply, index) => {
            console.log(`[BattleScene] 回應 ${index + 1}:`, {
              speaker: reply.speaker,
              messageLength: reply.message?.length,
              messagePreview: reply.message?.substring(0, 50)
            });
          });
          
          // 按順序顯示回應，確保每個回應都是獨立的氣泡
          for (let i = 0; i < response.replies.length; i++) {
            const reply = response.replies[i];
            
            // 短暫延遲，讓對話更自然
            if (i > 0) {
              await this.delay(800);
            }
            
            // 根據 speaker 類型添加對應的消息
            if (reply.speaker === 'scammer') {
              console.log('[BattleScene] 添加騙徒消息:', reply.message);
              this.addMessage('🎭 騙徒', reply.message, '#FF2E63');
            } else if (reply.speaker === 'expert') {
              console.log('[BattleScene] 添加專家消息:', reply.message);
              this.addMessage('🛡️ 防詐專家', reply.message, '#08D9D6');
            } else if (reply.speaker === 'victim') {
              console.log('[BattleScene] 添加受害者消息:', reply.message);
              this.addMessage('👤 受害者', reply.message, '#FFD93D');
            }
            
            // 強制重新渲染，確保每個消息都是獨立的氣泡
            this.renderMessages();
          }
          
          // 更新信任度
          if (response.trust_data) {
            this.trustSystem.updateTrustDirect(
              response.trust_data.trust_in_scammer,
              response.trust_data.trust_in_expert,
              response.trust_data.alertness
            );
            this.updateTrustMeters();
          }
          
          // 🔥 檢查後端返回的遊戲結束狀態
          if (response.game_status && response.game_status.game_over) {
            console.log('[BattleScene] 遊戲結束:', response.game_status);
            
            // 顯示遊戲結束消息
            if (response.game_status.winner === 'player') {
              this.addSystemMessage(`🎉 ${response.game_status.reason || '你贏了！'}`);
            } else if (response.game_status.winner === 'ai') {
              this.addSystemMessage(`💀 ${response.game_status.reason || '你輸了！'}`);
            } else {
              this.addSystemMessage(`⏸️ ${response.game_status.reason || '遊戲結束'}`);
            }
            
            // 禁用輸入並跳轉到結果場景
            this.isWaitingForAI = false;
            this.inputField.disabled = true;
            
            await this.delay(2000);
            await this.endBattle(response.game_status.winner === 'player' ? 'expert_win' : 'scammer_win');
            return;
          }
        } else {
          // 回退到舊的 API（向後兼容）
          this.addSystemMessage('🎭 騙徒正在回應...');
          const scammerResponse = await this.backendClient.sendMessage(message, 'scammer');
          
          if (scammerResponse.success) {
            this.addMessage('🎭 騙徒', scammerResponse.reply, '#FF2E63');
            
            if (scammerResponse.trust_in_scammer !== undefined || scammerResponse.trust_in_expert !== undefined) {
              this.trustSystem.updateTrust(scammerResponse);
              this.updateTrustMeters();
            }
          }
          
          await this.delay(1000);
          
          this.addSystemMessage('🛡️ 防詐專家正在分析...');
          const expertResponse = await this.backendClient.sendMessage(message, 'expert');
          
          if (expertResponse.success) {
            this.addMessage('🛡️ 防詐專家', expertResponse.reply, '#08D9D6');
            
            if (expertResponse.trust_in_scammer !== undefined || expertResponse.trust_in_expert !== undefined) {
              this.trustSystem.updateTrust(expertResponse);
              this.updateTrustMeters();
            }
          }
        }
        
        // 檢查遊戲結果
        const outcome = this.trustSystem.checkOutcome();
        if (outcome !== 'ongoing') {
          await this.endBattle(outcome);
          return;
        }
        
        // 檢查回合數限制
        if (this.roundCount >= 15) {
          this.addSystemMessage('⏰ 對話已達到最大回合數');
          await this.endBattle('ongoing');
          return;
        }
        
      } catch (error) {
        console.error('[BattleScene] 發送消息失敗:', error);
        this.addSystemMessage('❌ 發送失敗，請重試');
      } finally {
        this.isWaitingForAI = false;
        this.inputField.disabled = false;
        this.inputField.focus();
      }
    }
  }

  /**
   * 延遲函數
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 結束對話並顯示結果
   */
  private async endBattle(outcome: string): Promise<void> {
    this.inputField.disabled = true;
    
    // 顯示結果消息
    if (outcome === 'scammer_win') {
      this.addSystemMessage('💀 你被騙了！騙徒成功獲取了你的信任。');
    } else if (outcome === 'expert_win') {
      this.addSystemMessage('✅ 成功識破騙局！你保護了自己。');
    } else {
      this.addSystemMessage('⏸️ 對話結束。讓我們看看分析結果...');
    }
    
    await this.delay(2000);
    
    try {
      // 獲取最終分析（優先使用三方對話 API）
      this.addSystemMessage('📊 正在生成分析報告...');
      
      let analysis;
      try {
        // 嘗試使用三方對話分析 API
        const threeWayAnalysis = await this.backendClient.getThreeWayAnalysis();
        analysis = threeWayAnalysis.analysis;
        outcome = threeWayAnalysis.outcome || outcome;
      } catch (error) {
        console.log('[BattleScene] 三方對話分析不可用，使用舊版 API');
        // 回退到舊版 API
        const oldAnalysis = await this.backendClient.getAnalysis();
        analysis = oldAnalysis.analysis;
      }
      
      // 跳轉到結果場景
      this.scene.start('ResultScene', {
        outcome: outcome,
        analysis: analysis,
        scamType: this.data.scamTypeInfo,
        trustData: this.trustSystem.getAllTrustData(),
        roundCount: this.roundCount
      });
    } catch (error) {
      console.error('[BattleScene] 獲取分析失敗:', error);
      this.addSystemMessage('❌ 無法生成分析報告');
      
      await this.delay(2000);
      this.returnToWorld();
    }
  }

  private addMessage(speaker: string, text: string, color: string): void {
    // 確保每個消息都是獨立的對象，防止引用問題
    this.messages.push({ 
      speaker: speaker, 
      text: text, 
      color: color 
    });
    
    // 立即渲染以確保消息分離
    this.renderMessages();
  }

  private addSystemMessage(text: string): void {
    this.addMessage('💡 系統', text, '#FFD93D');
  }

  private renderMessages(): void {
    this.messageContainer.removeAll(true);

    const startY = 0;
    let currentY = 0;  // 動態計算 Y 位置
    
    // 顯示所有消息（不再限制數量）
    const allMessages = this.messages;
    
    // 計算每個消息的實際高度
    const messageHeights: number[] = [];
    // 限制每行約50個中文字（14px字體，每個中文字約14px寬，50字 = 700px）
    const maxWidth = Math.min(500, this.cameras.main.width - 430);
    
    allMessages.forEach((msg) => {
      // 創建臨時文字對象來測量高度
      const tempText = this.add.text(0, 0, msg.text, {
        fontFamily: 'Noto Sans TC, sans-serif',
        fontSize: '14px',
        color: '#FFFFFF',
        wordWrap: { width: maxWidth, useAdvancedWrap: true },
        lineSpacing: 2
      });
      
      const textHeight = tempText.height;
      tempText.destroy();
      
      // 消息高度 = 頂部間距(12) + 標題(20) + 間距(8) + 文字高度 + 底部間距(12)
      const bubbleHeight = Math.max(70, 12 + 20 + 8 + textHeight + 12);
      messageHeights.push(bubbleHeight);
    });
    
    // 計算總內容高度
    const totalContentHeight = messageHeights.reduce((sum, h) => sum + h + 6, 0);
    this.maxScrollOffset = Math.max(0, totalContentHeight - this.messageAreaHeight + 50);
    
    // 更新滾動條滑塊大小
    if (this.scrollThumb) {
      const thumbHeight = Math.max(30, (this.messageAreaHeight / totalContentHeight) * this.messageAreaHeight);
      this.scrollThumb.height = thumbHeight;
      
      // 如果內容不需要滾動，隱藏滾動條
      if (this.maxScrollOffset <= 0) {
        this.scrollBar.setAlpha(0);
        this.scrollThumb.setAlpha(0);
        this.scrollOffset = 0;
      } else {
        this.scrollBar.setAlpha(0.6);
        this.scrollThumb.setAlpha(0.8);
      }
    }

    allMessages.forEach((msg, index) => {
      const y = currentY;
      const bubbleHeight = messageHeights[index];
      const isPlayer = msg.speaker.includes(this.data.playerRole.nameZh);
      const isSystem = msg.speaker.includes('系統');
      
      // Message bubble container - 每個消息都是獨立的容器
      const messageBubble = this.add.container(0, y);
      
      // 根據說話者選擇背景顏色（確保騙徒和專家有不同的顏色）
      let bgColor = 0x16213E;
      let bgAlpha = 0.6;
      
      if (msg.speaker.includes('騙徒')) {
        bgColor = 0x2A1A1F;  // 深紅色背景
        bgAlpha = 0.7;
      } else if (msg.speaker.includes('專家')) {
        bgColor = 0x0A1F1F;  // 深青色背景
        bgAlpha = 0.7;
      } else if (isPlayer) {
        bgColor = 0x08D9D6;
        bgAlpha = 0.15;
      } else if (isSystem) {
        bgColor = 0x2A2F4F;
        bgAlpha = 0.5;
      }
      
      // Bubble background - 使用動態高度，確保不會被右側面板遮擋
      const bubbleBg = this.add.rectangle(
        0, 0, 
        this.cameras.main.width - 400, // 增加右側邊距
        bubbleHeight, 
        bgColor, 
        bgAlpha
      );
      bubbleBg.setOrigin(0, 0);
      bubbleBg.setStrokeStyle(2, parseInt(msg.color.replace('#', '0x')), 0.5);
      
      // Speaker name - 確保顯示完整的說話者名稱
      const speakerText = this.add.text(12, 12, msg.speaker, {
        fontFamily: 'Rajdhani, sans-serif',
        fontSize: '16px',
        color: msg.color,
        fontStyle: 'bold'
      });

      // Message text - 確保正確換行
      const messageText = this.add.text(12, 40, msg.text, {
        fontFamily: 'Noto Sans TC, sans-serif',
        fontSize: '14px',
        color: '#FFFFFF',
        wordWrap: { width: maxWidth, useAdvancedWrap: true },
        lineSpacing: 2  // 正值行距讓文字更易讀
      });

      messageBubble.add([bubbleBg, speakerText, messageText]);
      this.messageContainer.add(messageBubble);

      // Entrance animation (only for new messages)
      if (index === allMessages.length - 1) {
        messageBubble.setAlpha(0);
        messageBubble.setX(-20);
        this.tweens.add({
          targets: messageBubble,
          alpha: 1,
          x: 0,
          duration: 300,
          ease: 'Back.easeOut'
        });
        
        // 自動滾動到底部（顯示最新消息）
        this.time.delayedCall(100, () => {
          this.scrollOffset = this.maxScrollOffset;
          this.updateScrollThumb();
          this.updateMessagePositions();
        });
      }
      
      // 更新下一個消息的 Y 位置 - 增加間距以確保氣泡分離
      currentY += bubbleHeight + 8;  // 增加到 8px 間距，確保氣泡明顯分離
    });
  }

  private async returnToWorld(): Promise<void> {
    // 結束 Backend 會話
    try {
      await this.backendClient.endSession();
    } catch (error) {
      console.error('[BattleScene] 結束會話失敗:', error);
    }
    
    // Clean up HTML input
    if (this.inputField && this.inputField.parentNode) {
      this.inputField.parentNode.removeChild(this.inputField);
    }
    
    // Fade transition
    const overlay = this.add.rectangle(
      this.cameras.main.width / 2,
      this.cameras.main.height / 2,
      this.cameras.main.width,
      this.cameras.main.height,
      0x0A0E27,
      0
    );
    overlay.setDepth(200);
    
    this.tweens.add({
      targets: overlay,
      alpha: 1,
      duration: 400,
      onComplete: () => {
        this.scene.start('WorldMapScene');
      }
    });
  }

  shutdown(): void {
    // Clean up resize handler
    if (this.inputField && (this.inputField as any)._resizeHandler) {
      window.removeEventListener('resize', (this.inputField as any)._resizeHandler);
    }
    
    // Clean up input field
    if (this.inputField && this.inputField.parentNode) {
      this.inputField.parentNode.removeChild(this.inputField);
    }
    
    // Clean up scroll events
    this.input.off('wheel');
  }
}
