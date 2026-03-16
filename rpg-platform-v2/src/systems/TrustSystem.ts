/**
 * 信任系統管理器
 * 
 * 管理受害者對騙徒和專家的信任度，以及警覺性
 * 基於 Backend 的 PerformanceTracker 系統
 */

export interface TrustData {
  trustInScammer: number;    // 對騙徒的信任度 (0-100)
  trustInExpert: number;     // 對專家的信任度 (0-100)
  alertness: number;         // 警覺性 (0-100)
}

export type GameOutcome = 'scammer_win' | 'expert_win' | 'ongoing';

/**
 * 信任系統類
 */
export class TrustSystem {
  private trustInScammer: number = 50;
  private trustInExpert: number = 50;
  private alertness: number = 50;
  
  // 閾值配置（與 Backend config.py 保持一致）
  private readonly SCAMMER_WIN_THRESHOLD = 80;
  private readonly EXPERT_WIN_THRESHOLD = 75;
  private readonly SCAMMER_TRUST_MAX_FOR_EXPERT_WIN = 40;
  private readonly ALERTNESS_WIN_THRESHOLD = 80;

  constructor(initialTrust?: Partial<TrustData>) {
    if (initialTrust) {
      this.trustInScammer = initialTrust.trustInScammer ?? 50;
      this.trustInExpert = initialTrust.trustInExpert ?? 50;
      this.alertness = initialTrust.alertness ?? 50;
    }
  }

  /**
   * 更新信任度數據
   * @param data 從 Backend 返回的信任度數據
   */
  updateTrust(data: {
    trust_in_scammer?: number;
    trust_in_expert?: number;
  }): void {
    if (data.trust_in_scammer !== undefined) {
      this.trustInScammer = this.clamp(data.trust_in_scammer, 0, 100);
      console.log(`[TrustSystem] 對騙徒的信任度: ${this.trustInScammer}`);
    }
    
    if (data.trust_in_expert !== undefined) {
      this.trustInExpert = this.clamp(data.trust_in_expert, 0, 100);
      console.log(`[TrustSystem] 對專家的信任度: ${this.trustInExpert}`);
    }
    
    // 計算警覺性：信任騙徒越低，警覺性越高
    this.alertness = Math.max(0, 100 - this.trustInScammer);
    console.log(`[TrustSystem] 警覺性: ${this.alertness}`);
  }

  /**
   * 直接更新所有信任度數據（用於三方對話 API）
   * @param trustInScammer 對騙徒的信任度
   * @param trustInExpert 對專家的信任度
   * @param alertness 警覺性
   */
  updateTrustDirect(
    trustInScammer: number,
    trustInExpert: number,
    alertness: number
  ): void {
    this.trustInScammer = this.clamp(trustInScammer, 0, 100);
    this.trustInExpert = this.clamp(trustInExpert, 0, 100);
    this.alertness = this.clamp(alertness, 0, 100);
    
    console.log(`[TrustSystem] 信任度已更新 - 騙徒: ${this.trustInScammer}, 專家: ${this.trustInExpert}, 警覺: ${this.alertness}`);
  }

  /**
   * 獲取對騙徒的信任度
   */
  getTrustInScammer(): number {
    return this.trustInScammer;
  }

  /**
   * 獲取對專家的信任度
   */
  getTrustInExpert(): number {
    return this.trustInExpert;
  }

  /**
   * 獲取警覺性
   */
  getAlertness(): number {
    return this.alertness;
  }

  /**
   * 獲取所有信任數據
   */
  getAllTrustData(): TrustData {
    return {
      trustInScammer: this.trustInScammer,
      trustInExpert: this.trustInExpert,
      alertness: this.alertness
    };
  }

