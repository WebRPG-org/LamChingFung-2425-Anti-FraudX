import Phaser from 'phaser';
import { RoleManager } from '../systems/RoleManager';

export class MainMenuScene extends Phaser.Scene {
  private roleManager: RoleManager;

  constructor() {
    super({ key: 'MainMenuScene' });
    this.roleManager = RoleManager.getInstance();
  }

  create(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Background
    this.add.rectangle(0, 0, width, height, 0x1A1F2E).setOrigin(0, 0);

    // Title
    const title = this.add.text(width / 2, 100, 'AI 防詐騙訓練系統', {
      fontSize: '48px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    const subtitle = this.add.text(width / 2, 160, '2D RPG 平台', {
      fontSize: '24px',
      color: '#A0AEC0'
    });
    subtitle.setOrigin(0.5);

    // Role selection
    const roleText = this.add.text(width / 2, 240, '選擇你的角色：', {
      fontSize: '20px',
      color: '#ffffff'
    });
    roleText.setOrigin(0.5);

    // Create role buttons
    const roles = this.roleManager.getAllRoles();
    const startY = 300;
    const spacing = 100;

    roles.forEach((role, index) => {
      const y = startY + index * spacing;
      
      // Button background
      const button = this.add.rectangle(width / 2, y, 400, 80, role.colorHex, 0.8);
      button.setInteractive({ useHandCursor: true });
      
      // Button text
      const buttonText = this.add.text(width / 2, y, `${role.icon} ${role.nameZh}`, {
        fontSize: '24px',
        color: '#ffffff',
        fontStyle: 'bold'
      });
      buttonText.setOrigin(0.5);
      
      const descText = this.add.text(width / 2, y + 25, role.descriptionZh, {
        fontSize: '14px',
        color: '#ffffff'
      });
      descText.setOrigin(0.5);

      // Hover effects
      button.on('pointerover', () => {
        button.setFillStyle(role.colorHex, 1);
        button.setScale(1.05);
      });

      button.on('pointerout', () => {
        button.setFillStyle(role.colorHex, 0.8);
        button.setScale(1);
      });

      button.on('pointerdown', () => {
        this.roleManager.switchRole(role.id);
        this.startGame();
      });
    });

    // Auto Mode button
    const autoButton = this.add.rectangle(width / 2, height - 100, 300, 60, 0x6C5CE7, 0.8);
    autoButton.setInteractive({ useHandCursor: true });
    
    const autoText = this.add.text(width / 2, height - 100, '🤖 自動模式', {
      fontSize: '20px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    autoText.setOrigin(0.5);

    autoButton.on('pointerover', () => {
      autoButton.setFillStyle(0x6C5CE7, 1);
      autoButton.setScale(1.05);
    });

    autoButton.on('pointerout', () => {
      autoButton.setFillStyle(0x6C5CE7, 0.8);
      autoButton.setScale(1);
    });

    autoButton.on('pointerdown', () => {
      this.scene.start('AutoModeScene');
    });

    // Instructions
    const instructions = this.add.text(width / 2, height - 40, '提示：選擇角色後進入遊戲世界', {
      fontSize: '14px',
      color: '#A0AEC0'
    });
    instructions.setOrigin(0.5);
  }

  private startGame(): void {
    console.log('[MainMenuScene] Starting game with role:', this.roleManager.getCurrentRole().nameZh);
    this.scene.start('WorldMapScene');
  }
}
