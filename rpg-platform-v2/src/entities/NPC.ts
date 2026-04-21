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
  private indicatorFloatPhase = 0;

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
    const preferredSpriteKey = this.getSpriteKeyForScamType(this.scamId);
    const spriteKey = scene.textures.exists(preferredSpriteKey) ? preferredSpriteKey : 'player';
    this.sprite = scene.physics.add.sprite(x, y, spriteKey);
    this.sprite.setData('spriteKey', spriteKey);
    this.sprite.setImmovable(true);
    this.sprite.setDepth(5);
    
    // Set collision body
    this.sprite.setSize(32, 32);
    this.sprite.setOffset(8, 16);
    
    // Set idle frame directly to avoid runtime animation issues
    this.setIdleFrame('down');
    
    // Create interaction indicator (hidden by default)
    this.interactionIndicator = scene.add.container(x, y - 50);
    this.interactionIndicator.setDepth(20);
    
    // 使用騙案類型的顏色
    const bgColor = parseInt(this.scamType.color.replace('#', '0x'));
    const bg = scene.add.rectangle(0, 0, 110, 30, bgColor, 0.9);
    bg.setStrokeStyle(2, 0xffffff, 0.8);
    bg.setInteractive({ useHandCursor: true });
    bg.on('pointerdown', () => {
      // 觸發場景的 checkInteraction（透過自定義事件）
      scene.events.emit('npc-interact-click', this);
    });
    bg.on('pointerover', () => { bg.setAlpha(1); });
    bg.on('pointerout',  () => { bg.setAlpha(0.9); });
    
    // 顯示騙案類型圖標和提示
    const text = scene.add.text(0, 0, `${this.scamType.icon} [E]`, {
      fontSize: '14px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    text.setOrigin(0.5);
    
    this.interactionIndicator.add([bg, text]);
    this.interactionIndicator.setVisible(false);
    
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

  private setIdleFrame(direction: 'down' | 'left' | 'right' | 'up'): void {
    const idleFrames: Record<'down' | 'left' | 'right' | 'up', number> = {
      down: 1,
      left: 13,
      right: 25,
      up: 37
    };
    this.sprite.anims.stop();
    this.sprite.setFrame(idleFrames[direction]);
  }

  private playWalkAnimation(direction: 'down' | 'left' | 'right' | 'up'): void {
    const spriteKey = String(this.sprite.getData('spriteKey') || 'player');
    const animKey = `${spriteKey}-walk-${direction}`;
    if (!this.scene.anims.exists(animKey)) {
      return;
    }
    if (this.sprite.anims.currentAnim?.key !== animKey) {
      this.sprite.play(animKey);
    }
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
    this.playWalkAnimation(this.currentDirection);
    
    // Move in that direction
    const speed = 50;
    const distance = Phaser.Math.Between(30, 80);
    const duration = (distance / speed) * 1000;
    
    let targetX = this.sprite.x;
    let targetY = this.sprite.y;
    
    switch (this.currentDirection) {
      case 'down':
        targetY += distance;
        break;
      case 'up':
        targetY -= distance;
        break;
      case 'left':
        targetX -= distance;
        break;
      case 'right':
        targetX += distance;
        break;
    }
    
    // Animate movement
    this.scene.tweens.add({
      targets: this.sprite,
      x: targetX,
      y: targetY,
      duration: duration,
      ease: 'Linear',
      onComplete: () => {
        this.isWandering = false;
        this.setIdleFrame(this.currentDirection);
      }
    });
  }

  showInteractionIndicator(): void {
    this.interactionIndicator.setVisible(true);
  }

  hideInteractionIndicator(): void {
    this.interactionIndicator.setVisible(false);
  }

  update(): void {
    // Update interaction indicator position to follow NPC
    this.indicatorFloatPhase += 0.06;
    const indicatorOffsetY = 50 + Math.sin(this.indicatorFloatPhase) * 5;
    this.interactionIndicator.setPosition(this.sprite.x, this.sprite.y - indicatorOffsetY);
  }

  stopWandering(): void {
    if (this.wanderTimer) {
      this.wanderTimer.remove();
      this.wanderTimer = null;
    }
    this.isWandering = false;
    this.scene.tweens.killTweensOf(this.sprite);
    this.setIdleFrame(this.currentDirection);
  }

  destroy(): void {
    this.stopWandering();
    this.sprite.destroy();
    this.interactionIndicator.destroy();
  }
}
