# Quick Start Guide: 2D RPG Platform (Option B)
## Implementation Starter Kit

**Date:** 2026-02-04

---

## 1. Project Setup

### Initialize Project

```bash
# Create project directory
mkdir rpg-platform-v2
cd rpg-platform-v2

# Initialize npm project
npm init -y

# Install dependencies
npm install phaser@3.60.0
npm install typescript @types/node
npm install vite
npm install zustand  # State management
npm install howler   # Audio

# Install dev dependencies
npm install -D @types/phaser
npm install -D vite-plugin-static-copy
```

### Project Configuration

**package.json**
```json
{
  "name": "ai-antiscam-rpg-v2",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "phaser": "^3.60.0",
    "zustand": "^4.4.0",
    "howler": "^2.2.3"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/phaser": "^3.60.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

**tsconfig.json**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "types": ["phaser"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

**vite.config.ts**
```typescript
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
});
```

---

## 2. Core Game Structure

### Main Entry Point

**src/main.ts**
```typescript
import Phaser from 'phaser';
import { BootScene } from './scenes/BootScene';
import { MainMenuScene } from './scenes/MainMenuScene';
import { WorldMapScene } from './scenes/WorldMapScene';
import { BattleScene } from './scenes/BattleScene';
import { AutoModeScene } from './scenes/AutoModeScene';

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 1280,
  height: 720,
  parent: 'game-container',
  backgroundColor: '#2d2d2d',
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0 },
      debug: false
    }
  },
  scene: [
    BootScene,
    MainMenuScene,
    WorldMapScene,
    BattleScene,
    AutoModeScene
  ]
};

const game = new Phaser.Game(config);

export default game;
```

### Boot Scene

**src/scenes/BootScene.ts**
```typescript
import Phaser from 'phaser';

export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
  }

  preload(): void {
    // Load loading bar assets
    this.load.image('logo', 'assets/ui/logo.png');
    
    // Create loading bar
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;
    
    const progressBar = this.add.graphics();
    const progressBox = this.add.graphics();
    progressBox.fillStyle(0x222222, 0.8);
    progressBox.fillRect(width / 2 - 160, height / 2 - 25, 320, 50);
    
    this.load.on('progress', (value: number) => {
      progressBar.clear();
      progressBar.fillStyle(0x6C5CE7, 1);
      progressBar.fillRect(width / 2 - 150, height / 2 - 15, 300 * value, 30);
    });
    
    this.load.on('complete', () => {
      progressBar.destroy();
      progressBox.destroy();
    });
    
    // Load all game assets
    this.loadAssets();
  }

  private loadAssets(): void {
    // Sprites
    this.load.spritesheet('player', 'assets/sprites/player.png', {
      frameWidth: 32,
      frameHeight: 32
    });
    
    this.load.spritesheet('npcs', 'assets/sprites/npcs.png', {
      frameWidth: 32,
      frameHeight: 32
    });
    
    // Tilesets
    this.load.image('tiles', 'assets/tilesets/urban.png');
    this.load.tilemapTiledJSON('map', 'assets/maps/hongkong.json');
    
    // UI
    this.load.image('hud', 'assets/ui/hud.png');
    this.load.image('dialogue-box', 'assets/ui/dialogue-box.png');
    
    // Audio
    this.load.audio('bgm-world', 'assets/audio/bgm-world.mp3');
    this.load.audio('bgm-battle', 'assets/audio/bgm-battle.mp3');
    this.load.audio('sfx-interact', 'assets/audio/sfx-interact.mp3');
  }

  create(): void {
    this.scene.start('MainMenuScene');
  }
}
```

---

## 3. Role System Implementation

**src/systems/RoleManager.ts**
```typescript
export type RoleType = 'victim' | 'scammer' | 'expert';

export interface Role {
  id: RoleType;
  name: string;
  nameZh: string;
  color: string;
  description: string;
  aiOpponents: string[];
}

export class RoleManager {
  private static instance: RoleManager;
  private currentRole: Role;
  
  private roles: Map<RoleType, Role> = new Map([
    ['victim', {
      id: 'victim',
      name: 'Victim',
      nameZh: '受害者',
      color: '#0984E3',
      description: 'Defend against scam attempts',
      aiOpponents: ['scammer', 'expert', 'recorder']
    }],
    ['scammer', {
      id: 'scammer',
      name: 'Scammer',
      nameZh: '騙徒',
      color: '#FF6B6B',
      description: 'Manipulate victims using tactics',
      aiOpponents: ['victim', 'expert', 'recorder']
    }],
    ['expert', {
      id: 'expert',
      name: 'Expert',
      nameZh: '防詐專家',
      color: '#00B894',
      description: 'Intervene and educate victims',
      aiOpponents: ['scammer', 'victim', 'recorder']
    }]
  ]);

