import Phaser from 'phaser';
import { CollisionSystem } from '../systems/CollisionSystem';

export class Player {
  public sprite: Phaser.Physics.Arcade.Sprite;
  private scene: Phaser.Scene;
  private speed = 160;
  private cursors: Phaser.Types.Input.Keyboard.CursorKeys;
  private wasd: {
    up: Phaser.Input.Keyboard.Key;
    down: Phaser.Input.Keyboard.Key;
    left: Phaser.Input.Keyboard.Key;
    right: Phaser.Input.Keyboard.Key;
  };
  private currentDirection: 'down' | 'left' | 'right' | 'up' = 'down';
  private isMoving = false;
  private collisionSystem: CollisionSystem | null = null;
  private arrowIndicator: Phaser.GameObjects.Graphics;

  // State tracking for animation optimization
  private lastIsMoving = false;
  private lastDirection: 'down' | 'left' | 'right' | 'up' = 'down';

  constructor(scene: Phaser.Scene, x: number, y: number) {
    this.scene = scene;
    
    // Create sprite with professional RPG Maker MV asset
    this.sprite = this.scene.physics.add.sprite(x, y, 'player');
    this.sprite.setCollideWorldBounds(true);
    this.sprite.setDepth(10);
    
    // Set collision body size (slightly smaller than sprite for better feel)
    this.sprite.setSize(32, 32);
    this.sprite.setOffset(8, 16);
    
    // Play idle animation
    this.sprite.play('player-idle-down');
    
    // Create green arrow indicator above player
    this.arrowIndicator = this.scene.add.graphics();
    this.arrowIndicator.setDepth(15);
    this.drawArrow();
    
    // Add floating animation to arrow
    this.scene.tweens.add({
      targets: this.arrowIndicator,
      y: -5,
      duration: 800,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
    
    // Setup input
    this.cursors = this.scene.input.keyboard!.createCursorKeys();
    this.wasd = {
      up: this.scene.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.W),
      down: this.scene.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.S),
      left: this.scene.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.A),
      right: this.scene.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.D)
    };
  }

  /**
   * Draw green arrow indicator
   */
  private drawArrow(): void {
    this.arrowIndicator.clear();
    this.arrowIndicator.fillStyle(0x00ff00, 1);
    this.arrowIndicator.lineStyle(2, 0x00aa00, 1);
    
    // Draw arrow pointing down at player
    const arrowSize = 12;
    this.arrowIndicator.beginPath();
    this.arrowIndicator.moveTo(0, 0); // Top point
    this.arrowIndicator.lineTo(-arrowSize / 2, -arrowSize); // Left point
    this.arrowIndicator.lineTo(arrowSize / 2, -arrowSize); // Right point
    this.arrowIndicator.closePath();
    this.arrowIndicator.fillPath();
    this.arrowIndicator.strokePath();
  }

  /**
   * Set collision system for RPG Maker style collision detection
   */
  public setCollisionSystem(collisionSystem: CollisionSystem): void {
    this.collisionSystem = collisionSystem;
    console.log('[Player] Collision system enabled');
  }

  update(): void {
    const { left, right, up, down } = this.cursors;
    const { left: a, right: d, up: w, down: s } = this.wasd;
    
    // Reset velocity
    this.sprite.setVelocity(0);
    this.isMoving = false;
    
    // Determine movement direction and velocity
    let velocityX = 0;
    let velocityY = 0;
    let intendedDirection = this.currentDirection;
    
    // Horizontal movement (優先處理，避免斜向移動時方向混亂)
    if (left.isDown || a.isDown) {
      velocityX = -this.speed;
      intendedDirection = 'left';
      this.isMoving = true;
    } else if (right.isDown || d.isDown) {
      velocityX = this.speed;
      intendedDirection = 'right';
      this.isMoving = true;
    }
    
    // Vertical movement (只在沒有水平移動時更新方向)
    if (up.isDown || w.isDown) {
      velocityY = -this.speed;
      if (velocityX === 0) {
        intendedDirection = 'up';
      }
      this.isMoving = true;
    } else if (down.isDown || s.isDown) {
      velocityY = this.speed;
      if (velocityX === 0) {
        intendedDirection = 'down';
      }
      this.isMoving = true;
    }

    // Check collision before moving (RPG Maker style)
    if (this.isMoving && this.collisionSystem) {
      const currentX = this.sprite.x;
      const currentY = this.sprite.y;
      const futureX = currentX + velocityX * 0.016; // Approximate next frame position
      const futureY = currentY + velocityY * 0.016;

      // Check if movement is allowed
      const canMove = this.collisionSystem.canMoveTo(currentX, currentY, futureX, futureY);
      
      if (!canMove) {
        // Block movement - set velocity to zero
        velocityX = 0;
        velocityY = 0;
        this.isMoving = false;
        
        // Keep facing the intended direction even when blocked
        this.currentDirection = intendedDirection;
      } else {
        // Movement allowed - update direction
        this.currentDirection = intendedDirection;
      }
    } else if (this.isMoving) {
      // No collision system - allow free movement
      this.currentDirection = intendedDirection;
    }
    
    // Set velocity
    this.sprite.setVelocity(velocityX, velocityY);
    
    // Normalize diagonal movement
    if (velocityX !== 0 && velocityY !== 0) {
      this.sprite.setVelocity(velocityX * 0.707, velocityY * 0.707);
    }
    
    // 只在移動狀態改變或方向改變時更新動畫
    if (this.lastIsMoving !== this.isMoving || this.lastDirection !== this.currentDirection) {
      this.updateAnimation();
      this.lastIsMoving = this.isMoving;
      this.lastDirection = this.currentDirection;
    }
    
    // Update arrow indicator position to follow player
    this.arrowIndicator.setPosition(this.sprite.x, this.sprite.y - 35);
  }

  private updateAnimation(): void {
    const animKey = this.isMoving 
      ? `player-walk-${this.currentDirection}`
      : `player-idle-${this.currentDirection}`;
    
    // Only change animation if it's different from current
    if (this.sprite.anims.currentAnim?.key !== animKey) {
      this.sprite.play(animKey);
    }
  }

  getPosition(): { x: number; y: number } {
    return { x: this.sprite.x, y: this.sprite.y };
  }

  getDirection(): 'down' | 'left' | 'right' | 'up' {
    return this.currentDirection;
  }

  setPosition(x: number, y: number): void {
    this.sprite.setPosition(x, y);
  }

  playIdleAnimation(): void {
    this.sprite.play(`player-idle-${this.currentDirection}`);
  }
}
