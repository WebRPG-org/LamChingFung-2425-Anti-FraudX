/**
 * 結果場景 - 顯示對話分析報告
 * 
 * 展示 RecorderAgent 生成的詳細評分和分析
 */

import Phaser from 'phaser';
import { ScamType } from '../types/ScamTypes';
import { TrustData } from '../systems/TrustSystem';
import { localization } from '../systems/LocalizationManager';

interface ResultSceneData {
  outcome: 'scammer_win' | 'expert_win' | 'ongoing';
  playerRole?: 'victim' | 'expert' | 'scammer' | 'auto' | 'observer';
  analysis?: {
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
  trustData?: TrustData;
  roundCount: number;
}

export class ResultScene extends Phaser.Scene {
  private sceneData!: ResultSceneData;

  constructor() {
    super({ key: 'ResultScene' });
  }

  init(data: ResultSceneData): void {
    // 防護：確保 analysis 欄位存在
    this.sceneData = {
      ...data,
      analysis: data.analysis ?? {
        success: true,
        session_id: '',
        analysis: { scammer_score: 0, expert_score: 0, outcome: data.outcome },
        conversation_count: data.roundCount ?? 0
      }
    };
    console.log('[ResultScene] 顯示結果:', this.sceneData);
    console.log('[ResultScene] outcome 值:', this.sceneData.outcome);
    console.log('[ResultScene] outcome 類型:', typeof this.sceneData.outcome);
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
    if (this.sceneData.outcome === 'expert_win') {
      bgColor1 = 0x08D9D6;  // 青色（成功）
      bgColor2 = 0x0A0E27;
    } else if (this.sceneData.outcome === 'scammer_win') {
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
    const panelBg = this.add.rectangle(0, 0, 900, 550, 0x16213E, 0.95);
    panelBg.setStrokeStyle(3, this.getOutcomeColor(), 0.8);
    panel.add(panelBg);

    // 標題
    const title = this.createTitle();
    title.setPosition(0, -260);
    panel.add(title);

    // 騙案類型資訊
    const scamInfo = this.createScamInfo();
    scamInfo.setPosition(0, -195);
    panel.add(scamInfo);

    // 信任度數據
    const trustInfo = this.createTrustInfo();
    trustInfo.setPosition(0, -80);
    panel.add(trustInfo);

    // 建議區域
    const recommendations = this.createRecommendations();
    recommendations.setPosition(0, 70);
    panel.add(recommendations);

    // 按鈕
    const buttons = this.createButtons();
    buttons.setPosition(0, 240);
    panel.add(buttons);

    return panel;
  }

  private createTitle(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);
    const lang = localization.getLanguage();
    const mode = this.sceneData.playerRole ?? 'victim';
    const outcome = this.sceneData.outcome;

    let titleText: string;
    let titleIcon: string;
    let titleColor: string;

    if (mode === 'victim') {
      // 受害者模式
      if (outcome === 'expert_win') {
        titleIcon = '✅'; titleColor = '#08D9D6';
        titleText = lang === 'en-US' ? 'You Saw Through the Scam!'
          : lang === 'ja-JP' ? '詐欺を見抜きました！'
          : lang === 'zh-CN' ? '你成功識破騙局！'
          : '你成功識破騙局！';
      } else {
        titleIcon = '💀'; titleColor = '#FF2E63';
        titleText = lang === 'en-US' ? 'You Were Scammed...'
          : lang === 'ja-JP' ? '騙されました...'
          : lang === 'zh-CN' ? '你被骗了...'
          : '你被騙了...';
      }
    } else if (mode === 'scammer') {
      // 騙徒模式
      if (outcome === 'scammer_win') {
        titleIcon = '🎭'; titleColor = '#FF2E63';
        titleText = lang === 'en-US' ? 'Scam Successful! Victim Deceived!'
          : lang === 'ja-JP' ? '詐欺成功！被害者を騙しました！'
          : lang === 'zh-CN' ? '詐騙成功！受害者上鉤了！'
          : '詐騙成功！受害者上釣咗！';
      } else {
        titleIcon = '🛡️'; titleColor = '#08D9D6';
        titleText = lang === 'en-US' ? 'Scam Failed! Victim Was Alerted!'
          : lang === 'ja-JP' ? '詐欺失敗！被害者に見破られました！'
          : lang === 'zh-CN' ? '詐騙失敗！受害者識破了你！'
          : '詐騙失敗！受害者識穿咗你！';
      }
    } else if (mode === 'expert') {
      // 專家模式
      if (outcome === 'expert_win') {
        titleIcon = '🛡️'; titleColor = '#08D9D6';
        titleText = lang === 'en-US' ? 'Anti-Scam Success! Victim Protected!'
          : lang === 'ja-JP' ? '防犯成功！被害者を守りました！'
          : lang === 'zh-CN' ? '防詐成功！成功保護受害者！'
          : '防詐成功！成功保護受害者！';
      } else {
        titleIcon = '💀'; titleColor = '#FF2E63';
        titleText = lang === 'en-US' ? 'Prevention Failed! Victim Was Deceived!'
          : lang === 'ja-JP' ? '防犯失敗！被害者が騙されました！'
          : lang === 'zh-CN' ? '防詐失敗！受害者被騙了！'
          : '防詐失敗！受害者被騙咗！';
      }
    } else {
      titleIcon = '⏸️'; titleColor = '#FFD700';
      titleText = lang === 'en-US' ? 'Dialogue Ended'
        : lang === 'ja-JP' ? '会話終了'
        : lang === 'zh-CN' ? '对话结束'
        : '對話結束';
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
      `${this.sceneData.scamType.icon} ${this.sceneData.scamType.nameZh}`, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '20px',
      color: '#FFFFFF',
      fontStyle: 'bold'
    });
    scamText.setOrigin(0.5);

