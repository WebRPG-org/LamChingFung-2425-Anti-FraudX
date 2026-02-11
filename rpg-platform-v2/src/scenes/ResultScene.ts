/**
 * 結果場景 - 顯示對話分析報告
 * 
 * 展示 RecorderAgent 生成的詳細評分和分析
 */

import Phaser from 'phaser';
import { ScamType } from '../types/ScamTypes';
import { TrustData } from '../systems/TrustSystem';

interface ResultSceneData {
  outcome: 'scammer_win' | 'expert_win' | 'ongoing';
  analysis: {
    success: boolean;
    session_id: string;
    analysis: {
      scammer_score: number;
      expert_score: number;
      outcome: string;
      key_moments?: Array<{
        round: number;
        description: string;
        impact: string;
      }>;
      recommendations?: string[];
    };
    conversation_count: number;
  };
  scamType: ScamType;
  trustData: TrustData;
  roundCount: number;
}

export class ResultScene extends Phaser.Scene {
  private data!: ResultSceneData;

  constructor() {
    super({ key: 'ResultScene' });
  }

  init(data: ResultSceneData): void {
    this.data = data;
    console.log('[ResultScene] 顯示結果:', data);
  }

  create(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // 創建背景
    this.createBackground();

    // 創建主容器
    const mainContainer = this.add.container(width / 2, height / 2);

    // 結果面板
    const panel = this.createResultPanel();
    mainContainer.add(panel);

    // 入場動畫
    mainContainer.setAlpha(0);
    mainContainer.setScale(0.9);
    this.tweens.add({
      targets: mainContainer,
      alpha: 1,
      scale: 1,
      duration: 600,
      ease: 'Back.easeOut'
    });
  }

