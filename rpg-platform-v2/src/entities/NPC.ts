import Phaser from 'phaser';
import { ScamType, getScamTypeById } from '../types/ScamTypes';

/**
 * NPC 類別 - 代表不同的騙案類型
 * 
 * 重要：NPC 不再使用人名，而是代表具體的詐騙類型
 * 例如：投資詐騙、釣魚短訊、愛情詐騙等
 */
export class NPC {
  public sprite: Phaser.Physics.Arcade.Sprite;
  public scamType: ScamType;  // 騙案類型資訊
  public scamId: string;       // 騙案類型 ID
  private scene: Phaser.Scene;
  private interactionIndicator: Phaser.GameObjects.Container;
  private currentDirection: 'down' | 'left' | 'right' | 'up' = 'down';
  private wanderTimer: Phaser.Time.TimerEvent | null = null;
  private isWandering = false;
  private wanderDuration = 0;
  private wanderElapsed = 0;

  /**
   * 創建 NPC
   * @param scene Phaser 場景
   * @param x X 座標
   * @param y Y 座標
   * @param scamId 騙案類型 ID（例如：'investment', 'phishing', 'romance'）
   */
  constructor(scene: Phaser.Scene, x: number, y: number, scamId: string) {
    this.scene = scene;
    this.scamId = scamId;
    
    // 獲取騙案類型資訊
    const scamType = getScamTypeById(scamId);
    if (!scamType) {
      console.error(`[NPC] 未知的騙案類型: ${scamId}`);
      // 使用預設類型
      this.scamType = getScamTypeById('investment')!;
      this.scamId = 'investment';
    } else {
      this.scamType = scamType;
    }
    
    // Create sprite based on scam type
    // 暫時使用舊的 sprite key，之後會替換為騙案類型專用的圖片
    const spriteKey = this.getSpriteKeyForScamType(scamId);
    this.sprite = scene.physics.add.sprite(x, y, spriteKey);
    this.sprite.setCollideWorldBounds(true);
    this.sprite.setDepth(5);
    
    // Set collision body
    this.sprite.setSize(32, 32);
    this.sprite.setOffset(8, 16);
    
    // Play idle animation
    this.sprite.play(`${spriteKey}-idle-down`);
    
    // Create interaction indicator (hidden by default)
    this.interactionIndicator = scene.add.container(x, y - 50);
    this.interactionIndicator.setDepth(20);
    
    // 使用騙案類型的顏色
    const bgColor = parseInt(this.scamType.color.replace('#', '0x'));
    const bg = scene.add.rectangle(0, 0, 100, 24, bgColor, 0.9);
    bg.setStrokeStyle(2, 0xffffff, 0.8);
    
    // 顯示騙案類型圖標和提示
    const text = scene.add.text(0, 0, `${this.scamType.icon} [E]`, {
      fontSize: '14px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    text.setOrigin(0.5);
    
    this.interactionIndicator.add([bg, text]);
    this.interactionIndicator.setVisible(false);
    
    // Add subtle floating animation to indicator
    scene.tweens.add({
      targets: this.interactionIndicator,
      y: y - 55,
      duration: 1000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
    
    // Start wandering behavior
    this.startWandering();
  }

  /**
   * 根據騙案類型獲取對應的 sprite key
   * 暫時映射到現有的 sprite，之後會替換為專用圖片
   */
  private getSpriteKeyForScamType(scamId: string): string {
    const spriteMapping: Record<string, string> = {
      'investment': 'npc-overconfident',    // 西裝男（投資詐騙）
      'phishing': 'npc-average',            // 一般人（釣魚短訊）
      'romance': 'npc-student',             // 年輕人（愛情詐騙）
      'impersonation': 'npc-expert',        // 制服人物（假冒官員）
      'shopping': 'npc-student',            // 年輕人（購物詐騙）
      'job': 'npc-average',                 // 一般人（求職詐騙）
      'prize': 'npc-elderly',               // 長者（中獎詐騙）
      'whatsapp': 'npc-average',            // 一般人（WhatsApp）
      'banking': 'npc-expert',              // 制服人物（銀行詐騙）
      'crypto': 'npc-overconfident',        // 西裝男（加密貨幣）
      'rental': 'npc-average',              // 一般人（租屋詐騙）
      'tech_support': 'npc-average',        // 一般人（技術支援）
      'charity': 'npc-elderly'              // 長者（慈善詐騙）
    };
    
    return spriteMapping[scamId] || 'npc-average';
  }

  /**
   * 獲取騙案類型的顯示名稱
   */
  public getDisplayName(): string {
    return `${this.scamType.icon} ${this.scamType.nameZh}`;
  }

  /**
   * 獲取騙案類型的簡短描述
   */
  public getDescription(): string {
    return this.scamType.description;
  }

  /**
   * 獲取危險等級
   */
  public getDangerLevel(): number {
    return this.scamType.dangerLevel;
  }

  private startWandering(): void {
    // Random wandering behavior
    this.wanderTimer = this.scene.time.addEvent({
      delay: Phaser.Math.Between(3000, 6000),
      callback: () => {
        if (!this.isWandering && Math.random() > 0.5) {
          this.wander();
        }
      },
      loop: true
    });
  }

  private wander(): void {
    this.isWandering = true;
    
    // Choose random direction
    const directions: Array<'down' | 'left' | 'right' | 'up'> = ['down', 'left', 'right', 'up'];
    this.currentDirection = Phaser.Utils.Array.GetRandom(directions);
    
    // Play walk animation
    const spriteKey = this.getSpriteKeyForScamType(this.scamId);
    this.sprite.play(`${spriteKey}-walk-${this.currentDirection}`);
    
    // 使用物理速度移動（而不是 tween）
    const speed = 50;
    this.wanderDuration = Phaser.Math.Between(1000, 2000); // 移動 1-2 秒
    this.wanderElapsed = 0;
    
    // 設置速度
    switch (this.currentDirection) {
      case 'down':
        this.sprite.setVelocity(0, speed);
        break;
      case 'up':
        this.sprite.setVelocity(0, -speed);
        break;
      case 'left':
        this.sprite.setVelocity(-speed, 0);
        break;
      case 'right':
        this.sprite.setVelocity(speed, 0);
        break;
    }
  }

  showInteractionIndicator(): void {
    this.interactionIndicator.setVisible(true);
  }

  hideInteractionIndicator(): void {
    this.interactionIndicator.setVisible(false);
  }

  update(): void {
    // 檢查 sprite 是否還存在
    if (!this.sprite || !this.sprite.body) {
      return;
    }
    
    // Update interaction indicator position to follow NPC
    if (this.interactionIndicator) {
      this.interactionIndicator.setPosition(this.sprite.x, this.sprite.y - 50);
    }
    
    // 處理遊蕩計時
    if (this.isWandering) {
      this.wanderElapsed += this.scene.game.loop.delta;
      
      if (this.wanderElapsed >= this.wanderDuration) {
        // 停止移動
        this.sprite.setVelocity(0, 0);
        this.isWandering = false;
        
        // 播放待機動畫
        const spriteKey = this.getSpriteKeyForScamType(this.scamId);
        this.sprite.play(`${spriteKey}-idle-${this.currentDirection}`);
      }
    }
  }

  stopWandering(): void {
    if (this.wanderTimer) {
      this.wanderTimer.remove();
      this.wanderTimer = null;
    }
    this.isWandering = false;
    
    // 檢查 sprite 是否還存在
    if (this.sprite && this.sprite.body) {
      this.sprite.setVelocity(0, 0);
      const spriteKey = this.getSpriteKeyForScamType(this.scamId);
      this.sprite.play(`${spriteKey}-idle-${this.currentDirection}`);
    }
  }

  destroy(): void {
    this.stopWandering();
    
    // 安全地銷毀 sprite
    if (this.sprite) {
      this.sprite.destroy();
    }
    
    // 安全地銷毀互動指示器
    if (this.interactionIndicator) {
      this.interactionIndicator.destroy();
    }
  }
}