  private constructor() {
    this.currentRole = this.roles.get('victim')!;
  }

  static getInstance(): RoleManager {
    if (!RoleManager.instance) {
      RoleManager.instance = new RoleManager();
    }
    return RoleManager.instance;
  }

  getCurrentRole(): Role {
    return this.currentRole;
  }

  switchRole(roleType: RoleType): void {
    const newRole = this.roles.get(roleType);
    if (newRole) {
      this.currentRole = newRole;
      this.notifyRoleChange();
    }
  }

  private notifyRoleChange(): void {
    // Emit event for UI updates
    window.dispatchEvent(new CustomEvent('roleChanged', {
      detail: this.currentRole
    }));
  }
}
```

---

## 4. World Map Scene

**src/scenes/WorldMapScene.ts**
```typescript
import Phaser from 'phaser';
import { Player } from '../entities/Player';
import { NPC } from '../entities/NPC';
import { RoleManager } from '../systems/RoleManager';

export class WorldMapScene extends Phaser.Scene {
  private player!: Player;
  private npcs: NPC[] = [];
  private roleManager: RoleManager;
  private interactionRadius = 64;

  constructor() {
    super({ key: 'WorldMapScene' });
    this.roleManager = RoleManager.getInstance();
  }

  create(): void {
    // Create tilemap
    const map = this.make.tilemap({ key: 'map' });
    const tileset = map.addTilesetImage('urban', 'tiles');
    
    // Create layers
    const groundLayer = map.createLayer('Ground', tileset!, 0, 0);
    const buildingsLayer = map.createLayer('Buildings', tileset!, 0, 0);
    
    // Set collision
    buildingsLayer?.setCollisionByProperty({ collides: true });
    
    // Create player
    this.player = new Player(this, 400, 300);
    
    // Create NPCs
    this.createNPCs();
    
    // Setup camera
    this.cameras.main.startFollow(this.player.sprite);
    this.cameras.main.setBounds(0, 0, map.widthInPixels, map.heightInPixels);
    
    // Setup physics
    this.physics.add.collider(this.player.sprite, buildingsLayer!);
    
    // Setup input
    this.setupInput();
    
    // Create HUD
    this.createHUD();
  }

  private createNPCs(): void {
    const npcPositions = [
      { x: 500, y: 300, type: 'elderly' },
      { x: 600, y: 400, type: 'student' },
      { x: 700, y: 350, type: 'average' },
      { x: 450, y: 450, type: 'overconfident' }
    ];

    npcPositions.forEach(pos => {
      const npc = new NPC(this, pos.x, pos.y, pos.type);
      this.npcs.push(npc);
    });
  }

  private setupInput(): void {
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
  }

  private checkInteraction(): void {
    const nearbyNPCs = this.npcs.filter(npc => {
      const distance = Phaser.Math.Distance.Between(
        this.player.sprite.x,
        this.player.sprite.y,
        npc.sprite.x,
        npc.sprite.y
      );
      return distance <= this.interactionRadius;
    });

    if (nearbyNPCs.length > 0) {
      this.startBattle(nearbyNPCs[0]);
    }
  }

  private startBattle(npc: NPC): void {
    this.scene.start('BattleScene', {
      npc: npc,
      playerRole: this.roleManager.getCurrentRole()
    });
  }

  private createHUD(): void {
    // Create HUD elements (simplified)
    const hud = this.add.container(10, 10);
    
    const roleText = this.add.text(0, 0, '', {
      fontSize: '18px',
      color: '#ffffff',
      backgroundColor: '#000000',
      padding: { x: 10, y: 5 }
    });
    
    hud.add(roleText);
    hud.setScrollFactor(0);
    
    // Update role text
    const updateRoleText = () => {
      const role = this.roleManager.getCurrentRole();
      roleText.setText(`Role: ${role.nameZh}`);
      roleText.setBackgroundColor(role.color);
    };
    
    updateRoleText();
    window.addEventListener('roleChanged', updateRoleText);
  }

