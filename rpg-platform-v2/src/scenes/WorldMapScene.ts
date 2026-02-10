import Phaser from 'phaser';
import { Player } from '../entities/Player';
import { NPC } from '../entities/NPC';
import { RoleManager } from '../systems/RoleManager';
import { CollisionSystem } from '../systems/CollisionSystem';
import { getAllScamTypes } from '../types/ScamTypes';

export class WorldMapScene extends Phaser.Scene {
  private player!: Player;
  private npcs: NPC[] = [];
  private roleManager: RoleManager;
  private interactionRadius = 80;
  private hud!: Phaser.GameObjects.Container;
  private roleText!: Phaser.GameObjects.Text;
  private map!: Phaser.Tilemaps.Tilemap;
  private groundLayer!: Phaser.Tilemaps.TilemapLayer;
  private collisionSystem!: CollisionSystem;
  private instructionsContainer: Phaser.GameObjects.Container | null = null;
  private homeButton!: Phaser.GameObjects.Container;

  constructor() {
    super({ key: 'WorldMapScene' });
    this.roleManager = RoleManager.getInstance();
  }

  create(): void {
    // Create professional tilemap background (RPG Maker Forest Town map)
    this.createTilemapWorld();

    // Calculate map dimensions from loaded map (40x40 tiles * 48px = 1920x1920)
    const mapPixelWidth = this.map.widthInPixels;
    const mapPixelHeight = this.map.heightInPixels;

    console.log(`[WorldMapScene] Map size: ${mapPixelWidth}x${mapPixelHeight} pixels`);

    // Initialize collision system with RPG Maker rules
    this.collisionSystem = new CollisionSystem(this, this.map);
    this.loadTilesetCollisionData();

    // Create player at center of map
    this.player = new Player(this, mapPixelWidth / 2, mapPixelHeight / 2);
    
    // Connect collision system to player
    this.player.setCollisionSystem(this.collisionSystem);

    // Create NPCs at different positions
    this.createNPCs(mapPixelWidth, mapPixelHeight);

    // Setup camera to follow player
    this.cameras.main.startFollow(this.player.sprite, true, 0.1, 0.1);
    this.cameras.main.setBounds(0, 0, mapPixelWidth, mapPixelHeight);
    this.physics.world.setBounds(0, 0, mapPixelWidth, mapPixelHeight);
    
    // Set camera zoom for better view (RPG Maker standard view)
    this.cameras.main.setZoom(1.0);

    // Create HUD
    this.createHUD();
    
    // Create home button in top right
    this.createHomeButton();

    // Setup input
    this.setupInput();

    // Add instructions (hidden by default, toggle with H)
    this.showInstructions();
    
    // Add ambient effects
    this.addAmbientEffects();
  }

  private createTilemapWorld(): void {
    // Load test map with proper tileset
    console.log('[WorldMapScene] Loading test map...');
    
    // Load the test map
    this.map = this.make.tilemap({ key: 'test-minimal' });
    
    // Add tileset image (using Outside_B tileset - proper non-autotile format)
    const tileset = this.map.addTilesetImage('tileset-outside-b', 'tileset-outside-b');
    
    if (!tileset) {
      console.error('[WorldMapScene] Failed to load tileset');
      return;
    }
    
    console.log(`[WorldMapScene] Map loaded: ${this.map.width}x${this.map.height} tiles`);
    
    // Create layers - try by index first (more reliable)
    let groundLayer: Phaser.Tilemaps.TilemapLayer | null = null;
    let lowerLayer: Phaser.Tilemaps.TilemapLayer | null = null;
    let upperLayer: Phaser.Tilemaps.TilemapLayer | null = null;
    let shadowLayer: Phaser.Tilemaps.TilemapLayer | null = null;
    
    // Try to create layers by index (0, 1, 2, 3)
    try {
      groundLayer = this.map.createLayer(0, tileset, 0, 0);
      if (this.map.layers.length > 1) lowerLayer = this.map.createLayer(1, tileset, 0, 0);
      if (this.map.layers.length > 2) upperLayer = this.map.createLayer(2, tileset, 0, 0);
      if (this.map.layers.length > 3) shadowLayer = this.map.createLayer(3, tileset, 0, 0);
    } catch (e) {
      console.error('[WorldMapScene] Failed to create layers by index:', e);
    }
    
    if (!groundLayer) {
      console.error('[WorldMapScene] Failed to create ground layer');
      return;
    }
    
    this.groundLayer = groundLayer;
    
    // Set layer depths (RPG Maker standard)
    this.groundLayer.setDepth(0);
    if (lowerLayer) lowerLayer.setDepth(1);
    if (shadowLayer) shadowLayer.setDepth(0.5);
    if (upperLayer) upperLayer.setDepth(100);
    
    console.log('[WorldMapScene] All layers created successfully');
    
    // Load NPCs from map events
    this.loadMapEvents();
  }

