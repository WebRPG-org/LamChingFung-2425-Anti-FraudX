import Phaser from 'phaser';
import { RoleManager } from '../systems/RoleManager';
import { localization, AppLanguage } from '../systems/LocalizationManager';

export class MainMenuScene extends Phaser.Scene {
  private roleManager: RoleManager;
  private particles!: Phaser.GameObjects.Particles.ParticleEmitter;
  private languageButtonBg?: Phaser.GameObjects.Rectangle;
  private languageButtonText?: Phaser.GameObjects.Text;
  private languagePanel?: Phaser.GameObjects.Container;

  constructor() {
    super({ key: 'MainMenuScene' });
    this.roleManager = RoleManager.getInstance();
  }

  create(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    this.roleManager.applyLocalization();

    // Animated gradient background
    this.createAnimatedBackground();

    // Floating particles effect
    this.createParticleEffect();

    // Main title with glow effect
    this.createTitle();

    this.createLanguageSwitcher();

    // Role selection cards with modern design
    this.createRoleCards();

    // Bottom navigation
    this.createBottomNav();

    // Decorative elements
    this.createDecorativeElements();
  }

  private createAnimatedBackground(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Base gradient
    const bg = this.add.rectangle(0, 0, width, height, 0x0A0E27).setOrigin(0, 0);

    // Animated gradient overlay
    const graphics = this.add.graphics();
    graphics.fillGradientStyle(0xFF2E63, 0xFF2E63, 0x08D9D6, 0x08D9D6, 0.05, 0.05, 0.1, 0.1);
    graphics.fillRect(0, 0, width, height);

    // Pulsing glow circles
    const circle1 = this.add.circle(width * 0.2, height * 0.3, 200, 0xFF2E63, 0.1);
    const circle2 = this.add.circle(width * 0.8, height * 0.7, 250, 0x08D9D6, 0.1);

    this.tweens.add({
      targets: circle1,
      scale: { from: 1, to: 1.3 },
      alpha: { from: 0.1, to: 0.05 },
      duration: 4000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });

    this.tweens.add({
      targets: circle2,
      scale: { from: 1, to: 1.4 },
      alpha: { from: 0.1, to: 0.05 },
      duration: 5000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
  }

  private createParticleEffect(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Create simple particle graphics
    const particleGraphics = this.add.graphics();
    particleGraphics.fillStyle(0x08D9D6, 1);
    particleGraphics.fillCircle(2, 2, 2);
    particleGraphics.generateTexture('particle', 4, 4);
    particleGraphics.destroy();

    this.particles = this.add.particles(0, 0, 'particle', {
      x: { min: 0, max: width },
      y: { min: -50, max: height + 50 },
      lifespan: 8000,
      speedY: { min: 10, max: 30 },
      speedX: { min: -10, max: 10 },
      scale: { start: 0.5, end: 0 },
      alpha: { start: 0.6, end: 0 },
      blendMode: 'ADD',
      frequency: 200,
      quantity: 1
    });
    this.particles.setDepth(1);
  }

  private createTitle(): void {
    const width = this.cameras.main.width;

    // Main title with cyberpunk style
    const titleContainer = this.add.container(width / 2, 120);

    // Glowing background
    const titleBg = this.add.rectangle(0, 0, 700, 120, 0x000000, 0.3);
    titleBg.setStrokeStyle(2, 0x08D9D6, 0.5);

    // Main title
    const title = this.add.text(0, -20, localization.t('title'), {
      fontFamily: 'Orbitron, sans-serif',
      fontSize: '52px',
      color: '#FFFFFF',
      fontStyle: 'bold',
      stroke: '#08D9D6',
      strokeThickness: 2
    });
    title.setOrigin(0.5);

    // Subtitle with gradient effect
    const subtitle = this.add.text(0, 30, localization.t('subtitle'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '24px',
      color: '#B8C5D6',
      letterSpacing: 4
    });
    subtitle.setOrigin(0.5);

    titleContainer.add([titleBg, title, subtitle]);

    // Pulsing glow animation
    this.tweens.add({
      targets: title,
      scale: { from: 1, to: 1.02 },
      duration: 2000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });

    // Slide in animation
    titleContainer.setAlpha(0);
    titleContainer.setY(80);
    this.tweens.add({
      targets: titleContainer,
      alpha: 1,
      y: 120,
      duration: 800,
      ease: 'Back.easeOut'
    });
  }

  private createRoleCards(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Section title
    const sectionTitle = this.add.text(width / 2, 220, localization.t('chooseRole'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '28px',
      color: '#FFD93D',
      fontStyle: 'bold',
      letterSpacing: 2
    });
    sectionTitle.setOrigin(0.5);
    sectionTitle.setAlpha(0);
    this.tweens.add({
      targets: sectionTitle,
      alpha: 1,
      duration: 600,
      delay: 300
    });

    const roles = this.roleManager.getAllRoles();
    const cardWidth = 380;
    const cardHeight = 100;
    const startY = 290;
    const spacing = 120;

    roles.forEach((role, index) => {
      const y = startY + index * spacing;
      const delay = 400 + index * 150;

      this.createRoleCard(width / 2, y, cardWidth, cardHeight, role, delay);
    });
  }

  private createRoleCard(
    x: number,
    y: number,
    width: number,
    height: number,
    role: any,
    delay: number
  ): void {
    const container = this.add.container(x, y);

    // Card background with gradient
    const cardBg = this.add.rectangle(0, 0, width, height, 0x16213E, 0.8);
    cardBg.setStrokeStyle(2, role.colorHex, 0.6);

    // Glow effect
    const glow = this.add.rectangle(0, 0, width + 4, height + 4, role.colorHex, 0);
    glow.setStrokeStyle(3, role.colorHex, 0.3);

    // Role icon (larger)
    const icon = this.add.text(-width / 2 + 50, 0, role.icon, {
      fontSize: '48px'
    });
    icon.setOrigin(0.5);

    // Role name
    const nameText = this.add.text(-width / 2 + 120, -15, role.nameZh, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '26px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    nameText.setOrigin(0, 0.5);

    // Role description
    const descText = this.add.text(-width / 2 + 120, 15, role.descriptionZh, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '14px',
      color: '#B8C5D6'
    });
    descText.setOrigin(0, 0.5);

    // Arrow indicator
    const arrow = this.add.text(width / 2 - 30, 0, '→', {
      fontSize: '32px',
      color: role.color
    });
    arrow.setOrigin(0.5);
    arrow.setAlpha(0);

    container.add([glow, cardBg, icon, nameText, descText, arrow]);
    container.setDepth(10);

    // FIXED: Make cardBg interactive (simpler and more reliable)
    cardBg.setInteractive({ useHandCursor: true });

    // Hover effects
    cardBg.on('pointerover', () => {
      this.tweens.add({
        targets: container,
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
      this.tweens.add({
        targets: glow,
        alpha: 0.3,
        duration: 200
      });
      this.tweens.add({
        targets: arrow,
        alpha: 1,
        x: width / 2 - 25,
        duration: 300,
        ease: 'Back.easeOut'
      });
      cardBg.setStrokeStyle(3, role.colorHex, 1);
    });

    cardBg.on('pointerout', () => {
      this.tweens.add({
        targets: container,
        scale: 1,
        duration: 200
      });
      this.tweens.add({
        targets: glow,
        alpha: 0,
        duration: 200
      });
      this.tweens.add({
        targets: arrow,
        alpha: 0,
        x: width / 2 - 30,
        duration: 200
      });
      cardBg.setStrokeStyle(2, role.colorHex, 0.6);
    });

    cardBg.on('pointerdown', () => {
      // Click animation
      this.tweens.add({
        targets: container,
        scale: 0.95,
        duration: 100,
        yoyo: true,
        onComplete: () => {
          this.roleManager.switchRole(role.id);
          this.startGameWithTransition();
        }
      });
    });

    // Entrance animation
    container.setAlpha(0);
    container.setX(x - 50);
    this.tweens.add({
      targets: container,
      alpha: 1,
      x: x,
      duration: 500,
      delay: delay,
      ease: 'Power2'
    });
  }

  private createBottomNav(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Auto Mode button with modern design
    const autoContainer = this.add.container(width / 2 - 160, height - 80);

    const autoBg = this.add.rectangle(0, 0, 280, 60, 0xFF2E63, 0.9);
    autoBg.setStrokeStyle(2, 0xFF6B9D, 0.8);

    const autoText = this.add.text(0, 0, localization.t('autoMode'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '22px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    autoText.setOrigin(0.5);

    autoContainer.add([autoBg, autoText]);
    autoContainer.setDepth(10);

    // FIXED: Make autoBg interactive (simpler and more reliable)
    autoBg.setInteractive({ useHandCursor: true });

    autoBg.on('pointerover', () => {
      this.tweens.add({
        targets: autoContainer,
        scale: 1.08,
        duration: 200,
        ease: 'Back.easeOut'
      });
      autoBg.setFillStyle(0xFF2E63, 1);
    });

    autoBg.on('pointerout', () => {
      this.tweens.add({
        targets: autoContainer,
        scale: 1,
        duration: 200
      });
      autoBg.setFillStyle(0xFF2E63, 0.9);
    });

    autoBg.on('pointerdown', () => {
      this.tweens.add({
        targets: autoContainer,
        scale: 0.95,
        duration: 100,
        yoyo: true,
        onComplete: () => {
          this.scene.start('AutoModeScene');
        }
      });
    });

    // Entrance animation
    autoContainer.setAlpha(0);
    autoContainer.setY(height - 60);
    this.tweens.add({
      targets: autoContainer,
      alpha: 1,
      y: height - 80,
      duration: 600,
      delay: 1000,
      ease: 'Back.easeOut'
    });

    // Exit Game button - 返回主頁
    const exitContainer = this.add.container(width / 2 + 160, height - 80);

    const exitBg = this.add.rectangle(0, 0, 280, 60, 0x08D9D6, 0.9);
    exitBg.setStrokeStyle(2, 0x0BC9BF, 0.8);

    const exitText = this.add.text(0, 0, localization.t('backHome'), {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '22px',
      color: '#0A0E27',
      fontStyle: 'bold'
    });
    exitText.setOrigin(0.5);

    exitContainer.add([exitBg, exitText]);
    exitContainer.setDepth(10);

    // Make exitBg interactive
    exitBg.setInteractive({ useHandCursor: true });

    exitBg.on('pointerover', () => {
      this.tweens.add({
        targets: exitContainer,
        scale: 1.08,
        duration: 200,
        ease: 'Back.easeOut'
      });
      exitBg.setFillStyle(0x08D9D6, 1);
    });

    exitBg.on('pointerout', () => {
      this.tweens.add({
        targets: exitContainer,
        scale: 1,
        duration: 200
      });
      exitBg.setFillStyle(0x08D9D6, 0.9);
    });

    exitBg.on('pointerdown', () => {
      this.tweens.add({
        targets: exitContainer,
        scale: 0.95,
        duration: 100,
        yoyo: true,
        onComplete: () => {
          // 返回到主頁
          window.location.href = 'https://anti-fraudx-backend-5gznvtwxga-uc.a.run.app';
        }
      });
    });

    // Entrance animation
    exitContainer.setAlpha(0);
    exitContainer.setY(height - 60);
    this.tweens.add({
      targets: exitContainer,
      alpha: 1,
      y: height - 80,
      duration: 600,
      delay: 1100,
      ease: 'Back.easeOut'
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

  private createLanguageSwitcher(): void {
    const width = this.cameras.main.width;
    const x = width - 100;
    const y = 36;

    const bg = this.add.rectangle(x, y, 160, 46, 0x16213E, 0.9);
    bg.setStrokeStyle(2, 0x08D9D6, 0.7);
    bg.setInteractive({ useHandCursor: true });

    const text = this.add.text(x, y, `🌐 ${this.getCurrentLanguageLabel()}`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    }).setOrigin(0.5);

    bg.setDepth(50);
    text.setDepth(51);

    bg.on('pointerdown', () => this.toggleLanguagePanel());

    this.languageButtonBg = bg;
    this.languageButtonText = text;
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
    const startY = 72;
    const panel = this.add.container(width - 100, startY);
    panel.setDepth(80);

    const options = localization.getLanguageOptions();
    const panelBg = this.add.rectangle(0, 0, 170, options.length * 40 + 10, 0x0A0E27, 0.95);
    panelBg.setStrokeStyle(2, 0x08D9D6, 0.65);
    panelBg.setOrigin(0.5, 0);
    panel.add(panelBg);

    options.forEach((opt, index) => {
      const y = 20 + index * 38;
      const row = this.add.rectangle(0, y, 150, 32, 0x16213E, localization.getLanguage() === opt.code ? 1 : 0.75);
      row.setStrokeStyle(1, 0x08D9D6, 0.45);
      row.setInteractive({ useHandCursor: true });
      const label = this.add.text(0, y, opt.label, {
        fontFamily: 'Rajdhani, sans-serif',
        fontSize: '17px',
        color: '#FFFFFF',
        fontStyle: 'bold'
      }).setOrigin(0.5);

      row.on('pointerdown', () => this.applyLanguage(opt.code));
      panel.add([row, label]);
    });

    this.languagePanel = panel;
  }

  private applyLanguage(language: AppLanguage): void {
    localization.setLanguage(language);
    this.roleManager.applyLocalization();
    this.scene.restart();
  }

  private startGameWithTransition(): void {
    console.log('[MainMenuScene] Starting game with role:', this.roleManager.getCurrentRole().nameZh);

    // Fade out transition
    const overlay = this.add.rectangle(
      this.cameras.main.width / 2,
      this.cameras.main.height / 2,
      this.cameras.main.width,
      this.cameras.main.height,
      0x0A0E27,
      0
    );
    overlay.setDepth(100);

    this.tweens.add({
      targets: overlay,
      alpha: 1,
      duration: 500,
      onComplete: () => {
        console.log('[MainMenuScene] Transition complete, starting WorldMapScene...');
        // 停止當前場景並啟動遊戲場景
        this.scene.stop('MainMenuScene');
        this.scene.start('WorldMapScene');
      }
    });
  }

  /**
   * 場景關閉時清理資源
   */
  shutdown(): void {
    console.log('[MainMenuScene] Shutting down scene, cleaning up resources...');
    
    // 停止粒子效果
    if (this.particles) {
      this.particles.stop();
    }
    
    // 移除所有事件監聽
    this.input.removeAllListeners();
    
    console.log('[MainMenuScene] Cleanup complete');
  }
}