  /**
   * 檢查遊戲結果
   * 
   * 勝利條件：
   * - 騙徒勝利：對騙徒的信任度 >= 80
   * - 專家勝利：對專家的信任度 >= 75 且對騙徒的信任度 < 40
   * - 警覺勝利：警覺性 >= 80
   * - 進行中：不滿足以上任何條件
   */
  checkOutcome(): GameOutcome {
    // 騙徒勝利條件
    if (this.trustInScammer >= this.SCAMMER_WIN_THRESHOLD) {
      console.log('[TrustSystem] 遊戲結束：騙徒勝利（信任度過高）');
      return 'scammer_win';
    }
    
    // 專家勝利條件
    if (
      this.trustInExpert >= this.EXPERT_WIN_THRESHOLD &&
      this.trustInScammer < this.SCAMMER_TRUST_MAX_FOR_EXPERT_WIN
    ) {
      console.log('[TrustSystem] 遊戲結束：專家勝利（成功保護受害者）');
      return 'expert_win';
    }
    
    // 警覺勝利條件
    if (this.alertness >= this.ALERTNESS_WIN_THRESHOLD) {
      console.log('[TrustSystem] 遊戲結束：受害者警覺（自我保護）');
      return 'expert_win';  // 視為專家勝利
    }
    
    return 'ongoing';
  }

  /**
   * 獲取信任度變化的描述
   */
  getTrustChangeDescription(previousTrust: TrustData): string {
    const scammerChange = this.trustInScammer - previousTrust.trustInScammer;
    const expertChange = this.trustInExpert - previousTrust.trustInExpert;
    
    const descriptions: string[] = [];
    
    if (Math.abs(scammerChange) > 5) {
      if (scammerChange > 0) {
        descriptions.push(`⚠️ 對騙徒的信任度增加了 ${scammerChange.toFixed(1)} 點`);
      } else {
        descriptions.push(`✅ 對騙徒的信任度降低了 ${Math.abs(scammerChange).toFixed(1)} 點`);
      }
    }
    
    if (Math.abs(expertChange) > 5) {
      if (expertChange > 0) {
        descriptions.push(`✅ 對專家的信任度增加了 ${expertChange.toFixed(1)} 點`);
      } else {
        descriptions.push(`⚠️ 對專家的信任度降低了 ${Math.abs(expertChange).toFixed(1)} 點`);
      }
    }
    
    return descriptions.join('\n') || '信任度變化不大';
  }

  /**
   * 獲取當前狀態的風險等級
   */
  getRiskLevel(): 'safe' | 'caution' | 'danger' | 'critical' {
    if (this.trustInScammer >= 80) {
      return 'critical';  // 極度危險
    } else if (this.trustInScammer >= 60) {
      return 'danger';    // 危險
    } else if (this.trustInScammer >= 40) {
      return 'caution';   // 警戒
    } else {
      return 'safe';      // 安全
    }
  }

  /**
   * 獲取風險等級的顏色
   */
  getRiskColor(): string {
    const level = this.getRiskLevel();
    const colors = {
      safe: '#08D9D6',      // 青色（安全）
      caution: '#FFD700',   // 金色（警戒）
      danger: '#FF8C00',    // 橙色（危險）
      critical: '#FF2E63'   // 紅色（極度危險）
    };
    return colors[level];
  }

  /**
   * 獲取風險等級的描述
   */
  getRiskDescription(): string {
    const level = this.getRiskLevel();
    const descriptions = {
      safe: '✅ 安全：保持警覺，繼續識別詐騙手法',
      caution: '⚠️ 警戒：開始相信騙徒，需要提高警覺',
      danger: '🚨 危險：高度信任騙徒，可能被騙',
      critical: '💀 極度危險：即將上當，立即停止對話！'
    };
    return descriptions[level];
  }

  /**
   * 重置信任系統
   */
  reset(): void {
    this.trustInScammer = 50;
    this.trustInExpert = 50;
    this.alertness = 50;
    console.log('[TrustSystem] 信任系統已重置');
  }

  /**
   * 限制數值範圍
   */
  private clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, value));
  }

  /**
   * 導出狀態（用於保存/恢復）
   */
  exportState(): TrustData {
    return this.getAllTrustData();
  }

  /**
   * 導入狀態（用於保存/恢復）
   */
  importState(state: TrustData): void {
    this.trustInScammer = this.clamp(state.trustInScammer, 0, 100);
    this.trustInExpert = this.clamp(state.trustInExpert, 0, 100);
    this.alertness = this.clamp(state.alertness, 0, 100);
    console.log('[TrustSystem] 狀態已導入:', state);
  }
}
