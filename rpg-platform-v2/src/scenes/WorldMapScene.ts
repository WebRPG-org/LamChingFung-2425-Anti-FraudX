import Phaser from 'phaser';
import { Player } from '../entities/Player';
import { NPC } from '../entities/NPC';
import { RoleManager } from '../systems/RoleManager';
import { localization, AppLanguage } from '../systems/LocalizationManager';
import { getAllScamTypes } from '../types/ScamTypes';

export class WorldMapScene extends Phaser.Scene {
  private player!: Player;
  private npcs: NPC[] = [];
  private roleManager: RoleManager;
  private interactionRadius = 80;
  private hud!: Phaser.GameObjects.Container;
  private roleText!: Phaser.GameObjects.Text;
  private instructionsContainer: Phaser.GameObjects.Container | null = null;
  private homeButton!: Phaser.GameObjects.Container;
  private obstacles: Phaser.Physics.Arcade.StaticGroup | null = null;
  private roleChangeCallback: (() => void) | null = null;
  private languageButton?: Phaser.GameObjects.Container;
  private languagePanel?: Phaser.GameObjects.Container;

  constructor() {
    super({ key: 'WorldMapScene' });
    this.roleManager = RoleManager.getInstance();
  }

  create(): void {
    console.log('[WorldMapScene] Creating scene...');
    
    // Use simple background image instead of tilemap
    const worldMapBg = this.add.image(0, 0, 'world-map-bg').setOrigin(0, 0);
    worldMapBg.setDepth(0);
    
    // Get map dimensions from background image
    const mapPixelWidth = worldMapBg.width;
    const mapPixelHeight = worldMapBg.height;

    console.log(`[WorldMapScene] Map size: ${mapPixelWidth}x${mapPixelHeight} pixels`);

    // Create obstacles (invisible collision boxes)
    this.createObstacles(mapPixelWidth, mapPixelHeight);

    // Create player at center of map
    this.player = new Player(this, mapPixelWidth / 2, mapPixelHeight / 2);
    
    // Setup collision between player and obstacles
    if (this.obstacles) {
      this.physics.add.collider(this.player.sprite, this.obstacles);
    }

    // Create NPCs at different positions
    this.createNPCs(mapPixelWidth, mapPixelHeight);
    
    // Setup collision between NPCs and obstacles
    if (this.obstacles) {
      this.npcs.forEach(npc => {
        this.physics.add.collider(npc.sprite, this.obstacles!);
      });
    }

    // Setup camera to follow player
    this.cameras.main.startFollow(this.player.sprite, true, 0.1, 0.1);
    this.cameras.main.setBounds(0, 0, mapPixelWidth, mapPixelHeight);
    this.physics.world.setBounds(0, 0, mapPixelWidth, mapPixelHeight);
    
    // Set camera zoom for better view (RPG Maker standard view)
    this.cameras.main.setZoom(1.0);

    // Create HUD
    this.createHUD();
    this.createLanguageSwitcher();
    
    // Create home button in top right
    this.createHomeButton();

    // Setup input
    this.setupInput();

    // Add instructions (hidden by default, toggle with H)
    this.showInstructions();
    
    // Add ambient effects
    this.addAmbientEffects(mapPixelWidth, mapPixelHeight);
  }

