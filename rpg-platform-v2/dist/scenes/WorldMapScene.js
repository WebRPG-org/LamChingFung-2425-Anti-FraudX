import Phaser from 'phaser';
import { Player } from '../entities/Player';
import { NPC } from '../entities/NPC';
import { RoleManager } from '../systems/RoleManager';
import { CollisionSystem } from '../systems/CollisionSystem';
export class WorldMapScene extends Phaser.Scene {
    constructor() {
        super({ key: 'WorldMapScene' });
        this.npcs = [];
        this.interactionRadius = 80;
        this.roleManager = RoleManager.getInstance();
    }
    create() {
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
        // Setup input
        this.setupInput();
        // Add instructions
        this.showInstructions();
        // Add ambient effects
        this.addAmbientEffects();
    }
    createTilemapWorld() {
        // Load RPG Maker MV map: Forest Town (40x40 tiles)
        console.log('[WorldMapScene] Loading Forest Town map...');
        this.map = this.make.tilemap({ key: 'forest-town' });
        // Add tileset image (RPG Maker uses Outside_A2 tileset)
        const tileset = this.map.addTilesetImage('tileset-outside', 'tileset-outside');
        if (!tileset) {
            console.error('[WorldMapScene] Failed to load tileset');
            return;
        }
        console.log(`[WorldMapScene] Map loaded: ${this.map.width}x${this.map.height} tiles`);
        // Create layers from RPG Maker map (Ground, Lower, Upper, Shadow)
        const groundLayer = this.map.createLayer('Ground', tileset);
        const lowerLayer = this.map.createLayer('Lower', tileset);
        const upperLayer = this.map.createLayer('Upper', tileset);
        const shadowLayer = this.map.createLayer('Shadow', tileset);
        if (!groundLayer) {
            console.error('[WorldMapScene] Failed to create ground layer');
            return;
        }
        this.groundLayer = groundLayer;
        // Set layer depths (RPG Maker standard)
        this.groundLayer.setDepth(0);
        if (lowerLayer)
            lowerLayer.setDepth(1);
        if (shadowLayer)
            shadowLayer.setDepth(0.5);
        if (upperLayer)
            upperLayer.setDepth(100);
        console.log('[WorldMapScene] All layers created successfully');
        // Load NPCs from map events
        this.loadMapEvents();
    }
    loadMapEvents() {
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
    loadTilesetCollisionData() {
        console.log('[WorldMapScene] Loading tileset collision data...');
        // Try to load flags from cache (if converter included them)
        const mapData = this.cache.json.get('forest-town');
        if (mapData && mapData.tilesetFlags) {
            this.collisionSystem.loadFlagsFromData(mapData.tilesetFlags);
            console.log('[WorldMapScene] Loaded collision flags from map data');
            return;
        }
        // Fallback: Define collision rules manually based on RPG Maker standards
        console.log('[WorldMapScene] Using manual collision configuration');
        this.setupManualCollisionRules();
    }
    /**
     * Setup manual collision rules for common tile patterns
     * This is used when tileset flags are not available
     */
    setupManualCollisionRules() {
        // Water tiles - completely impassable (空氣牆)
        const waterTiles = [2816, 2817, 2818, 2832, 2833, 2834, 2840, 2841, 2842];
        waterTiles.forEach(tileId => {
            this.collisionSystem.setTileFlags(tileId, 0x0010); // FLAG_IMPASSABLE
        });
        // Building/wall tiles - impassable
        const buildingTiles = [7760, 7761, 7762, 7776, 7777, 7778, 7784, 7785, 7786, 7800, 7801, 7802];
        buildingTiles.forEach(tileId => {
            this.collisionSystem.setTileFlags(tileId, 0x0010); // FLAG_IMPASSABLE
        });
        // Tree/obstacle tiles - impassable
        const obstacleTiles = [2226, 2228, 2230, 2232];
        obstacleTiles.forEach(tileId => {
            this.collisionSystem.setTileFlags(tileId, 0x0010); // FLAG_IMPASSABLE
        });
        // Counter tiles - can pass from below (☆ passable)
        const counterTiles = [2082, 2084, 2088, 2086];
        counterTiles.forEach(tileId => {
            this.collisionSystem.setTileFlags(tileId, 0x0800); // FLAG_STAR
        });
        console.log('[WorldMapScene] Manual collision rules configured');
    }
    addAmbientEffects() {
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
            }
        });
        particles.setDepth(0);
    }
    createNPCs(mapWidth, mapHeight) {
        const centerX = mapWidth / 2;
        const centerY = mapHeight / 2;
        // Place NPCs in structured positions (RPG Maker style)
        const npcData = [
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
    setupInput() {
        // Interaction key (E)
        this.input.keyboard?.on('keydown-E', () => {
            this.checkInteraction();
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
        // ESC to return to menu
        this.input.keyboard?.on('keydown-ESC', () => {
            this.scene.start('MainMenuScene');
        });
    }
    createHUD() {
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
        const instructionsText = this.add.text(150, 80, '按 E 互動 | 1/2/3 切換角色', {
            fontSize: '12px',
            color: '#A0AEC0'
        });
        instructionsText.setOrigin(0.5);
        this.hud.add([instructionsBox, instructionsText]);
    }
    updateRoleDisplay() {
        const role = this.roleManager.getCurrentRole();
        this.roleText.setText(`${role.icon} ${role.nameZh}`);
        this.roleText.setColor(role.color);
    }
    checkInteraction() {
        const playerPos = this.player.getPosition();
        const nearbyNPCs = this.npcs.filter(npc => {
            const distance = Phaser.Math.Distance.Between(playerPos.x, playerPos.y, npc.sprite.x, npc.sprite.y);
            return distance <= this.interactionRadius;
        });
        if (nearbyNPCs.length > 0) {
            this.startBattle(nearbyNPCs[0]);
        }
        else {
            this.showMessage('附近沒有可互動的NPC');
        }
    }
    startBattle(npc) {
        console.log(`[WorldMapScene] Starting battle with ${npc.name}`);
        this.scene.start('BattleScene', {
            npc: npc,
            npcType: npc.type,
            npcName: npc.name,
            playerRole: this.roleManager.getCurrentRole()
        });
    }
    showInstructions() {
        const width = this.cameras.main.width;
        const height = this.cameras.main.height;
        const instructions = this.add.container(width / 2, height / 2);
        instructions.setScrollFactor(0);
        instructions.setDepth(200);
        const bg = this.add.rectangle(0, 0, 600, 400, 0x000000, 0.95);
        bg.setStrokeStyle(3, 0x6C5CE7);
        const title = this.add.text(0, -150, '🎮 香港反詐騙 RPG 訓練', {
            fontSize: '28px',
            color: '#FFD700',
            fontStyle: 'bold'
        });
        title.setOrigin(0.5);
        const text = this.add.text(0, -50, '🎯 遊戲目標\n' +
            '與 NPC 互動，學習識別和防範詐騙\n\n' +
            '🕹️ 操作說明\n' +
            '• 方向鍵 或 WASD - 移動角色\n' +
            '• E 鍵 - 與 NPC 互動\n' +
            '• 1/2/3 - 切換角色（受害者/騙徒/專家）\n' +
            '• ESC - 返回主選單\n\n' +
            '💡 提示：靠近 NPC 會顯示互動提示', {
            fontSize: '14px',
            color: '#E0E0E0',
            align: 'center',
            lineSpacing: 8
        });
        text.setOrigin(0.5);
        const startBtn = this.add.text(0, 140, '點擊開始遊戲', {
            fontSize: '18px',
            color: '#ffffff',
            backgroundColor: '#6C5CE7',
            padding: { x: 20, y: 10 }
        });
        startBtn.setOrigin(0.5);
        startBtn.setInteractive({ useHandCursor: true });
        startBtn.on('pointerover', () => {
            startBtn.setScale(1.1);
        });
        startBtn.on('pointerout', () => {
            startBtn.setScale(1);
        });
        startBtn.on('pointerdown', () => {
            instructions.destroy();
        });
        instructions.add([bg, title, text, startBtn]);
        // Auto dismiss after 8 seconds
        this.time.delayedCall(8000, () => {
            if (instructions.active) {
                this.tweens.add({
                    targets: instructions,
                    alpha: 0,
                    duration: 500,
                    onComplete: () => instructions.destroy()
                });
            }
        });
    }
    showMessage(message) {
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
    update() {
        this.player.update();
        // Update NPCs and check proximity
        const playerPos = this.player.getPosition();
        this.npcs.forEach(npc => {
            npc.update();
            const distance = Phaser.Math.Distance.Between(playerPos.x, playerPos.y, npc.sprite.x, npc.sprite.y);
            if (distance <= this.interactionRadius) {
                npc.showInteractionIndicator();
            }
            else {
                npc.hideInteractionIndicator();
            }
        });
    }
}
