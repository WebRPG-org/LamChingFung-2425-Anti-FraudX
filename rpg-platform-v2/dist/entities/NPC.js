import Phaser from 'phaser';
export class NPC {
    constructor(scene, x, y, type) {
        this.currentDirection = 'down';
        this.wanderTimer = null;
        this.isWandering = false;
        this.scene = scene;
        this.type = type;
        this.name = this.getNameByType(type);
        // Create sprite based on type with professional RPG Maker MV asset
        const spriteKey = `npc-${type}`;
        this.sprite = scene.physics.add.sprite(x, y, spriteKey);
        this.sprite.setImmovable(true);
        this.sprite.setDepth(5);
        // Set collision body
        this.sprite.setSize(32, 32);
        this.sprite.setOffset(8, 16);
        // Play idle animation
        this.sprite.play(`${spriteKey}-idle-down`);
        // Create name label (always visible)
        this.nameLabel = scene.add.text(x, y - 40, this.name, {
            fontSize: '12px',
            color: '#ffffff',
            backgroundColor: '#000000',
            padding: { x: 4, y: 2 }
        });
        this.nameLabel.setOrigin(0.5);
        this.nameLabel.setDepth(20);
        // Create interaction indicator (hidden by default)
        this.interactionIndicator = scene.add.container(x, y - 50);
        this.interactionIndicator.setDepth(20);
        const bg = scene.add.rectangle(0, 0, 60, 20, 0x6C5CE7, 0.9);
        bg.setStrokeStyle(2, 0xffffff, 0.8);
        const text = scene.add.text(0, 0, '💬 [E]', {
            fontSize: '12px',
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
    getNameByType(type) {
        const names = {
            'elderly': '陳婆婆',
            'student': '王小明',
            'average': '張文軒',
            'overconfident': '李俊傑',
            'scammer': '神秘人',
            'expert': '黃警官'
        };
        return names[type];
    }
    startWandering() {
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
    wander() {
        this.isWandering = true;
        // Choose random direction
        const directions = ['down', 'left', 'right', 'up'];
        this.currentDirection = Phaser.Utils.Array.GetRandom(directions);
        // Play walk animation
        const spriteKey = `npc-${this.type}`;
        this.sprite.play(`${spriteKey}-walk-${this.currentDirection}`);
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
                // Play idle animation
                this.sprite.play(`${spriteKey}-idle-${this.currentDirection}`);
            }
        });
    }
    showInteractionIndicator() {
        this.interactionIndicator.setVisible(true);
    }
    hideInteractionIndicator() {
        this.interactionIndicator.setVisible(false);
    }
    update() {
        // Update UI elements position to follow NPC
        this.nameLabel.setPosition(this.sprite.x, this.sprite.y - 40);
        this.interactionIndicator.setPosition(this.sprite.x, this.sprite.y - 50);
    }
    stopWandering() {
        if (this.wanderTimer) {
            this.wanderTimer.remove();
            this.wanderTimer = null;
        }
        this.isWandering = false;
        this.scene.tweens.killTweensOf(this.sprite);
        const spriteKey = `npc-${this.type}`;
        this.sprite.play(`${spriteKey}-idle-${this.currentDirection}`);
    }
    destroy() {
        this.stopWandering();
        this.sprite.destroy();
        this.interactionIndicator.destroy();
        this.nameLabel.destroy();
    }
}