  /**
   * 創建障礙物 - 根據香港街景地圖設置不可通行區域
   * 包含建築物、樹木、車輛等障礙物
   */
  private createObstacles(mapWidth: number, mapHeight: number): void {
    // 創建靜態物理組用於障礙物
    this.obstacles = this.physics.add.staticGroup();
    
    const centerX = mapWidth / 2;
    const centerY = mapHeight / 2;
    
    // 根據 outside_map.jpg 的實際內容設置障礙物
    const obstacleData = [
      // ========== 四邊邊界（不要動）==========
      // 上方邊界牆
      { x: centerX, y: 15, width: mapWidth - 50, height: 50, color: 0x888888, name: '上邊界' },
      
      // 下方邊界牆
      { x: centerX, y: mapHeight - 15, width: mapWidth - 50, height: 50, color: 0x888888, name: '下邊界' },
      
      // 左方邊界牆
      { x: 15, y: centerY, width: 50, height: mapHeight - 50, color: 0x888888, name: '左邊界' },
      
      // 右方邊界牆
      { x: mapWidth - 15, y: centerY, width: 50, height: mapHeight - 50, color: 0x888888, name: '右邊界' },
      
      // ========== 左側建築群 ==========
      // 左上角大樓
      { x: 200 , y: 100, width: 300, height: 140, color: 0xff6b6b, name: '左上大樓' },
      { x: 100 , y: 190, width: 150, height: 50, color: 0xff6b6b, name: '水' },   
      { x: 100 , y: 240, width: 60, height: 50, color: 0xff6b6b, name: '水' },
      { x: 80 , y: 290, width: 100, height: 1200, color: 0xff6b6b, name: '左中大樓' },
      { x: 370 , y: 300, width: 220, height: 175, color: 0xff6b6b, name: '左上中大樓' },
      { x: 420 , y: 60, width: 300, height: 50, color: 0xff6b6b, name: '左上杆欄' },
      { x: 420 , y: 150, width: 300, height: 40, color: 0xff6b6b, name: '左上杆欄' },
      { x: 150 , y: 570, width: 220, height: 170, color: 0xff6b6b, name: '左中下大樓' },
      { x: 220 , y: 350, width: 80, height: 175, color: 0xff6b6b, name: '左上中大樓' },
      { x: 150 , y: 680, width: 50, height: 375, color: 0xff6b6b, name: '左下大樓' },
      { x: 200 , y: 840, width: 45, height: 100, color: 0xff6b6b, name: '吊車' },
      { x: 285 , y: 680, width: 95, height: 35, color: 0xff6b6b, name: '左下杆欄' },
      { x: 445 , y: 680, width: 70, height: 35, color: 0xff6b6b, name: '左下杆欄' },
      { x: 460 , y: 780, width: 40, height: 175, color: 0xff6b6b, name: '左下杆欄' },
      { x: 310 , y: 810, width: 80, height: 155, color: 0xff6b6b, name: '車' },
      { x: 420 , y: 825, width: 40, height: 80, color: 0xff6b6b, name: '紅筒' },
      { x: 375 , y: 440, width: 40, height: 80, color: 0xff6b6b, name: '燈' },
      { x: 550 , y: 875, width: 40, height: 80, color: 0xff6b6b, name: '燈' },
      { x: 550 , y: 745, width: 40, height: 80, color: 0xff6b6b, name: '燈' },
      { x: 550 , y: 615, width: 40, height: 80, color: 0xff6b6b, name: '燈' },
      { x: 550 , y: 350, width: 40, height: 180, color: 0xff6b6b, name: '燈' },
      { x: 550 , y: 190, width: 40, height: 40, color: 0xff6b6b, name: '箱' },

      // ========== 右側建築群 ==========
      { x: 725 , y: 170, width: 40, height: 80, color: 0x4ecdc4, name: '箱' },
      { x: 725 , y: 350, width: 40, height: 180, color: 0x4ecdc4, name: '箱' },
      { x: 725 , y: 615, width: 40, height: 80, color: 0x4ecdc4, name: '燈' },
      { x: 770 , y: 720, width: 130, height: 220, color: 0x4ecdc4, name: '右下大樓' },
      { x: 860 , y: 785, width: 40, height: 90, color: 0x4ecdc4, name: '右下大樓' },
      { x: 920 , y: 807, width: 90, height: 45, color: 0x4ecdc4, name: '右下大樓' },
      { x: 900 , y: 440, width: 40, height: 80, color: 0x4ecdc4, name: '燈' },
      { x: 1150 , y: 700, width: 180, height: 180, color: 0x4ecdc4, name: '右大樓' },
      { x: 1125 , y: 480, width: 130, height: 270, color: 0x4ecdc4, name: '右大樓' },
      { x: 925 , y: 370, width: 260, height: 40, color: 0x4ecdc4, name: '右上杆欄' },
      { x: 880 , y: 225, width: 90, height: 70, color: 0x4ecdc4, name: '箱' },
      { x: 870 , y: 140, width: 110, height: 30, color: 0x4ecdc4, name: '右上杆欄' },
      { x: 1080 , y: 190, width: 310, height: 50, color: 0x4ecdc4, name: '箱' },
      { x: 1080 , y: 235, width: 40, height: 40, color: 0x4ecdc4, name: '吊車' },
      { x: 1210 , y: 235, width: 40, height: 40, color: 0x4ecdc4, name: '洞' },
      { x: 1080 , y: 100, width: 310, height: 150, color: 0x4ecdc4, name: '右上大樓' },
      { x: 900 , y: 60, width: 40, height: 40, color: 0x4ecdc4, name: '右上大樓' },
      { x: 730 , y: 60, width: 40, height: 40, color: 0x4ecdc4, name: '右上大樓' },
      
     
      
    
    ];
    
    console.log(`[WorldMapScene] 創建 ${obstacleData.length} 個障礙物（包含4個邊界）`);
    
    obstacleData.forEach((obstacle, index) => {
      // 創建矩形作為障礙物
      const rect = this.add.rectangle(
        obstacle.x, 
        obstacle.y, 
        obstacle.width, 
        obstacle.height, 
        obstacle.color, 
        0 // 完全隱藏填充
      );
      rect.setStrokeStyle(2, obstacle.color, 0); // 邊線透明度改為 0（完全透明）
      rect.setDepth(5);
      
      // 添加到物理組
      this.obstacles!.add(rect);
      
      console.log(`[WorldMapScene] 障礙物 ${index + 1} [${obstacle.name}]: (${Math.round(obstacle.x)}, ${Math.round(obstacle.y)}) ${obstacle.width}x${obstacle.height}`);
    });
    
    // 刷新物理邊界
    this.obstacles.refresh();
    
    console.log('[WorldMapScene] 障礙物系統初始化完成！');
    console.log('[WorldMapScene] 提示：將障礙物透明度改為 0 可完全隱藏');
  }