  private loadMapEvents(): void {
    // Get events object layer from the map
    const eventLayer = this.map.getObjectLayer('Events');
    
    if (!eventLayer) {
      console.log('[WorldMapScene] No events layer found');
      return;
    }
    
    console.log(`[WorldMapScene] Found ${eventLayer.objects.length} events`);
    
    // Process events (NPCs, triggers, etc.)
    eventLayer.objects.forEach(obj => {
      if (obj.type === 'event') {
        console.log(`[WorldMapScene] Event: ${obj.name} at (${obj.x}, ${obj.y})`);
        // Events will be handled separately
      }
    });
  }

  /**
   * Load tileset collision data from RPG Maker
   * This loads the flags array that defines which tiles are passable
   */
  private loadTilesetCollisionData(): void {
    console.log('[WorldMapScene] Loading tileset collision data...');
    
    // For test map, use simple collision rules
    console.log('[WorldMapScene] Using test map collision configuration');
    this.setupTestMapCollisionRules();
  }

  /**
   * Setup collision rules for test map
   * Tile 1 and 65 are borders (impassable), tile 81 is walkable
   */
  private setupTestMapCollisionRules(): void {
    // Border tiles - impassable
    this.collisionSystem.setTileFlags(1, 0x0010);  // Outer border
    this.collisionSystem.setTileFlags(65, 0x0010); // Inner border
    
    // Tile 81 is walkable (no flags needed, default is passable)
    
    console.log('[WorldMapScene] Test map collision rules configured');
  }

  private addAmbientEffects(): void {
    // Add subtle particles for atmosphere (RPG Maker style)
    const mapPixelWidth = this.map.widthInPixels;
    const mapPixelHeight = this.map.heightInPixels;
    
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
   * 
   * 重要改變：不再使用人名（陳婆婆、王小明等），
   * 而是使用騙案類型（投資詐騙、釣魚短訊等）
   */
  private createNPCs(mapWidth: number, mapHeight: number): void {
    const centerX = mapWidth / 2;
    const centerY = mapHeight / 2;

    // 定義 NPC 位置和對應的騙案類型
    const npcData: Array<{ x: number; y: number; scamId: string }> = [
      // 市中心區域 - 高危險騙案
      { x: centerX + 200, y: centerY, scamId: 'investment' },           // 💰 投資詐騙
      { x: centerX - 200, y: centerY + 150, scamId: 'phishing' },       // 📱 釣魚短訊
      { x: centerX + 300, y: centerY - 200, scamId: 'romance' },        // 💕 愛情詐騙
      { x: centerX - 300, y: centerY - 100, scamId: 'impersonation' },  // 👮 假冒官員
      
      // 外圍區域 - 中等危險騙案
      { x: centerX, y: centerY + 400, scamId: 'banking' },              // 🏦 假冒銀行
      { x: centerX + 500, y: centerY + 300, scamId: 'crypto' },         // ₿ 加密貨幣
      
      // 四個角落 - 各種騙案類型
      { x: 300, y: 300, scamId: 'whatsapp' },                           // 💬 WhatsApp 詐騙
      { x: mapWidth - 300, y: 300, scamId: 'shopping' },                // 🛒 購物詐騙
      { x: 300, y: mapHeight - 300, scamId: 'job' },                    // 💼 求職詐騙
      { x: mapWidth - 300, y: mapHeight - 300, scamId: 'prize' },       // 🎁 中獎詐騙
      
      // 額外騙案類型
      { x: centerX + 400, y: centerY + 200, scamId: 'rental' },         // 🏠 租屋詐騙
      { x: centerX - 400, y: centerY - 300, scamId: 'tech_support' },   // 💻 技術支援
      { x: centerX + 100, y: centerY - 400, scamId: 'charity' }         // ❤️ 慈善詐騙
    ];

    console.log(`[WorldMapScene] 創建 ${npcData.length} 個騙案類型 NPC`);

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
    const roleLabel = this.add.text(85, 15, '當前角色', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '11px',
      color: '#B8C5D6',
      alpha: 0.8
    });
    roleLabel.setOrigin(0, 0.5);

    roleContainer.add([roleBox, iconBg, this.roleText, roleLabel]);
    this.hud.add(roleContainer);

    // Update role display
    this.updateRoleDisplay();
    this.roleManager.onRoleChange(() => this.updateRoleDisplay());

    // Modern instructions panel
    const instructionsContainer = this.add.container(20, 100);
    
    const instructionsBox = this.add.rectangle(0, 0, 300, 90, 0x16213E, 0.85);
    instructionsBox.setOrigin(0, 0);
    instructionsBox.setStrokeStyle(2, 0xFF2E63, 0.5);
    
    const instructionsTitle = this.add.text(15, 12, '⌨️ 操作提示', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '14px',
      color: '#FFD93D',
      fontStyle: 'bold'
    });
    
