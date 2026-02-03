import Phaser from 'phaser';
export class BootScene extends Phaser.Scene {
    constructor() {
        super({ key: 'BootScene' });
    }
    preload() {
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
        this.load.on('progress', (value) => {
            progressBar.clear();
            progressBar.fillStyle(0x6C5CE7, 1);
            progressBar.fillRect(width / 2 - 150, height / 2 - 15, 300 * value, 30);
            percentText.setText(Math.floor(value * 100) + '%');
        });
        this.load.on('fileprogress', (file) => {
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
    loadProfessionalAssets() {
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
        // Load RPG Maker maps
        this.load.tilemapTiledJSON('forest-town', 'assets/maps/Forest_Town.json');
        this.load.tilemapTiledJSON('shop-district', 'assets/maps/Shop_District.json');
        this.load.image('tileset-buildings', 'assets/tilesets/Outside_B.png');
        this.load.image('tileset-decorations', 'assets/tilesets/Outside_C.png');
        // Load battle backgrounds
        this.load.image('battle-ground', 'assets/battlebacks/Ruins2.png');
        this.load.image('battle-sky', 'assets/battlebacks/Town2.png');
        // Load system UI
        this.load.image('window-skin', 'assets/system/Window.png');
        this.load.image('icon-set', 'assets/system/IconSet.png');
        this.load.spritesheet('balloon', 'assets/system/Balloon.png', {
            frameWidth: 48,
            frameHeight: 48
        });
        // Load map backgrounds
        this.load.image('title-bg', 'assets/maps/Castle.png');
        // Load interactive objects
        this.load.spritesheet('chest', 'assets/characters/!Chest.png', {
            frameWidth: 48,
            frameHeight: 48
        });
        this.load.spritesheet('door', 'assets/characters/!Door1.png', {
            frameWidth: 48,
            frameHeight: 48
        });
    }
    create() {
        console.log('[BootScene] Creating character animations...');
        this.createCharacterAnimations();
        console.log('[BootScene] Assets loaded, starting MainMenuScene');
        this.scene.start('MainMenuScene');
    }
    createCharacterAnimations() {
        // Character sprite layout: 3 columns x 4 rows
        // Row 0: Down (frames 0-2)
        // Row 1: Left (frames 3-5)
        // Row 2: Right (frames 6-8)
        // Row 3: Up (frames 9-11)
        const characters = ['player', 'npc-elderly', 'npc-student', 'npc-average', 'npc-scammer', 'npc-expert'];
        characters.forEach(char => {
            // Walk down
            this.anims.create({
                key: `${char}-walk-down`,
                frames: this.anims.generateFrameNumbers(char, { start: 0, end: 2 }),
                frameRate: 8,
                repeat: -1
            });
            // Walk left
            this.anims.create({
                key: `${char}-walk-left`,
                frames: this.anims.generateFrameNumbers(char, { start: 3, end: 5 }),
                frameRate: 8,
                repeat: -1
            });
            // Walk right
            this.anims.create({
                key: `${char}-walk-right`,
                frames: this.anims.generateFrameNumbers(char, { start: 6, end: 8 }),
                frameRate: 8,
                repeat: -1
            });
            // Walk up
            this.anims.create({
                key: `${char}-walk-up`,
                frames: this.anims.generateFrameNumbers(char, { start: 9, end: 11 }),
                frameRate: 8,
                repeat: -1
            });
            // Idle animations (middle frame of each direction)
            this.anims.create({
                key: `${char}-idle-down`,
                frames: [{ key: char, frame: 1 }],
                frameRate: 1
            });
            this.anims.create({
                key: `${char}-idle-left`,
                frames: [{ key: char, frame: 4 }],
                frameRate: 1
            });
            this.anims.create({
                key: `${char}-idle-right`,
                frames: [{ key: char, frame: 7 }],
                frameRate: 1
            });
            this.anims.create({
                key: `${char}-idle-up`,
                frames: [{ key: char, frame: 10 }],
                frameRate: 1
            });
        });
        // Chest animation
        this.anims.create({
            key: 'chest-closed',
            frames: [{ key: 'chest', frame: 0 }],
            frameRate: 1
        });
        this.anims.create({
            key: 'chest-open',
            frames: [{ key: 'chest', frame: 1 }],
            frameRate: 1
        });
        console.log('[BootScene] Character animations created');
    }
}