  private addAmbientEffects(mapPixelWidth: number, mapPixelHeight: number): void {
    // Add subtle particles for atmosphere
    
    const particles = this.add.particles(0, 0, 'player', {
      frame: 0,
      lifespan: 4000,
      speed: { min: 10, max: 30 },
      scale: { start: 0.1, end: 0 },
      alpha: { start: 0.3, end: 0 },
      blendMode: 'ADD',
      frequency: 500,
      emitZone: {
        type: 'random',
        source: new Phaser.Geom.Rectangle(0, 0, mapPixelWidth, mapPixelHeight)
      } as any
    });
    particles.setDepth(0);
  }

  /**
   * 創建 NPC - 每個 NPC 代表一種騙案類型
   * NPC 位置已調整，避免生成在障礙物內部
   */
  private createNPCs(mapWidth: number, mapHeight: number): void {
    const centerX = mapWidth / 2;
    const centerY = mapHeight / 2;

    // 定義 NPC 位置和對應的騙案類型（確保在可通行區域）
    const npcData: Array<{ x: number; y: number; scamId: string }> = [
      // 中央道路區域 - 安全位置
      { x: centerX, y: centerY, scamId: 'investment' },                 // 💰 投資詐騙（中央）
      { x: centerX, y: centerY + 150, scamId: 'phishing' },             // 📱 釣魚短訊
      { x: centerX, y: centerY - 150, scamId: 'romance' },              // 💕 愛情詐騙
      
      // 左側道路區域
      { x: 250, y: 450, scamId: 'impersonation' },                      // 👮 假冒官員
      { x: 400, y: 550, scamId: 'banking' },                            // 🏦 假冒銀行
      { x: 250, y: 750, scamId: 'whatsapp' },                           // 💬 WhatsApp 詐騙
      
      // 右側道路區域
      { x: mapWidth - 250, y: 450, scamId: 'crypto' },                  // ₿ 加密貨幣
      { x: mapWidth - 400, y: 550, scamId: 'shopping' },                // 🛒 購物詐騙
      { x: mapWidth - 450, y: 850, scamId: 'job' },                     // 💼 求職詐騙（調整位置避開右下大樓）
      
      // 上方道路區域
      { x: centerX - 130, y: 250, scamId: 'prize' },                    // 🎁 中獎詐騙
      { x: centerX + 150, y: 250, scamId: 'rental' },                   // 🏠 租屋詐騙
      
      // 下方道路區域
      { x: centerX - 130, y: mapHeight - 150, scamId: 'tech_support' }, // 💻 技術支援
      { x: centerX + 350, y: mapHeight - 250, scamId: 'charity' }       // ❤️ 慈善詐騙（調整位置避開障礙物）
    ];

    console.log(`[WorldMapScene] 創建 ${npcData.length} 個騙案類型 NPC（已避開障礙物）`);

    npcData.forEach(data => {
      const npc = new NPC(this, data.x, data.y, data.scamId);
      this.npcs.push(npc);
      console.log(`[WorldMapScene] 創建 NPC: ${npc.getDisplayName()} at (${data.x}, ${data.y})`);
    });
  }

  private setupInput(): void {
    // Interaction key (E)
    this.input.keyboard?.on('keydown-E', () => {
      this.checkInteraction();
    });

    // Toggle instructions with H key
    this.input.keyboard?.on('keydown-H', () => {
      this.toggleInstructions();
    });

    // Role switching (F1, F2, F3)
    this.input.keyboard?.on('keydown-F1', () => {
      this.roleManager.switchRole('victim');
    });

    this.input.keyboard?.on('keydown-F2', () => {
      this.roleManager.switchRole('scammer');
    });

    this.input.keyboard?.on('keydown-F3', () => {
      this.roleManager.switchRole('expert');
    });

    // NPC 互動指示器點擊事件
    this.events.on('npc-interact-click', (npc: import('../entities/NPC').NPC) => {
      this.startBattle(npc);
    });
  }