  update(): void {
    this.player.update();
  }
}
```

---

## 5. Player Entity

**src/entities/Player.ts**
```typescript
import Phaser from 'phaser';

export class Player {
  public sprite: Phaser.Physics.Arcade.Sprite;
  private scene: Phaser.Scene;
  private speed = 160;
  private cursors: Phaser.Types.Input.Keyboard.CursorKeys;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    this.scene = scene;
    
    // Create sprite
    this.sprite = scene.physics.add.sprite(x, y, 'player');
    this.sprite.setCollideWorldBounds(true);
    
    // Setup animations
    this.createAnimations();
    
    // Setup input
    this.cursors = scene.input.keyboard!.createCursorKeys();
  }

  private createAnimations(): void {
    // Down
    this.scene.anims.create({
      key: 'walk-down',
      frames: this.scene.anims.generateFrameNumbers('player', { start: 0, end: 3 }),
      frameRate: 10,
      repeat: -1
    });
    
    // Up
    this.scene.anims.create({
      key: 'walk-up',
      frames: this.scene.anims.generateFrameNumbers('player', { start: 4, end: 7 }),
      frameRate: 10,
      repeat: -1
    });
    
    // Left
    this.scene.anims.create({
      key: 'walk-left',
      frames: this.scene.anims.generateFrameNumbers('player', { start: 8, end: 11 }),
      frameRate: 10,
      repeat: -1
    });
    
    // Right
    this.scene.anims.create({
      key: 'walk-right',
      frames: this.scene.anims.generateFrameNumbers('player', { start: 12, end: 15 }),
      frameRate: 10,
      repeat: -1
    });
  }

  update(): void {
    const { left, right, up, down } = this.cursors;
    
    // Reset velocity
    this.sprite.setVelocity(0);
    
    // Horizontal movement
    if (left.isDown) {
      this.sprite.setVelocityX(-this.speed);
      this.sprite.anims.play('walk-left', true);
    } else if (right.isDown) {
      this.sprite.setVelocityX(this.speed);
      this.sprite.anims.play('walk-right', true);
    }
    
    // Vertical movement
    if (up.isDown) {
      this.sprite.setVelocityY(-this.speed);
      this.sprite.anims.play('walk-up', true);
    } else if (down.isDown) {
      this.sprite.setVelocityY(this.speed);
      this.sprite.anims.play('walk-down', true);
    }
    
    // Stop animation if not moving
    if (this.sprite.body!.velocity.x === 0 && this.sprite.body!.velocity.y === 0) {
      this.sprite.anims.stop();
    }
  }
}
```

---

## 6. Backend Integration

**src/api/BackendClient.ts**
```typescript
export interface SimulationConfig {
  victim_persona: string;
  scam_tactic: string;
  mode: 'fast' | 'demo';
  player_role: string;
}

export class BackendClient {
  private baseURL = 'http://localhost:8000';
  private ws: WebSocket | null = null;
  private messageHandlers: Map<string, Function> = new Map();

  async startSimulation(config: SimulationConfig): Promise<string> {
    const response = await fetch(`${this.baseURL}/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      throw new Error(`Failed to start simulation: ${response.statusText}`);
    }

    const data = await response.json();
    return data.simulation_id;
  }

  connectWebSocket(simulationId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const wsURL = this.baseURL.replace('http', 'ws');
      this.ws = new WebSocket(`${wsURL}/ws/simulation/${simulationId}`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.ws = null;
      };
    });
  }

  private handleMessage(data: any): void {
    const handler = this.messageHandlers.get(data.event_type);
    if (handler) {
      handler(data);
    }
  }

  on(eventType: string, handler: Function): void {
    this.messageHandlers.set(eventType, handler);
  }

  sendMessage(message: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'player_message',
        content: message
      }));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

---

## 7. Next Steps

1. **Create Assets**
   - Design player and NPC sprites (32x32 or 64x64)
   - Create tileset for Hong Kong urban environment
   - Design UI elements (HUD, dialogue boxes)

2. **Implement Battle Scene**
   - Create dialogue interface
   - Integrate trust system
   - Add AI agent responses

3. **Add Voice Support**
   - Implement Web Speech API
   - Add voice input/output handlers
   - Create voice UI controls

4. **Build Auto Mode**
   - Implement AI-controlled player
   - Create pathfinding system
   - Add statistics dashboard

5. **Testing & Polish**
   - Cross-browser testing
   - Performance optimization
   - User feedback integration

---

**Ready to start development!** 🚀
