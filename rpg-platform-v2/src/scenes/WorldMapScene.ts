import Phaser from 'phaser';
import { Player } from '../entities/Player';
import { NPC, NPCType } from '../entities/NPC';
import { RoleManager } from '../systems/RoleManager';
import { CollisionSystem } from '../systems/CollisionSystem';

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

  private createNPCs(mapWidth: number, mapHeight: number): void {
    const centerX = mapWidth / 2;
    const centerY = mapHeight / 2;

    // Place NPCs in structured positions (RPG Maker style)
    const npcData: Array<{ x: number; y: number; type: NPCType }> = [
      // Town center NPCs
      { x: centerX + 200, y: centerY, type: 'elderly' },
      { x: centerX - 200, y: centerY + 150, type: 'student' },
      { x: centerX + 300, y: centerY - 200, type: 'average' },
      { x: centerX - 300, y: centerY - 100, type: 'overconfident' },
      
      // Outer area NPCs
      { x: centerX, y: centerY + 400, type: 'scammer' },
      { x: centerX + 500, y: centerY + 300, type: 'expert' },
      
      // Additional NPCs in corners
      { x: 300, y: 300, type: 'elderly' },
      { x: mapWidth - 300, y: 300, type: 'student' },
      { x: 300, y: mapHeight - 300, type: 'average' },
      { x: mapWidth - 300, y: mapHeight - 300, type: 'overconfident' }
    ];

    npcData.forEach(data => {
      const npc = new NPC(this, data.x, data.y, data.type);
      this.npcs.push(npc);
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

    // Role switching (1, 2, 3)
    this.input.keyboard?.on('keydown-ONE', () => {
      this.roleManager.switchRole('victim');
    });

    this.input.keyboard?.on('keydown-TWO', () => {
      this.roleManager.switchRole('scammer');
    });

    this.input.keyboard?.on('keydown-THREE', () => {
      this.roleManager.switchRole('expert');
    });
  }

  private createHUD(): void {
    this.hud = this.add.container(0, 0);
    this.hud.setScrollFactor(0);
    this.hud.setDepth(100);

    // Role display
    const roleBox = this.add.rectangle(150, 30, 280, 50, 0x000000, 0.7);
    this.roleText = this.add.text(150, 30, '', {
      fontSize: '18px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    this.roleText.setOrigin(0.5);

    this.hud.add([roleBox, this.roleText]);

    // Update role display
    this.updateRoleDisplay();
    this.roleManager.onRoleChange(() => this.updateRoleDisplay());

    // Instructions
    const instructionsBox = this.add.rectangle(150, 80, 280, 40, 0x000000, 0.7);
    const instructionsText = this.add.text(150, 80, '按 E 互動 | 按 H 顯示說明', {
      fontSize: '12px',
      color: '#A0AEC0'
    });
    instructionsText.setOrigin(0.5);

    this.hud.add([instructionsBox, instructionsText]);
  }

  private createHomeButton(): void {
    const width = this.cameras.main.width;
    
    // Position at top right corner
    this.homeButton = this.add.container(width - 70, 30);
    this.homeButton.setScrollFactor(0);
    this.homeButton.setDepth(100);
    
    const bg = this.add.rectangle(0, 0, 120, 40, 0xFF6B6B, 0.9);
    bg.setStrokeStyle(2, 0xffffff, 0.8);
    
    const text = this.add.text(0, 0, '🏠 主頁', {
      fontSize: '16px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    text.setOrigin(0.5);
    
    this.homeButton.add([bg, text]);
    
    // Make the entire container interactive with correct hit area
    this.homeButton.setInteractive(
      new Phaser.Geom.Rectangle(-60, -20, 120, 40),
      Phaser.Geom.Rectangle.Contains
    );
    
    // Enable input on the container
    this.homeButton.input!.cursor = 'pointer';
    
    this.homeButton.on('pointerover', () => {
      this.homeButton.setScale(1.05);
      bg.setFillStyle(0xFF7B7B, 0.9);
    });
    
    this.homeButton.on('pointerout', () => {
      this.homeButton.setScale(1);
      bg.setFillStyle(0xFF6B6B, 0.9);
    });
    
    this.homeButton.on('pointerdown', () => {
      this.homeButton.setScale(0.95);
      bg.setFillStyle(0xFF5B5B, 0.9);
      
      // Return to main menu immediately
      this.scene.start('MainMenuScene');
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
    console.log(`[WorldMapScene] Starting battle with ${npc.name}`);
    this.scene.start('BattleScene', {
      npc: npc,
      npcType: npc.type,
      npcName: npc.name,
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

    const bg = this.add.rectangle(0, 0, 600, 460, 0x000000, 0.95);
    bg.setStrokeStyle(3, 0x6C5CE7);
    
    const title = this.add.text(0, -180, '🎮 香港反詐騙 RPG 訓練', {
      fontSize: '30px',
      color: '#FFD700',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    const text = this.add.text(0, -30, 
      '🎯 遊戲目標\n' +
      '與 NPC 互動，學習識別和防範詐騙\n\n' +
      '🕹️ 操作說明\n' +
      '• 方向鍵 或 WASD - 移動角色\n' +
      '• E 鍵 - 與 NPC 互動\n' +
      '• H 鍵 - 顯示/隱藏說明\n' +
      '• 1/2/3 - 切換角色（受害者/騙徒/專家）\n' +
      '• 右上角按鈕 - 返回主頁\n\n' +
      '💡 提示：靠近 NPC 會顯示互動提示',
      {
        fontSize: '14px',
        color: '#E0E0E0',
        align: 'center',
        lineSpacing: 8
      }
    );
    text.setOrigin(0.5);
    
    const closeBtn = this.add.text(0, 170, '關閉 (H)', {
      fontSize: '18px',
      color: '#ffffff',
      backgroundColor: '#6C5CE7',
      padding: { x: 20, y: 10 }
    });
    closeBtn.setOrigin(0.5);
    
    // Make button interactive
    closeBtn.setInteractive({ useHandCursor: true });
    
    // Immediate visual feedback on hover
    closeBtn.on('pointerover', () => {
      closeBtn.setScale(1.1);
      closeBtn.setStyle({ backgroundColor: '#7C6CF7' });
    });
    
    closeBtn.on('pointerout', () => {
      closeBtn.setScale(1);
      closeBtn.setStyle({ backgroundColor: '#6C5CE7' });
    });
    
    // Instant close on click
    closeBtn.on('pointerdown', () => {
      closeBtn.setScale(0.95);
      closeBtn.setStyle({ backgroundColor: '#5C4CD7' });
      
      // Destroy instructions
      if (this.instructionsContainer) {
        this.instructionsContainer.destroy();
        this.instructionsContainer = null;
      }
    });

    this.instructionsContainer.add([bg, title, text, closeBtn]);
  }

  private showMessage(message: string): void {
    const width = this.cameras.main.width;
    
    const messageBox = this.add.container(width / 2, 100);
    messageBox.setScrollFactor(0);
    messageBox.setDepth(150);

    const bg = this.add.rectangle(0, 0, 300, 50, 0xFF6B6B, 0.9);
    const text = this.add.text(0, 0, message, {
      fontSize: '14px',
      color: '#ffffff'
    });
    text.setOrigin(0.5);

    messageBox.add([bg, text]);

    // Fade out and destroy
    this.tweens.add({
      targets: messageBox,
      alpha: 0,
      duration: 2000,
      delay: 1000,
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