  private createHUD(): void {
    this.hud = this.add.container(0, 0);
    this.hud.setScrollFactor(0);
    this.hud.setDepth(100);

    // Modern role display with glass morphism
    const roleContainer = this.add.container(20, 20);
    
    // Glass background
    const roleBox = this.add.rectangle(0, 0, 300, 70, 0x16213E, 0.85);
    roleBox.setOrigin(0, 0);
    roleBox.setStrokeStyle(2, 0x08D9D6, 0.5);
    
    // Role icon background
    const iconBg = this.add.circle(45, 35, 25, 0x08D9D6, 0.2);
    iconBg.setStrokeStyle(2, 0x08D9D6, 0.6);
    
    // Role text
    this.roleText = this.add.text(85, 35, '', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '22px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    this.roleText.setOrigin(0, 0.5);
    
    // Role label
    const roleLabel = this.add.text(85, 15, localization.t('currentRole'), {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '11px',
      color: '#B8C5D6'
    });
    roleLabel.setOrigin(0, 0.5);
    roleLabel.setAlpha(0.8);

    roleContainer.add([roleBox, iconBg, this.roleText, roleLabel]);
    this.hud.add(roleContainer);

    // 保存回調函數的引用，以便稍後移除
    this.roleChangeCallback = () => this.updateRoleDisplay();
    this.roleManager.onRoleChange(this.roleChangeCallback);
    
    // 延遲更新角色顯示，確保場景完全激活
    this.time.delayedCall(100, () => {
      console.log('[WorldMapScene] Delayed role display update...');
      this.updateRoleDisplay();
    });

    // Modern instructions panel
    const instructionsContainer = this.add.container(20, 100);
    
    const instructionsBox = this.add.rectangle(0, 0, 300, 90, 0x16213E, 0.85);
    instructionsBox.setOrigin(0, 0);
    instructionsBox.setStrokeStyle(2, 0xFF2E63, 0.5);
    instructionsBox.setInteractive({ useHandCursor: true });
    instructionsBox.on('pointerover', () => { instructionsBox.setStrokeStyle(2, 0xFF2E63, 1); instructionsBox.setFillStyle(0xFF2E63, 0.15); });
    instructionsBox.on('pointerout',  () => { instructionsBox.setStrokeStyle(2, 0xFF2E63, 0.5); instructionsBox.setFillStyle(0x16213E, 0.85); });
    instructionsBox.on('pointerdown', () => this.toggleInstructions());
    
    const instructionsTitle = this.add.text(15, 12, localization.t('controls'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '14px',
      color: '#FFD93D',
      fontStyle: 'bold'
    });
    
    const instructionsText = this.add.text(15, 35, localization.t('controlsBody'), {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '11px',
      color: '#B8C5D6',
      lineSpacing: 4
    });
    instructionsText.setAlpha(0.8);
    
    instructionsContainer.add([instructionsBox, instructionsTitle, instructionsText]);
    this.hud.add(instructionsContainer);

    // 讓控制說明面板可以點擊（直接加透明覆蓋層到 scene，繞開 Container 的 pointer 問題）
    const hClickZone = this.add.rectangle(20, 100, 300, 90, 0x000000, 0);
    hClickZone.setOrigin(0, 0);
    hClickZone.setScrollFactor(0);
    hClickZone.setDepth(110);
    hClickZone.setInteractive({ useHandCursor: true });
    hClickZone.on('pointerdown', () => this.toggleInstructions());
    hClickZone.on('pointerover', () => { instructionsBox.setStrokeStyle(2, 0xFF2E63, 1); instructionsBox.setFillStyle(0xFF2E63, 0.15); });
    hClickZone.on('pointerout',  () => { instructionsBox.setStrokeStyle(2, 0xFF2E63, 0.5); instructionsBox.setFillStyle(0x16213E, 0.85); });

    // Entrance animation
    roleContainer.setAlpha(0);
    roleContainer.setX(0);
    this.tweens.add({
      targets: roleContainer,
      alpha: 1,
      x: 20,
      duration: 600,
      ease: 'Back.easeOut'
    });

    instructionsContainer.setAlpha(0);
    instructionsContainer.setX(0);
    this.tweens.add({
      targets: instructionsContainer,
      alpha: 1,
      x: 20,
      duration: 600,
      delay: 200,
      ease: 'Back.easeOut'
    });

    // E/H 鍵互動已透過 NPC indicator 點擊和鍵盤快捷鍵支援
  }

  private createHomeButton(): void {
    const width = this.cameras.main.width;
    const buttonX = width - 90;
    const buttonY = 50;
    
    // Glass morphism background - this will be the interactive element
    const bg = this.add.rectangle(buttonX, buttonY, 140, 60, 0x16213E, 0.85);
    bg.setOrigin(0.5, 0.5);
    bg.setStrokeStyle(2, 0xFF2E63, 0.6);
    bg.setScrollFactor(0);
    bg.setDepth(100);
    
    // Icon
    const icon = this.add.text(buttonX - 35, buttonY, '🏠', {
      fontSize: '24px'
    });
    icon.setOrigin(0.5, 0.5);
    icon.setScrollFactor(0);
    icon.setDepth(101);
    
    // Text
    const text = this.add.text(buttonX + 15, buttonY, localization.t('backHome'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    text.setOrigin(0.4 , 0.5);
    text.setScrollFactor(0);
    text.setDepth(101);
    
    // Store references for animation
    this.homeButton = this.add.container(0, 0);
    this.homeButton.add([bg, icon, text]);
    
    // Make background interactive
    bg.setInteractive({ useHandCursor: true });
    
    bg.on('pointerover', () => {
      this.tweens.add({
        targets: [bg, icon, text],
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
      bg.setStrokeStyle(3, 0xFF2E63, 1);
      bg.setFillStyle(0xFF2E63, 0.3);
    });
    
    bg.on('pointerout', () => {
      this.tweens.add({
        targets: [bg, icon, text],
        scale: 1,
        duration: 200
      });
      bg.setStrokeStyle(2, 0xFF2E63, 0.6);
      bg.setFillStyle(0x16213E, 0.85);
    });
    
    bg.on('pointerdown', () => {
      this.tweens.add({
        targets: [bg, icon, text],
        scale: 0.95,
        duration: 100,
        yoyo: true,
        onComplete: () => {
          // 清理場景資源
          console.log('[WorldMapScene] 返回主頁，清理資源...');
          
          // Fade transition
          const overlay = this.add.rectangle(
            this.cameras.main.centerX,
            this.cameras.main.centerY,
            this.cameras.main.width * 2,
            this.cameras.main.height * 2,
            0x0A0E27,
            0
          );
          overlay.setScrollFactor(0);
          overlay.setDepth(200);
          
          this.tweens.add({
            targets: overlay,
            alpha: 1,
            duration: 400,
            onComplete: () => {
              // 停止當前場景並啟動主選單
              this.scene.stop('WorldMapScene');
              this.scene.start('MainMenuScene');
            }
          });
        }
      });
    });

    // Entrance animation
    bg.setAlpha(0);
    icon.setAlpha(0);
    text.setAlpha(0);
    bg.setX(buttonX + 20);
    icon.setX(buttonX - 15);
    text.setX(buttonX + 35);
    
    this.tweens.add({
      targets: [bg, icon, text],
      alpha: 1,
      duration: 600,
      delay: 400,
      ease: 'Back.easeOut'
    });
    
    this.tweens.add({
      targets: bg,
      x: buttonX,
      duration: 600,
      delay: 400,
      ease: 'Back.easeOut'
    });
    
    this.tweens.add({
      targets: icon,
      x: buttonX - 35,
      duration: 600,
      delay: 400,
      ease: 'Back.easeOut'
    });
    
    this.tweens.add({
      targets: text,
      x: buttonX + 15,
      duration: 600,
      delay: 400,
      ease: 'Back.easeOut'
    });
  }

  private createLanguageSwitcher(): void {
    const width = this.cameras.main.width;
    const container = this.add.container(width - 270, 50);
    container.setScrollFactor(0);
    container.setDepth(102);

    const bg = this.add.rectangle(0, 0, 130, 44, 0x16213E, 0.9);
    bg.setStrokeStyle(2, 0x08D9D6, 0.6);
    bg.setInteractive({ useHandCursor: true });

    const text = this.add.text(0, 0, `🌐 ${this.getCurrentLanguageLabel()}`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '16px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    container.add([bg, text]);
    this.languageButton = container;

    bg.on('pointerdown', () => this.toggleLanguagePanel());

    // 監聽語言變化，同步更新按鈕文字
    const onLangChange = () => {
      text.setText(`🌐 ${this.getCurrentLanguageLabel()}`);
    };
    localization.onLanguageChange(onLangChange);
    // 場景關閉時移除監聽器
    this.events.once('shutdown', () => localization.offLanguageChange(onLangChange));
    this.events.once('destroy', () => localization.offLanguageChange(onLangChange));
  }

  private getCurrentLanguageLabel(): string {
    const current = localization.getLanguage();
    return localization.getLanguageOptions().find((item) => item.code === current)?.label ?? '繁體';
  }

  private toggleLanguagePanel(): void {
    if (this.languagePanel?.active) {
      this.languagePanel.destroy();
      this.languagePanel = undefined;
      return;
    }

    const width = this.cameras.main.width;
    const panel = this.add.container(width - 270, 80);
    panel.setScrollFactor(0);
    panel.setDepth(110);

    const options = localization.getLanguageOptions();
    const panelBg = this.add.rectangle(0, 0, 140, options.length * 34 + 10, 0x0A0E27, 0.95);
    panelBg.setOrigin(0.5, 0);
    panelBg.setStrokeStyle(2, 0x08D9D6, 0.7);
    panel.add(panelBg);

    options.forEach((option, index) => {
      const y = 18 + index * 32;
      const row = this.add.rectangle(0, y, 122, 28, 0x16213E, localization.getLanguage() === option.code ? 1 : 0.8);
      row.setStrokeStyle(1, 0x08D9D6, 0.4);
      row.setInteractive({ useHandCursor: true });

      const label = this.add.text(0, y, option.label, {
        fontFamily: 'Rajdhani, sans-serif',
        fontSize: '15px',
        color: '#FFFFFF',
        fontStyle: 'bold'
      }).setOrigin(0.5);

      row.on('pointerdown', () => this.applyLanguage(option.code));
      panel.add([row, label]);
    });

    this.languagePanel = panel;
  }

  private applyLanguage(language: AppLanguage): void {
    localization.setLanguage(language);
    this.roleManager.applyLocalization();
    this.scene.restart();
  }

  private updateRoleDisplay(): void {
    // 檢查場景是否還在運行
    if (!this.scene.isActive('WorldMapScene') || !this.roleText) {
      console.log('[WorldMapScene] updateRoleDisplay skipped - scene not active or roleText not ready');
      return;
    }
    
    const role = this.roleManager.getCurrentRole();
    console.log('[WorldMapScene] Updating role display:', role.nameZh, role.icon, role.color);
    this.roleText.setText(`${role.icon} ${role.nameZh}`);
    this.roleText.setColor(role.color);
  }

  private checkInteraction(): void {
    const playerPos = this.player.getPosition();
    
    const nearbyNPCs = this.npcs.filter(npc => {
      const distance = Phaser.Math.Distance.Between(
        playerPos.x,
        playerPos.y,
        npc.sprite.x,
        npc.sprite.y
      );
      return distance <= this.interactionRadius;
    });

    if (nearbyNPCs.length > 0) {
      this.startBattle(nearbyNPCs[0]);
    } else {
      this.showMessage(localization.t('noNpc'));
    }
  }

  private startBattle(npc: NPC): void {
    console.log(`[WorldMapScene] Launching BattleScene overlay for ${npc.getDisplayName()}`);
    // 🔥 Use launch (overlay) instead of start (replace) so the map stays visible
    // behind the 75%-opacity battle panel. WorldMap is paused, not destroyed.
    this.scene.launch('BattleScene', {
      npc: npc,
      scamType: npc.scamId,
      scamTypeInfo: npc.scamType,
      playerRole: this.roleManager.getCurrentRole(),
      language: localization.getLanguage()
    });
    this.scene.pause('WorldMapScene');
  }

  private toggleInstructions(): void {
    if (this.instructionsContainer && this.instructionsContainer.active) {
      // Hide instructions
      this.instructionsContainer.destroy();
      this.instructionsContainer = null;
    } else {
      // Show instructions
      this.showInstructions();
    }
  }

  private showInstructions(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    this.instructionsContainer = this.add.container(width / 2, height / 2);
    this.instructionsContainer.setScrollFactor(0);
    this.instructionsContainer.setDepth(200);

    // Modern glass background with blur effect
    const bg = this.add.rectangle(0, 0, 700, 550, 0x0A0E27, 0.95);
    bg.setStrokeStyle(3, 0x08D9D6, 0.8);
    
    // Add background first (bottom layer)
    this.instructionsContainer.add(bg);
    
    // Decorative corner elements
    const cornerSize = 20;
    const corners = [
      { x: -350, y: -275 }, { x: 350, y: -275 },
      { x: -350, y: 275 }, { x: 350, y: 275 }
    ];
    
    corners.forEach(corner => {
      const cornerGraphics = this.add.graphics();
      cornerGraphics.lineStyle(3, 0xFF2E63, 1);
      cornerGraphics.strokeRect(corner.x, corner.y, cornerSize, cornerSize);
      this.instructionsContainer!.add(cornerGraphics);
    });
    
    // Title with glow
    const title = this.add.text(0, -220, localization.t('guideTitle'), {
      fontFamily: 'Orbitron, sans-serif',
      fontSize: '38px',
      color: '#08D9D6',
      fontStyle: 'bold',
      stroke: '#08D9D6',
      strokeThickness: 1
    });
    title.setOrigin(0.5);
    this.instructionsContainer.add(title);

    // Subtitle
    const subtitle = this.add.text(0, -175, localization.t('guideSubtitle'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#FFD93D',
      letterSpacing: 2
    });
    subtitle.setOrigin(0.5);
    this.instructionsContainer.add(subtitle);

    // Content sections with modern styling
    const sections = [
      {
        icon: '🎯',
        title: localization.t('gameGoal'),
        content: localization.t('gameGoalDesc')
      },
      {
        icon: '🕹️',
        title: localization.t('gameControls'),
        content: localization.t('gameControlsDesc')
      },
      {
        icon: '💡',
        title: localization.t('gameTips'),
        content: localization.t('gameTipsDesc')
      }
    ];

    let yOffset = -110;
    sections.forEach((section, index) => {
      // Section container with better visibility
      const sectionBg = this.add.rectangle(0, yOffset, 620, 110, 0x1a2332, 0.9);
      sectionBg.setStrokeStyle(2, 0x08D9D6, 0.6);
      
      // Icon
      const icon = this.add.text(-280, yOffset, section.icon, {
        fontSize: '32px'
      });
      icon.setOrigin(0.5);
      
      // Title
      const sectionTitle = this.add.text(-240, yOffset - 30, section.title, {
        fontFamily: 'Rajdhani, sans-serif',
        fontSize: '20px',
        color: '#FFD93D',
        fontStyle: 'bold'
      });
      sectionTitle.setOrigin(0, 0.5);
      
      // Content
      const content = this.add.text(-240, yOffset + 10, section.content, {
        fontFamily: 'Noto Sans TC, sans-serif',
        fontSize: '13px',
        color: '#FFFFFF',
        lineSpacing: 6,
        wordWrap: { width: 500 }
      });
      content.setOrigin(0, 0.5);
      
      this.instructionsContainer!.add([sectionBg, icon, sectionTitle, content]);
      
      yOffset += 130;
    });
    
    // Close button with modern design
    const closeBg = this.add.rectangle(0, 220, 200, 50, 0xFF2E63, 0.9);
    closeBg.setOrigin(0.5, 0.5);
    closeBg.setStrokeStyle(2, 0xFF6B9D, 0.8);
    
    const closeText = this.add.text(0, 220, localization.t('gameGuideStart'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '20px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    closeText.setOrigin(0.5, 0.5);
    
    // Make button interactive with proper hit area
    closeBg.setInteractive({ useHandCursor: true });
    
    // Hover effect
    closeBg.on('pointerover', () => {
      this.tweens.add({
        targets: [closeBg, closeText],
        scale: 1.08,
        duration: 200,
        ease: 'Back.easeOut'
      });
      closeBg.setFillStyle(0xFF2E63, 1);
      closeBg.setStrokeStyle(3, 0xFF6B9D, 1);
    });
    
    // Hover out effect
    closeBg.on('pointerout', () => {
      this.tweens.add({
        targets: [closeBg, closeText],
        scale: 1,
        duration: 200
      });
      closeBg.setFillStyle(0xFF2E63, 0.9);
      closeBg.setStrokeStyle(2, 0xFF6B9D, 0.8);
    });
    
    // Click effect
    closeBg.on('pointerdown', () => {
      this.tweens.add({
        targets: [closeBg, closeText],
        scale: 0.95,
        duration: 100,
        yoyo: true,
        onComplete: () => {
          // Fade out animation
          this.tweens.add({
            targets: this.instructionsContainer,
            alpha: 0,
            scale: 0.95,
            duration: 300,
            onComplete: () => {
              if (this.instructionsContainer) {
                this.instructionsContainer.destroy();
                this.instructionsContainer = null;
              }
            }
          });
        }
      });
    });

    // Add button last (on top)
    this.instructionsContainer.add([closeBg, closeText]);

    // 透明覆蓋層讓紅色按鈕可以點擊（繞開 Container pointer 問題）
    const closeClickZone = this.add.rectangle(width / 2, height / 2 + 220, 200, 50, 0x000000, 0);
    closeClickZone.setScrollFactor(0);
    closeClickZone.setDepth(210);
    closeClickZone.setInteractive({ useHandCursor: true });
    closeClickZone.on('pointerdown', () => {
      closeClickZone.destroy();
      this.tweens.add({
        targets: this.instructionsContainer,
        alpha: 0,
        scale: 0.9,
        duration: 300,
        ease: 'Back.easeIn',
        onComplete: () => {
          if (this.instructionsContainer) {
            this.instructionsContainer.destroy();
            this.instructionsContainer = null;
          }
        }
      });
    });
    closeClickZone.on('pointerover', () => { closeBg.setFillStyle(0xFF2E63, 1); closeBg.setStrokeStyle(3, 0xFF6B9D, 1); });
    closeClickZone.on('pointerout',  () => { closeBg.setFillStyle(0xFF2E63, 0.9); closeBg.setStrokeStyle(2, 0xFF6B9D, 0.8); });
    // instructionsContainer 關閉時同步移除覆蓋層
    this.events.once('instructions-close', () => closeClickZone.destroy());

    // Entrance animation
    this.instructionsContainer.setAlpha(0);
    this.instructionsContainer.setScale(0.9);
    this.tweens.add({
      targets: this.instructionsContainer,
      alpha: 1,
      scale: 1,
      duration: 400,
      ease: 'Back.easeOut'
    });
  }

  private showMessage(message: string): void {
    const width = this.cameras.main.width;
    
    const messageBox = this.add.container(width / 2, 120);
    messageBox.setScrollFactor(0);
    messageBox.setDepth(150);

    // Modern message design
    const bg = this.add.rectangle(0, 0, 350, 60, 0x16213E, 0.95);
    bg.setStrokeStyle(2, 0xFF2E63, 0.8);
    
    const icon = this.add.text(-150, 0, '⚠️', {
      fontSize: '24px'
    });
    icon.setOrigin(0.5);
    
    const text = this.add.text(-120, 0, message, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#FFFFFF'
    });
    text.setOrigin(0, 0.5);

    messageBox.add([bg, icon, text]);

    // Entrance animation
    messageBox.setAlpha(0);
    messageBox.setY(100);
    this.tweens.add({
      targets: messageBox,
      alpha: 1,
      y: 120,
      duration: 300,
      ease: 'Back.easeOut'
    });

    // Fade out and destroy
    this.tweens.add({
      targets: messageBox,
      alpha: 0,
      y: 100,
      duration: 300,
      delay: 2000,
      ease: 'Back.easeIn',
      onComplete: () => messageBox.destroy()
    });
  }

  update(): void {
    // 檢查場景是否還在運行
    if (!this.scene.isActive('WorldMapScene')) {
      return;
    }
    
    // 檢查玩家是否存在
    if (!this.player || !this.player.sprite) {
      return;
    }
    
    this.player.update();

    // Update NPCs and check proximity
    const playerPos = this.player.getPosition();
    
    this.npcs.forEach(npc => {
      // 檢查 NPC 是否還有效
      if (!npc || !npc.sprite) {
        return;
      }
      
      npc.update();
      
      const distance = Phaser.Math.Distance.Between(
        playerPos.x,
        playerPos.y,
        npc.sprite.x,
        npc.sprite.y
      );

      if (distance <= this.interactionRadius) {
        npc.showInteractionIndicator();
      } else {
        npc.hideInteractionIndicator();
      }
    });
  }

  /**
   * 場景關閉時清理資源
   */
  shutdown(): void {
    console.log('[WorldMapScene] Shutting down scene, cleaning up resources...');
    
    // 移除 RoleManager 的監聽器
    if (this.roleChangeCallback) {
      this.roleManager.offRoleChange(this.roleChangeCallback);
      this.roleChangeCallback = null;
    }
    
    // 停止所有 NPC
    this.npcs.forEach(npc => {
      npc.stopWandering();
      npc.destroy();
    });
    this.npcs = [];
    
    // 清理障礙物
    if (this.obstacles) {
      this.obstacles.clear(true, true);
      this.obstacles = null;
    }
    
    // 清理玩家
    if (this.player) {
      this.player.sprite.destroy();
    }
    
    // 清理 HUD
    if (this.hud) {
      this.hud.destroy();
    }
    
    // 清理說明容器
    if (this.instructionsContainer) {
      this.instructionsContainer.destroy();
      this.instructionsContainer = null;
    }
    
    // 清理返回按鈕
    if (this.homeButton) {
      this.homeButton.destroy();
    }

    if (this.languagePanel) {
      this.languagePanel.destroy();
      this.languagePanel = null as any;
    }
    if (this.languageButton) {
      this.languageButton.destroy();
      this.languageButton = null as any;
    }
    
    // 移除所有鍵盤事件監聽
    this.input.keyboard?.removeAllListeners();
    
    console.log('[WorldMapScene] Cleanup complete');
  }
}