  private createBackground(): void {
    const width = this.cameras.main.width;
    const height = this.cameras.main.height;

    // 根據結果選擇背景顏色
    let bgColor1, bgColor2;
    if (this.data.outcome === 'expert_win') {
      bgColor1 = 0x08D9D6;  // 青色（成功）
      bgColor2 = 0x0A0E27;
    } else if (this.data.outcome === 'scammer_win') {
      bgColor1 = 0xFF2E63;  // 紅色（失敗）
      bgColor2 = 0x0A0E27;
    } else {
      bgColor1 = 0xFFD700;  // 金色（平局）
      bgColor2 = 0x0A0E27;
    }

    // 基礎背景
    const bg = this.add.rectangle(0, 0, width, height, 0x0A0E27).setOrigin(0, 0);

    // 漸變覆蓋
    const graphics = this.add.graphics();
    graphics.fillGradientStyle(bgColor1, bgColor1, bgColor2, bgColor2, 0.1, 0.1, 0.05, 0.05);
    graphics.fillRect(0, 0, width, height);

    // 裝飾圓圈
    const circle1 = this.add.circle(width * 0.2, height * 0.3, 200, bgColor1, 0.05);
    const circle2 = this.add.circle(width * 0.8, height * 0.7, 250, bgColor1, 0.05);

    this.tweens.add({
      targets: [circle1, circle2],
      scale: { from: 1, to: 1.3 },
      alpha: { from: 0.05, to: 0.02 },
      duration: 3000,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
  }

  private createResultPanel(): Phaser.GameObjects.Container {
    const panel = this.add.container(0, 0);

    // 面板背景
    const panelBg = this.add.rectangle(0, 0, 900, 650, 0x16213E, 0.95);
    panelBg.setStrokeStyle(3, this.getOutcomeColor(), 0.8);
    panel.add(panelBg);

    // 標題
    const title = this.createTitle();
    title.setPosition(0, -280);
    panel.add(title);

    // 騙案類型資訊
    const scamInfo = this.createScamInfo();
    scamInfo.setPosition(0, -220);
    panel.add(scamInfo);

    // 評分區域
    const scores = this.createScores();
    scores.setPosition(0, -120);
    panel.add(scores);

    // 信任度數據
    const trustInfo = this.createTrustInfo();
    trustInfo.setPosition(0, 20);
    panel.add(trustInfo);

    // 建議區域
    const recommendations = this.createRecommendations();
    recommendations.setPosition(0, 150);
    panel.add(recommendations);

    // 按鈕
    const buttons = this.createButtons();
    buttons.setPosition(0, 280);
    panel.add(buttons);

    return panel;
  }

  private createTitle(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    let titleText, titleIcon, titleColor;
    if (this.data.outcome === 'expert_win') {
      titleIcon = '✅';
      titleText = '成功識破騙局！';
      titleColor = '#08D9D6';
    } else if (this.data.outcome === 'scammer_win') {
      titleIcon = '💀';
      titleText = '不幸被騙了...';
      titleColor = '#FF2E63';
    } else {
      titleIcon = '⏸️';
      titleText = '對話結束';
      titleColor = '#FFD700';
    }

    const title = this.add.text(0, 0, `${titleIcon} ${titleText}`, {
      fontFamily: 'Orbitron, sans-serif',
      fontSize: '36px',
      color: titleColor,
      fontStyle: 'bold',
      stroke: titleColor,
      strokeThickness: 2
    });
    title.setOrigin(0.5);

    container.add(title);
    return container;
  }

  private createScamInfo(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    const scamText = this.add.text(0, 0, 
      `${this.data.scamType.icon} ${this.data.scamType.nameZh}`, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '20px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    scamText.setOrigin(0.5);

    const dangerText = this.add.text(0, 30, 
      `危險等級: ${'⭐'.repeat(this.data.scamType.dangerLevel)}`, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#FFD700'
    });
    dangerText.setOrigin(0.5);

    container.add([scamText, dangerText]);
    return container;
  }

  private createScores(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    // 背景
    const bg = this.add.rectangle(0, 0, 850, 100, 0x0A0E27, 0.5);
    bg.setStrokeStyle(2, 0x08D9D6, 0.3);
    container.add(bg);

    const analysis = this.data.analysis.analysis;

    // 騙徒評分
    const scammerScore = this.add.text(-300, -20, '🎭 騙徒表現', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '18px',
      color: '#FF2E63',
      fontStyle: 'bold'
    });
    scammerScore.setOrigin(0, 0.5);

    const scammerValue = this.add.text(-300, 15, 
      `${analysis.scammer_score || 0}/100`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '32px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    scammerValue.setOrigin(0, 0.5);

    // 專家評分
    const expertScore = this.add.text(100, -20, '🛡️ 專家表現', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '18px',
      color: '#08D9D6',
      fontStyle: 'bold'
    });
    expertScore.setOrigin(0, 0.5);

    const expertValue = this.add.text(100, 15, 
      `${analysis.expert_score || 0}/100`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '32px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    expertValue.setOrigin(0, 0.5);

    container.add([scammerScore, scammerValue, expertScore, expertValue]);
    return container;
  }

  private createTrustInfo(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    // 背景
    const bg = this.add.rectangle(0, 0, 850, 100, 0x0A0E27, 0.5);
    bg.setStrokeStyle(2, 0x08D9D6, 0.3);
    container.add(bg);

    const trustData = this.data.trustData;

    // 標題
    const title = this.add.text(0, -35, '📊 最終信任度數據', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#08D9D6',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    // 三個數據
    const scammerTrust = this.add.text(-250, 10, 
      `騙徒: ${Math.round(trustData.trustInScammer)}%`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#FF2E63'
    });
    scammerTrust.setOrigin(0.5);

    const expertTrust = this.add.text(0, 10, 
      `專家: ${Math.round(trustData.trustInExpert)}%`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#08D9D6'
    });
    expertTrust.setOrigin(0.5);

    const alertness = this.add.text(250, 10, 
      `警覺: ${Math.round(trustData.alertness)}%`, {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#FFD700'
    });
    alertness.setOrigin(0.5);

    container.add([title, scammerTrust, expertTrust, alertness]);
    return container;
  }

  private createRecommendations(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    // 背景
    const bg = this.add.rectangle(0, 0, 850, 100, 0x0A0E27, 0.5);
    bg.setStrokeStyle(2, 0x08D9D6, 0.3);
    container.add(bg);

    // 標題
    const title = this.add.text(0, -35, '💡 學習要點', {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#FFD700',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    // 建議文字
    let recommendationText = '';
    if (this.data.outcome === 'expert_win') {
      recommendationText = '✅ 你成功識破了騙局！保持警覺，繼續學習防詐技巧。';
    } else if (this.data.outcome === 'scammer_win') {
      recommendationText = '⚠️ 這次被騙了，記住騙徒的手法，下次要更加小心！';
    } else {
      recommendationText = '📚 繼續學習不同的詐騙手法，提高防範意識。';
    }

    const recommendation = this.add.text(0, 10, recommendationText, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '14px',
      color: '#FFFFFF',
      wordWrap: { width: 800 },
      align: 'center'
    });
    recommendation.setOrigin(0.5);

    container.add([title, recommendation]);
    return container;
  }

  private createButtons(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    // 返回地圖按鈕
    const returnButton = this.createButton(-150, 0, '🏠 返回地圖', 0x08D9D6, () => {
      this.returnToWorld();
    });

    // 再試一次按鈕
    const retryButton = this.createButton(150, 0, '🔄 再試一次', 0xFF2E63, () => {
      this.retryBattle();
    });

    container.add([returnButton, retryButton]);
    return container;
  }

  private createButton(
    x: number, 
    y: number, 
    text: string, 
    color: number, 
    callback: () => void
  ): Phaser.GameObjects.Container {
    const button = this.add.container(x, y);

    const bg = this.add.rectangle(0, 0, 250, 50, color, 0.9);
    bg.setStrokeStyle(2, color, 1);

    const buttonText = this.add.text(0, 0, text, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '18px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    buttonText.setOrigin(0.5);

    button.add([bg, buttonText]);

    // 互動
    bg.setInteractive({ useHandCursor: true });
    bg.on('pointerover', () => {
      this.tweens.add({
        targets: button,
        scale: 1.05,
        duration: 200,
        ease: 'Back.easeOut'
      });
    });
    bg.on('pointerout', () => {
      this.tweens.add({
        targets: button,
        scale: 1,
        duration: 200
      });
    });
    bg.on('pointerdown', callback);

    return button;
  }

  private getOutcomeColor(): number {
    if (this.data.outcome === 'expert_win') {
      return 0x08D9D6;
    } else if (this.data.outcome === 'scammer_win') {
      return 0xFF2E63;
    } else {
      return 0xFFD700;
    }
  }

  private returnToWorld(): void {
    // 淡出過渡
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
        this.scene.start('WorldMapScene');
      }
    });
  }

  private retryBattle(): void {
    // 重新開始相同的騙案對話
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
        this.scene.start('BattleScene', {
          scamType: this.data.scamType.id,
          scamTypeInfo: this.data.scamType,
          playerRole: { id: 'victim', nameZh: '受害者', color: '#08D9D6', colorHex: 0x08D9D6, icon: '🛡️' }
        });
      }
    });
  }
}
