import Phaser from 'phaser';
export class Player {
    constructor(scene, x, y) {
        this.speed = 160;
        this.currentDirection = 'down';
        this.isMoving = false;
        this.collisionSystem = null;
        // State tracking for animation optimization
        this.lastIsMoving = false;
        this.lastDirection = 'down';
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
        // Setup input
        this.cursors = this.scene.input.keyboard.createCursorKeys();
        this.wasd = {
            up: this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.W),
            down: this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.S),
            left: this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.A),
            right: this.scene.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.D)
        };
    }
    /**
     * Set collision system for RPG Maker style collision detection
     */
    setCollisionSystem(collisionSystem) {
        this.collisionSystem = collisionSystem;
        console.log('[Player] Collision system enabled');
    }
    update() {
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
        }
        else if (right.isDown || d.isDown) {
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
        }
        else if (down.isDown || s.isDown) {
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
            }
            else {
                // Movement allowed - update direction
                this.currentDirection = intendedDirection;
            }
        }
        else if (this.isMoving) {
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
    }
    updateAnimation() {
        const animKey = this.isMoving
            ? `player-walk-${this.currentDirection}`
            : `player-idle-${this.currentDirection}`;
        // Only change animation if it's different from current
        if (this.sprite.anims.currentAnim?.key !== animKey) {
            this.sprite.play(animKey);
        }
    }
    getPosition() {
        return { x: this.sprite.x, y: this.sprite.y };
    }
    getDirection() {
        return this.currentDirection;
    }
    setPosition(x, y) {
        this.sprite.setPosition(x, y);
    }
    playIdleAnimation() {
        this.sprite.play(`player-idle-${this.currentDirection}`);
    }
}
