import Phaser from 'phaser';

export class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene' });
  }

  preload(): void {
    // Create loading bar
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;
    
    const progressBar = this.add.graphics();
    const progressBox = this.add.graphics();
    progressBox.fillStyle(0x222222, 0.8);
    progressBox.fillRect(width / 2 - 160, height / 2 - 25, 320, 50);
    
    const loadingText = this.add.text(width / 2, height / 2 - 50, '載入專業素材中...', {
      fontSize: '20px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    loadingText.setOrigin(0.5, 0.5);
    
    const percentText = this.add.text(width / 2, height / 2, '0%', {
      fontSize: '18px',
      color: '#ffffff'
    });
    percentText.setOrigin(0.5, 0.5);
    
    const assetText = this.add.text(width / 2, height / 2 + 40, '', {
      fontSize: '12px',
      color: '#A0AEC0'
    });
    assetText.setOrigin(0.5, 0.5);
    
    this.load.on('progress', (value: number) => {
      progressBar.clear();
      progressBar.fillStyle(0x6C5CE7, 1);
      progressBar.fillRect(width / 2 - 150, height / 2 - 15, 300 * value, 30);
      percentText.setText(Math.floor(value * 100) + '%');
    });
    
    this.load.on('fileprogress', (file: Phaser.Loader.File) => {
      assetText.setText(`載入: ${file.key}`);
    });
    
    this.load.on('complete', () => {
      progressBar.destroy();
      progressBox.destroy();
      loadingText.destroy();
      percentText.destroy();
      assetText.destroy();
    });
    
    // Load professional RPG Maker MV assets
    this.loadProfessionalAssets();
  }

  private loadProfessionalAssets(): void {
    console.log('[BootScene] Loading professional RPG Maker MV assets...');
    
    // Load character spritesheets (48x48, 3 columns x 4 rows)
    this.load.spritesheet('player', 'assets/characters/Actor1.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    this.load.spritesheet('npc-elderly', 'assets/characters/People3.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    this.load.spritesheet('npc-student', 'assets/characters/People2.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    this.load.spritesheet('npc-average', 'assets/characters/People1.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    // Use People4 for overconfident type
    this.load.spritesheet('npc-overconfident', 'assets/characters/People4.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    this.load.spritesheet('npc-scammer', 'assets/characters/Evil.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    this.load.spritesheet('npc-expert', 'assets/characters/People4.png', {
      frameWidth: 48,
      frameHeight: 48
    });
    
    // Load tilesets
    this.load.image('tileset-outside', 'assets/tilesets/Outside_A2.png');
    this.load.image('tileset-outside-b', 'assets/tilesets/tileset-outside-b.png');
    
    // Load RPG Maker maps
    this.load.tilemapTiledJSON('forest-town', 'assets/maps/Forest_Town.json');
    this.load.tilemapTiledJSON('test-minimal', 'assets/maps/test-minimal.json');
    
    console.log('[BootScene] Essential assets loaded');
  }

  create(): void {
    console.log('[BootScene] Creating character animations...');
    this.createCharacterAnimations();
    
    console.log('[BootScene] Assets loaded, starting MainMenuScene');
    this.scene.start('MainMenuScene');
  }

  private createCharacterAnimations(): void {
    // RPG Maker MV Actor spritesheets: 12 columns x 8 rows (8 characters, each 3 cols x 4 rows)
    // For Actor1.png (576x384 = 12x8 tiles), we use only the first character (columns 0-2)
    // Each character layout:
    // Row 0: Down (frames 0-2)
    // Row 1: Left (frames 12-14) 
    // Row 2: Right (frames 24-26)
    // Row 3: Up (frames 36-38)
    
    // Player animations (using first character from Actor1.png)
    this.anims.create({
      key: 'player-walk-down',
      frames: this.anims.generateFrameNumbers('player', { frames: [0, 1, 2] }),
      frameRate: 8,
      repeat: -1
    });
    
    this.anims.create({
      key: 'player-walk-left',
      frames: this.anims.generateFrameNumbers('player', { frames: [12, 13, 14] }),
      frameRate: 8,
      repeat: -1
    });
    
    this.anims.create({
      key: 'player-walk-right',
      frames: this.anims.generateFrameNumbers('player', { frames: [24, 25, 26] }),
      frameRate: 8,
      repeat: -1
    });
    
    this.anims.create({
      key: 'player-walk-up',
      frames: this.anims.generateFrameNumbers('player', { frames: [36, 37, 38] }),
      frameRate: 8,
      repeat: -1
    });
    
    // Idle animations (middle frame of each direction)
    this.anims.create({
      key: 'player-idle-down',
      frames: [{ key: 'player', frame: 1 }],
      frameRate: 1
    });
    
    this.anims.create({
      key: 'player-idle-left',
      frames: [{ key: 'player', frame: 13 }],
      frameRate: 1
    });
    
    this.anims.create({
      key: 'player-idle-right',
      frames: [{ key: 'player', frame: 25 }],
      frameRate: 1
    });
    
    this.anims.create({
      key: 'player-idle-up',
      frames: [{ key: 'player', frame: 37 }],
      frameRate: 1
    });
    
    // NPC animations (People spritesheets also use 12x8 layout, same as Actor1)
    // Each spritesheet has 8 characters (3 cols each), we use the first character
    const npcCharacters = [
      { key: 'npc-elderly', spritesheet: 'npc-elderly' },
      { key: 'npc-student', spritesheet: 'npc-student' },
      { key: 'npc-average', spritesheet: 'npc-average' },
      { key: 'npc-overconfident', spritesheet: 'npc-overconfident' },
      { key: 'npc-scammer', spritesheet: 'npc-scammer' },
      { key: 'npc-expert', spritesheet: 'npc-expert' }
    ];
    
    npcCharacters.forEach(({ key, spritesheet }) => {
      // Walk animations (using first character: frames 0-2, 12-14, 24-26, 36-38)
      this.anims.create({
        key: `${key}-walk-down`,
        frames: this.anims.generateFrameNumbers(spritesheet, { frames: [0, 1, 2] }),
        frameRate: 8,
        repeat: -1
      });
      
      this.anims.create({
        key: `${key}-walk-left`,
        frames: this.anims.generateFrameNumbers(spritesheet, { frames: [12, 13, 14] }),
        frameRate: 8,
        repeat: -1
      });
      
      this.anims.create({
        key: `${key}-walk-right`,
        frames: this.anims.generateFrameNumbers(spritesheet, { frames: [24, 25, 26] }),
        frameRate: 8,
        repeat: -1
      });
      
      this.anims.create({
        key: `${key}-walk-up`,
        frames: this.anims.generateFrameNumbers(spritesheet, { frames: [36, 37, 38] }),
        frameRate: 8,
        repeat: -1
      });
      
      // Idle animations (middle frame of each direction)
      this.anims.create({
        key: `${key}-idle-down`,
        frames: [{ key: spritesheet, frame: 1 }],
        frameRate: 1
      });
      
      this.anims.create({
        key: `${key}-idle-left`,
        frames: [{ key: spritesheet, frame: 13 }],
        frameRate: 1
      });
      
      this.anims.create({
        key: `${key}-idle-right`,
        frames: [{ key: spritesheet, frame: 25 }],
        frameRate: 1
      });
      
      this.anims.create({
        key: `${key}-idle-up`,
        frames: [{ key: spritesheet, frame: 37 }],
        frameRate: 1
      });
    });
    
    console.log('[BootScene] Character animations created');
  }
}