    const instructionsText = this.add.text(15, 35, 
      '方向鍵/WASD - 移動\n' +
      'E - 互動 | H - 說明 | F1/F2/F3 - 切換角色', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '11px',
      color: '#B8C5D6',
      lineSpacing: 4
    });
    
    instructionsContainer.add([instructionsBox, instructionsTitle, instructionsText]);
    this.hud.add(instructionsContainer);

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
    const text = this.add.text(buttonX + 15, buttonY, '返回主頁', {
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

  private updateRoleDisplay(): void {
    const role = this.roleManager.getCurrentRole();
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
      this.showMessage('附近沒有可互動的NPC');
    }
  }

  private startBattle(npc: NPC): void {
    console.log(`[WorldMapScene] Starting battle with ${npc.getDisplayName()}`);
    this.scene.start('BattleScene', {
      npc: npc,
      scamType: npc.scamId,           // 傳遞騙案類型 ID
      scamTypeInfo: npc.scamType,     // 傳遞完整騙案類型資訊
      playerRole: this.roleManager.getCurrentRole()
    });
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
    const title = this.add.text(0, -220, '🎮 遊戲指南', {
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
    const subtitle = this.add.text(0, -175, '香港反詐騙 AI 模擬對話系統', {
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
        title: '遊戲目標',
        content: '與 NPC 互動，學習識別和防範各種詐騙手法'
      },
      {
        icon: '🕹️',
        title: '操作說明',
        content: '方向鍵 或 WASD - 移動角色\nE 鍵 - 與 NPC 互動\nH 鍵 - 顯示/隱藏說明\nF1/F2/F3 - 切換角色（受害者/騙徒/專家）'
      },
      {
        icon: '💡',
        title: '遊戲提示',
        content: '靠近 NPC 會顯示互動提示\n不同角色有不同的對話選項\n完成對話可獲得訓練數據'
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
    
    const closeText = this.add.text(0, 220, '開始遊戲 (H)', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '20px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    closeText.setOrigin(0.5, 0.5);
    
    // Make button interactive with proper hit area
    closeBg.setInteractive({ 
      useHandCursor: true,
      hitArea: new Phaser.Geom.Rectangle(80, 360, 200, 50),
      hitAreaCallback: Phaser.Geom.Rectangle.Contains
    });
    
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
    this.player.update();

    // Update NPCs and check proximity
    const playerPos = this.player.getPosition();
    
    this.npcs.forEach(npc => {
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
}
