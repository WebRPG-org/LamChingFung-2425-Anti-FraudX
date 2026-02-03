import Phaser from 'phaser';

export class AutoModeScene extends Phaser.Scene {
  private isRunning = false;
  private stats = {
    totalSimulations: 0,
    scammerWins: 0,
    expertWins: 0,
    averageDuration: 0
  };

  constructor() {
    super({ key: 'AutoModeScene' });
  }

  create(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // Background
    this.add.rectangle(0, 0, width, height, 0x1A1F2E).setOrigin(0, 0);

    // Title
    const title = this.add.text(width / 2, 80, '🤖 自動模式', {
      fontSize: '36px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    const subtitle = this.add.text(width / 2, 130, 'AI 自動運行訓練模擬', {
      fontSize: '18px',
      color: '#A0AEC0'
    });
    subtitle.setOrigin(0.5);

    // Stats display
    this.createStatsDisplay();

    // Control buttons
    this.createControls();

    // Info text
    const info = this.add.text(width / 2, height - 60,
      '自動模式將持續運行模擬，生成訓練數據\n' +
      'AI 控制的角色會自動導航並與 NPC 互動',
      {
        fontSize: '14px',
        color: '#A0AEC0',
        align: 'center'
      }
    );
    info.setOrigin(0.5);
  }

  private createStatsDisplay(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const statsContainer = this.add.container(width / 2, height / 2 - 50);

    // Stats grid
    const statBoxes = [
      { label: '總模擬次數', value: () => this.stats.totalSimulations, color: 0x6C5CE7 },
      { label: '騙徒勝利', value: () => this.stats.scammerWins, color: 0xFF6B6B },
      { label: '專家勝利', value: () => this.stats.expertWins, color: 0x00B894 },
      { label: '平均時長', value: () => `${this.stats.averageDuration}s`, color: 0x0984E3 }
    ];

    const boxWidth = 250;
    const boxHeight = 100;
    const spacing = 20;
    const cols = 2;

    statBoxes.forEach((stat, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      const x = (col - 0.5) * (boxWidth + spacing);
      const y = row * (boxHeight + spacing);

      const box = this.add.rectangle(x, y, boxWidth, boxHeight, stat.color, 0.2);
      box.setStrokeStyle(2, stat.color, 0.5);

      const valueText = this.add.text(x, y - 15, '0', {
        fontSize: '32px',
        color: '#ffffff',
        fontStyle: 'bold'
      });
      valueText.setOrigin(0.5);
      valueText.setName(`stat-${index}`);

      const labelText = this.add.text(x, y + 20, stat.label, {
        fontSize: '14px',
        color: '#A0AEC0'
      });
      labelText.setOrigin(0.5);

      statsContainer.add([box, valueText, labelText]);
    });

    // Update stats periodically
    this.time.addEvent({
      delay: 1000,
      callback: () => this.updateStatsDisplay(statsContainer, statBoxes),
      loop: true
    });
  }

  private updateStatsDisplay(container: Phaser.GameObjects.Container, statBoxes: any[]): void {
    statBoxes.forEach((stat, index) => {
      const valueText = container.getByName(`stat-${index}`) as Phaser.GameObjects.Text;
      if (valueText) {
        valueText.setText(String(stat.value()));
      }
    });
  }

  private createControls(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    const controlsY = height - 150;

    // Start/Stop button
    const startButton = this.add.text(width / 2 - 120, controlsY, '▶️ 開始', {
      fontSize: '20px',
      color: '#ffffff',
      backgroundColor: '#00B894',
      padding: { x: 30, y: 15 }
    });
    startButton.setOrigin(0.5);
    startButton.setInteractive({ useHandCursor: true });
    startButton.on('pointerdown', () => this.toggleAutoMode(startButton));
    startButton.on('pointerover', () => startButton.setScale(1.05));
    startButton.on('pointerout', () => startButton.setScale(1));

    // Back button
    const backButton = this.add.text(width / 2 + 120, controlsY, '🏠 返回', {
      fontSize: '20px',
      color: '#ffffff',
      backgroundColor: '#6C5CE7',
      padding: { x: 30, y: 15 }
    });
    backButton.setOrigin(0.5);
    backButton.setInteractive({ useHandCursor: true });
    backButton.on('pointerdown', () => this.returnToMenu());
    backButton.on('pointerover', () => backButton.setScale(1.05));
    backButton.on('pointerout', () => backButton.setScale(1));
  }

  private toggleAutoMode(button: Phaser.GameObjects.Text): void {
    this.isRunning = !this.isRunning;

    if (this.isRunning) {
      button.setText('⏸️ 停止');
      button.setBackgroundColor('#FF6B6B');
      this.startAutoSimulation();
    } else {
      button.setText('▶️ 開始');
      button.setBackgroundColor('#00B894');
    }
  }

  private startAutoSimulation(): void {
    console.log('[AutoModeScene] Starting auto simulation...');

    // Simulate running simulations
    const simulationLoop = this.time.addEvent({
      delay: 3000,
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
    this.scene.start('MainMenuScene');
  }
}