    const dangerText = this.add.text(0, 30, 
      `危險等級: ${'⭐'.repeat(this.sceneData.scamType.dangerLevel)}`, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#FFD700'
    });
    dangerText.setOrigin(0.5);

    container.add([scamText, dangerText]);
    return container;
  }

  private createTrustInfo(): Phaser.GameObjects.Container {
    const container = this.add.container(0, 0);

    // 背景
    const bg = this.add.rectangle(0, 0, 850, 100, 0x0A0E27, 0.5);
    bg.setStrokeStyle(2, 0x08D9D6, 0.3);
    container.add(bg);

    const trustData = this.sceneData.trustData ?? { trustInScammer: 0, trustInExpert: 0, alertness: 50 };

    // 標題
    const title = this.add.text(0, -35, localization.t('trustPanel').replace('📊 ', '') !== localization.t('trustPanel') ? '📊 ' + (localization.getLanguage() === 'en-US' ? 'Final Trust Data' : localization.getLanguage() === 'ja-JP' ? '最終信頼度データ' : localization.getLanguage() === 'zh-CN' ? '📊 最终信任度数据' : '📊 最終信任度數據') : '📊 最終信任度數據', {
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
    const title = this.add.text(0, -35, localization.t('learningPoints'), {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#FFD700',
      fontStyle: 'bold'
    });
    title.setOrigin(0.5);

    // 建議文字
    const mode = this.sceneData.playerRole ?? 'victim';
    const outcome = this.sceneData.outcome;
    const lang = localization.getLanguage();
    let recommendationText = '';

    if (mode === 'victim') {
      if (outcome === 'expert_win') {
        recommendationText = localization.t('successSummary');
      } else if (outcome === 'scammer_win') {
        recommendationText = localization.t('failSummary');
      } else {
        recommendationText = localization.t('neutralSummary');
      }
    } else if (mode === 'scammer') {
      if (outcome === 'scammer_win') {
        recommendationText = lang === 'en-US'
          ? '🎭 You successfully manipulated the victim! Study how psychological tactics work to better defend against them.'
          : lang === 'ja-JP'
          ? '🎭 被害者の操作に成功！心理的な手法を理解することで、詐欺への防衛力が高まります。'
          : lang === 'zh-CN'
          ? '🎭 你成功骗到了受害者！了解骗术心理有助于在现实中识破类似手法。'
          : '🎭 你成功騙到咗受害者！了解呢啲騙術手法，有助於喺現實中識破同類騙局。';
      } else {
        recommendationText = lang === 'en-US'
          ? '🛡️ The victim saw through your scam. Real-world scammers adapt and persist — stay vigilant!'
          : lang === 'ja-JP'
          ? '🛡️ 被害者に見破られました。現実の詐欺師は手口を変えてきます。常に警戒を！'
          : lang === 'zh-CN'
          ? '🛡️ 受害者识破了你的骗局。现实骗徒会不断变换手法，保持警惕！'
          : '🛡️ 受害者識穿咗你嘅騙局。現實騙徒會不斷變換手法，保持警覺！';
      }
    } else if (mode === 'expert') {
      if (outcome === 'expert_win') {
        recommendationText = lang === 'en-US'
          ? '🛡️ Excellent! Your advice successfully protected the victim. Keep sharing anti-scam knowledge!'
          : lang === 'ja-JP'
          ? '🛡️ 素晴らしい！あなたのアドバイスが被害者を守りました。防犯知識を広め続けましょう！'
          : lang === 'zh-CN'
          ? '🛡️ 出色！你的建议成功保护了受害者。继续传播防骗知识！'
          : '🛡️ 出色！你嘅建議成功保護咗受害者。繼續傳播防騙知識！';
      } else {
        recommendationText = lang === 'en-US'
          ? '💡 The victim was still deceived. Try more direct and urgent warnings next time to break through the scammer\'s influence.'
          : lang === 'ja-JP'
          ? '💡 被害者はまだ騙されてしまいました。次回はより直接的で緊急性のある警告を試してみましょう。'
          : lang === 'zh-CN'
          ? '💡 受害者还是被骗了。下次试试更直接、更紧迫的警告，打破骗徒的心理控制。'
          : '💡 受害者仍然俾人騙咗。下次試試更直接、更緊迫嘅警告，打破騙徒嘅心理控制。';
      }
    } else {
      recommendationText = localization.t('neutralSummary');
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
    const returnButton = this.createButton(-150, 0, localization.t('returnMap'), 0x08D9D6, () => {
      this.returnToWorld();
    });

    // 再試一次按鈕
    const retryButton = this.createButton(150, 0, localization.t('tryAgain'), 0xFF2E63, () => {
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
    if (this.sceneData.outcome === 'expert_win') {
      return 0x08D9D6;
    } else if (this.sceneData.outcome === 'scammer_win') {
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
    // 重新開始相同的騙案對話，保持原來的角色
    const mode = this.sceneData.playerRole ?? 'victim';
    const roleMap: Record<string, { id: string; nameZh: string; color: string; colorHex: number; icon: string }> = {
      victim:  { id: 'victim',  nameZh: '受害者',   color: '#08D9D6', colorHex: 0x08D9D6, icon: '🛡️' },
      scammer: { id: 'scammer', nameZh: '騙徒',     color: '#FF2E63', colorHex: 0xFF2E63, icon: '🎭' },
      expert:  { id: 'expert',  nameZh: '防詐專家', color: '#FFD93D', colorHex: 0xFFD93D, icon: '🔍' },
    };
    const playerRole = roleMap[mode] ?? roleMap['victim'];

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
          scamType: this.sceneData.scamType.id,
          scamTypeInfo: this.sceneData.scamType,
          playerRole
        });
      }
    });
  }
}
