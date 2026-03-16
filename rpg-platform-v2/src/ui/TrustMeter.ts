/**
 * 信任度計量表 UI 組件
 * 
 * 可重用的信任度顯示組件
 */

import Phaser from 'phaser';

export interface TrustMeterConfig {
  label: string;           // 標籤文字
  color: number;           // 顏色（hex）
  initialValue?: number;   // 初始值 (0-100)
  width?: number;          // 寬度
  height?: number;         // 高度
}

/**
 * 信任度計量表類
 */
export class TrustMeter extends Phaser.GameObjects.Container {
  private bar: Phaser.GameObjects.Rectangle;
  private bgBar: Phaser.GameObjects.Rectangle;
  private valueText: Phaser.GameObjects.Text;
  private labelText: Phaser.GameObjects.Text;
  private currentValue: number;
  private maxWidth: number;

  constructor(
    scene: Phaser.Scene,
    x: number,
    y: number,
    config: TrustMeterConfig
  ) {
    super(scene, x, y);

    this.currentValue = config.initialValue ?? 50;
    this.maxWidth = config.width ?? 200;
    const barHeight = config.height ?? 20;

    // 標籤
    this.labelText = scene.add.text(0, 0, config.label, {
      fontFamily: 'Noto Sans TC, sans-serif',
      fontSize: '16px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    this.labelText.setOrigin(0, 0.5);

    // 背景條
    this.bgBar = scene.add.rectangle(0, 25, this.maxWidth, barHeight, 0x333333);
    this.bgBar.setOrigin(0, 0.5);
    this.bgBar.setStrokeStyle(1, 0x666666, 0.5);

    // 進度條
    this.bar = scene.add.rectangle(0, 25, 0, barHeight, config.color);
    this.bar.setOrigin(0, 0.5);

    // 數值文字
    this.valueText = scene.add.text(this.maxWidth + 10, 25, '50%', {
      fontFamily: 'Rajdhani, sans-serif',
      fontSize: '18px',
      color: '#ffffff',
      fontStyle: 'bold'
    });
    this.valueText.setOrigin(0, 0.5);

    // 添加到容器
    this.add([this.labelText, this.bgBar, this.bar, this.valueText]);

    // 初始化顯示
    this.updateValue(this.currentValue, false);

    scene.add.existing(this);
  }

  /**
   * 更新數值
   * @param value 新數值 (0-100)
   * @param animate 是否使用動畫
   */
  updateValue(value: number, animate: boolean = true): void {
    value = Phaser.Math.Clamp(value, 0, 100);
    this.currentValue = value;

    const targetWidth = (value / 100) * this.maxWidth;

    if (animate) {
      // 動畫更新
      this.scene.tweens.add({
        targets: this.bar,
        width: targetWidth,
        duration: 500,
        ease: 'Power2'
      });
    } else {
      // 立即更新
      this.bar.width = targetWidth;
    }

    // 更新文字
    this.valueText.setText(`${Math.round(value)}%`);

    // 根據數值改變顏色強度
    this.updateBarColor(value);
  }

  /**
   * 根據數值更新顏色
   */
  private updateBarColor(value: number): void {
    // 可以根據數值調整透明度或顏色
    const alpha = 0.7 + (value / 100) * 0.3; // 0.7 到 1.0
    this.bar.setAlpha(alpha);
  }

  /**
   * 獲取當前數值
   */
  getValue(): number {
    return this.currentValue;
  }

  /**
   * 設置標籤文字
   */
  setLabel(label: string): void {
    this.labelText.setText(label);
  }

  /**
   * 設置顏色
   */
  setColor(color: number): void {
    this.bar.setFillStyle(color);
  }

  /**
   * 顯示脈衝動畫（用於強調變化）
   */
  pulse(): void {
    this.scene.tweens.add({
      targets: this.bar,
      scaleY: 1.2,
      duration: 200,
      yoyo: true,
      ease: 'Sine.easeInOut'
    });
  }

  /**
   * 顯示警告效果（當數值達到危險閾值時）
   */
  showWarning(): void {
    // 閃爍效果
    this.scene.tweens.add({
      targets: this.bar,
      alpha: { from: 1, to: 0.3 },
      duration: 300,
      yoyo: true,
      repeat: 2,
      ease: 'Sine.easeInOut'
    });
  }

  /**
   * 重置到初始值
   */
  reset(initialValue: number = 50): void {
    this.updateValue(initialValue, true);
  }
}

/**
 * 創建標準的信任度計量表組
 */
export class TrustMeterGroup extends Phaser.GameObjects.Container {
  private scammerMeter: TrustMeter;
  private expertMeter: TrustMeter;
  private alertnessMeter: TrustMeter;

  constructor(scene: Phaser.Scene, x: number, y: number) {
    super(scene, x, y);

    // 創建三個計量表
    this.scammerMeter = new TrustMeter(scene, 0, 0, {
      label: '🎭 對騙徒的信任',
      color: 0xFF2E63,
      initialValue: 50,
      width: 200
    });

    this.expertMeter = new TrustMeter(scene, 0, 60, {
      label: '🛡️ 對專家的信任',
      color: 0x08D9D6,
      initialValue: 50,
      width: 200
    });

    this.alertnessMeter = new TrustMeter(scene, 0, 120, {
      label: '⚠️ 警覺性',
      color: 0xFFD700,
      initialValue: 50,
      width: 200
    });

    this.add([this.scammerMeter, this.expertMeter, this.alertnessMeter]);
    scene.add.existing(this);
  }

  /**
   * 更新所有計量表
   */
  updateAll(scammerTrust: number, expertTrust: number, alertness: number): void {
    this.scammerMeter.updateValue(scammerTrust);
    this.expertMeter.updateValue(expertTrust);
    this.alertnessMeter.updateValue(alertness);

    // 如果騙徒信任度過高，顯示警告
    if (scammerTrust >= 80) {
      this.scammerMeter.showWarning();
    }
  }

  /**
   * 獲取各個計量表
   */
  getScammerMeter(): TrustMeter {
    return this.scammerMeter;
  }

  getExpertMeter(): TrustMeter {
    return this.expertMeter;
  }

  getAlertnessMeter(): TrustMeter {
    return this.alertnessMeter;
  }

  /**
   * 重置所有計量表
   */
  resetAll(): void {
    this.scammerMeter.reset();
    this.expertMeter.reset();
    this.alertnessMeter.reset();
  }
}
