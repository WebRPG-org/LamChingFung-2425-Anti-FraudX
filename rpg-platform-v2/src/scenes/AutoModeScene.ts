import Phaser from 'phaser';

export class AutoModeScene extends Phaser.Scene {
  private isRunning = false;
  private stats = {
    totalSimulations: 0,
    scammerWins: 0,
    expertWins: 0,
    averageDuration: 0
  };
  private statTexts: Map<string, Phaser.GameObjects.Text> = new Map();

  constructor() {
    super({ key: 'AutoModeScene' });
  }

  create(): void {
    // Modern gradient background
    this.createModernBackground();

    // Animated title
    this.createAnimatedTitle();

    // Stats display with modern cards
    this.createModernStatsDisplay();

    // Control buttons
    this.createModernControls();

    // Info panel
    this.createInfoPanel();

    // Decorative elements
    this.createDecorativeElements();
  }

  private createModernBackground(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Base gradient
    const bg = this.add.rectangle(0, 0, width, height, 0x0A0E27).setOrigin(0, 0);

    // Animated gradient overlay
    const graphics = this.add.graphics();
    graphics.fillGradientStyle(0xFF2E63, 0xFF2E63, 0x08D9D6, 0x08D9D6, 0.05, 0.05, 0.1, 0.1);
    graphics.fillRect(0, 0, width, height);

    // Pulsing circles
    const circle1 = this.add.circle(width * 0.2, height * 0.3, 200, 0xFF2E63, 0.1);
    const circle2 = this.add.circle(width * 0.8, height * 0.7, 250, 0x08D9D6, 0.1);

    this.tweens.add({
      targets: [circle1, circle2],
      scale: { from: 1, to: 1.3 },
      alpha: { from: 0.1, to: 0.05 },
      duration: 4000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
  }

  private createAnimatedTitle(): void {
    const width = this.cameras.main.width;

    const titleContainer = this.add.container(width / 2, 100);

    // Title background
    const titleBg = this.add.rectangle(0, 0, 600, 100, 0x16213E, 0.8);
    titleBg.setStrokeStyle(2, 0x08D9D6, 0.5);

    // Main title
    const title = this.add.text(0, -15, '🤖 自動訓練模式', {
      fontFamily: 'Orbitron, sans-serif',
      fontSize: '42px',
      color: '#08D9D6',
      fontStyle: 'bold',
      stroke: '#08D9D6',
      strokeThickness: 1
    });
    title.setOrigin(0.5);

    // Subtitle
    const subtitle = this.add.text(0, 25, 'AI 自動運行訓練模擬', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#B8C5D6',
      letterSpacing: 2
    });
    subtitle.setOrigin(0.5);

    titleContainer.add([titleBg, title, subtitle]);

    // Pulsing animation
    this.tweens.add({
      targets: title,
      scale: { from: 1, to: 1.02 },
      duration: 2000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });

    // Entrance animation
    titleContainer.setAlpha(0);
    titleContainer.setY(80);
    this.tweens.add({
      targets: titleContainer,
      alpha: 1,
      y: 100,
      duration: 600,
      ease: 'Back.easeOut'
    });
  }

  private createModernStatsDisplay(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const statsContainer = this.add.container(width / 2, height / 2 - 20);

    // Stats configuration
    const statBoxes = [
      { 
        key: 'total',
        label: '總模擬次數', 
        value: () => this.stats.totalSimulations, 
        color: 0x08D9D6,
        icon: '📊'
      },
      { 
        key: 'scammer',
        label: '騙徒勝利', 
        value: () => this.stats.scammerWins, 
        color: 0xFF2E63,
        icon: '🎭'
      },
      { 
        key: 'expert',
        label: '專家勝利', 
        value: () => this.stats.expertWins, 
        color: 0x6BCF7F,
        icon: '🛡️'
      },
      { 
        key: 'duration',
        label: '平均時長', 
        value: () => `${this.stats.averageDuration}s`, 
        color: 0xFFD93D,
        icon: '⏱️'
      }
    ];

    const boxWidth = 280;
    const boxHeight = 120;
    const spacing = 30;
    const cols = 2;

    statBoxes.forEach((stat, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = (col - 0.5) * (boxWidth + spacing);
      const y = row * (boxHeight + spacing);

      // Card container
      const card = this.add.container(x, y);

      // Card background with glass effect
      const box = this.add.rectangle(0, 0, boxWidth, boxHeight, 0x16213E, 0.8);
      box.setStrokeStyle(2, stat.color, 0.6);

      // Glow effect
      const glow = this.add.rectangle(0, 0, boxWidth + 4, boxHeight + 4, stat.color, 0);
      glow.setStrokeStyle(3, stat.color, 0.3);

      // Icon
      const icon = this.add.text(-boxWidth / 2 + 30, -20, stat.icon, {
        fontSize: '36px'
      });
      icon.setOrigin(0.5);

      // Value text
      const valueText = this.add.text(0, -10, '0', {
        fontFamily: 'Orbitron, sans-serif',
        fontSize: '38px',
        color: '#FFFFFF',
        fontStyle: 'bold'
      });
      valueText.setOrigin(0.5);
      this.statTexts.set(stat.key, valueText);

      // Label text
      const labelText = this.add.text(0, 30, stat.label, {
        fontFamily: 'Noto Sans TC, sans-serif',
        fontSize: '14px',
        color: '#B8C5D6'
      });
      labelText.setOrigin(0.5);

      card.add([glow, box, icon, valueText, labelText]);
      statsContainer.add(card);

      // Entrance animation
      card.setAlpha(0);
      card.setScale(0.8);
      this.tweens.add({
        targets: card,
        alpha: 1,
        scale: 1,
        duration: 500,
        delay: 300 + index * 100,
        ease: 'Back.easeOut'
      });

      // Hover effect
      box.setInteractive();
      box.on('pointerover', () => {
        this.tweens.add({
          targets: card,
          scale: 1.05,
          duration: 200,
          ease: 'Back.easeOut'
        });
        this.tweens.add({
          targets: glow,
          alpha: 0.3,
          duration: 200
        });
      });
      box.on('pointerout', () => {
        this.tweens.add({
          targets: card,
          scale: 1,
          duration: 200
        });
        this.tweens.add({
          targets: glow,
          alpha: 0,
          duration: 200
        });
      });
    });

    // Update stats periodically
    this.time.addEvent({
      delay: 500,
      callback: () => this.updateStatsDisplay(statBoxes),
      loop: true
    });
  }

  private updateStatsDisplay(statBoxes: any[]): void {
    statBoxes.forEach((stat) => {
      const valueText = this.statTexts.get(stat.key);
      if (valueText) {
        const newValue = String(stat.value());
        if (valueText.text !== newValue) {
          valueText.setText(newValue);
          
          // Pulse animation on update
          this.tweens.add({
            targets: valueText,
            scale: { from: 1.2, to: 1 },
            duration: 300,
            ease: 'Back.easeOut'
          });
        }
      }
    });
  }

  private createModernControls(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const controlsY = height - 120;
    const controlsContainer = this.add.container(width / 2, controlsY);

    // Start/Stop button - FIXED: Use centered origin
    const startButton = this.add.container(-140, 0);
    const startBg = this.add.rectangle(0, 0, 220, 60, 0x6BCF7F, 0.9);
    startBg.setOrigin(0.5);
    startBg.setStrokeStyle(2, 0x7FDF95, 0.8);
    const startText = this.add.text(0, 0, '▶️ 開始模擬', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '22px',
      color: '#0A0E27',
      fontStyle: 'bold'
    });
    startText.setOrigin(0.5);
    startButton.add([startBg, startText]);

    // FIXED: Make startBg interactive (simpler and more reliable)
    startBg.setInteractive({ useHandCursor: true });
    startBg.on('pointerdown', () => this.toggleAutoMode(startButton, startBg, startText));
    startBg.on('pointerover', () => {
      this.tweens.add({
        targets: startButton,
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
    });
    startBg.on('pointerout', () => {
      this.tweens.add({
        targets: startButton,
        scale: 1,
        duration: 200
      });
    });

    // Back button - FIXED: Use centered origin
    const backButton = this.add.container(140, 0);
    const backBg = this.add.rectangle(0, 0, 220, 60, 0xFF2E63, 0.9);
    backBg.setOrigin(0.5);
    backBg.setStrokeStyle(2, 0xFF6B9D, 0.8);
    const backText = this.add.text(0, 0, '🏠 返回主頁', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '22px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    backText.setOrigin(0.5);
    backButton.add([backBg, backText]);

    // FIXED: Make backBg interactive (simpler and more reliable)
    backBg.setInteractive({ useHandCursor: true });
    backBg.on('pointerdown', () => this.returnToMenu());
    backBg.on('pointerover', () => {
      this.tweens.add({
        targets: backButton,
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
    });
    backBg.on('pointerout', () => {
      this.tweens.add({
        targets: backButton,
        scale: 1,
        duration: 200
      });
    });

    controlsContainer.add([startButton, backButton]);

    // Entrance animation
    controlsContainer.setAlpha(0);
    controlsContainer.setY(height - 100);
    this.tweens.add({
      targets: controlsContainer,
      alpha: 1,
      y: controlsY,
      duration: 600,
      delay: 800,
      ease: 'Back.easeOut'
    });
  }

  private createInfoPanel(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const infoContainer = this.add.container(width / 2, height - 40);

    const infoBg = this.add.rectangle(0, 0, 600, 50, 0x16213E, 0.6);
    infoBg.setStrokeStyle(1, 0x08D9D6, 0.3);

    const info = this.add.text(0, 0,
      '💡 自動模式將持續運行模擬，AI 控制角色自動導航並與 NPC 互動',
      {
        fontFamily: 'Noto Sans TC, sans-serif',
        fontSize: '12px',
        color: '#B8C5D6',
        align: 'center'
      }
    );
    info.setOrigin(0.5);

    infoContainer.add([infoBg, info]);

    // Entrance animation
    infoContainer.setAlpha(0);
    this.tweens.add({
      targets: infoContainer,
      alpha: 1,
      duration: 600,
      delay: 1000
    });
  }

  private createDecorativeElements(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Corner decorations
    const corners = [
      { x: 30, y: 30, angle: 0 },
      { x: width - 30, y: 30, angle: 90 },
      { x: 30, y: height - 30, angle: -90 },
      { x: width - 30, y: height - 30, angle: 180 }
    ];

    corners.forEach((corner, index) => {
      const graphics = this.add.graphics();
      graphics.lineStyle(2, 0x08D9D6, 0.5);
      graphics.beginPath();
      graphics.moveTo(0, 0);
      graphics.lineTo(30, 0);
      graphics.moveTo(0, 0);
      graphics.lineTo(0, 30);
      graphics.strokePath();

      graphics.setPosition(corner.x, corner.y);
      graphics.setAngle(corner.angle);
      graphics.setAlpha(0);

      this.tweens.add({
        targets: graphics,
        alpha: 1,
        duration: 800,
        delay: 1200 + index * 100
      });
    });
  }

  private toggleAutoMode(
    button: Phaser.GameObjects.Container,
    bg: Phaser.GameObjects.Rectangle,
    text: Phaser.GameObjects.Text
  ): void {
    this.isRunning = !this.isRunning;

    if (this.isRunning) {
      text.setText('⏸️ 停止模擬');
      bg.setFillStyle(0xFF2E63, 0.9);
      bg.setStrokeStyle(2, 0xFF6B9D, 0.8);
      this.startAutoSimulation();
    } else {
      text.setText('▶️ 開始模擬');
      bg.setFillStyle(0x6BCF7F, 0.9);
      bg.setStrokeStyle(2, 0x7FDF95, 0.8);
    }

    // Button animation
    this.tweens.add({
      targets: button,
      scale: 0.95,
      duration: 100,
      yoyo: true
    });
  }

  private startAutoSimulation(): void {
    console.log('[AutoModeScene] Starting auto simulation...');

    // Simulate running simulations
    const simulationLoop = this.time.addEvent({
      delay: 2500,
      callback: () => {
        if (this.isRunning) {
          this.runOneSimulation();
        } else {
          simulationLoop.remove();
        }
      },
      loop: true
    });
  }

  private runOneSimulation(): void {
    this.stats.totalSimulations++;
    
    // Random outcome
    const isScammerWin = Math.random() > 0.5;
    if (isScammerWin) {
      this.stats.scammerWins++;
    } else {
      this.stats.expertWins++;
    }

    // Random duration
    this.stats.averageDuration = Math.floor(
      (this.stats.averageDuration * (this.stats.totalSimulations - 1) + 
       Math.random() * 60 + 30) / this.stats.totalSimulations
    );

    console.log('[AutoModeScene] Simulation completed:', this.stats);
  }

  private returnToMenu(): void {
    this.isRunning = false;
    
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
        this.scene.start('MainMenuScene');
      }
    });
  }
}
