/**
 * Backend API 客戶端
 * 
 * 負責與 FastAPI Backend 通信，處理 AI 對話和會話管理
 */

export interface SimulationConfig {
  scamType: string;                    // 騙案類型 ID
  playerRole: 'victim' | 'expert' | 'scammer';     // 玩家角色
  victimPersona?: string;              // 受害者人格
}

export interface MessageResponse {
  reply: string;                       // AI 回覆內容
  trust_in_scammer?: number;           // 對騙徒的信任度 (0-100)
  trust_in_expert?: number;            // 對專家的信任度 (0-100)
  metrics?: {                          // 性能指標
    persuasiveness?: number;
    credibility?: number;
    empathy?: number;
  };
  success: boolean;                    // 請求是否成功
  error?: string;                      // 錯誤訊息（如果有）
}

export interface ThreeWayMessageResponse {
  session_id: string;
  replies: Array<{
    speaker: 'scammer' | 'expert' | 'victim';
    message: string;
  }>;
  trust_data?: {
    trust_in_scammer: number;
    trust_in_expert: number;
    alertness: number;
    round_count: number;
  };
  game_status?: {
    game_over: boolean;
    winner?: string;
    reason?: string;
    instant_win?: boolean;
    final_scores?: {
      player: number;
      ai: number;
    };
    final_trust?: {
      trust_in_scammer: number;
      trust_in_expert: number;
      alertness: number;
    };
  };
  success: boolean;
}

export interface AnalysisResponse {
  success: boolean;
  session_id: string;
  analysis: {
    scammer_score: number;             // 騙徒評分 (0-100)
    expert_score: number;              // 專家評分 (0-100)
    outcome: string;                   // 結果描述
    key_moments: Array<{               // 關鍵時刻
      round: number;
      description: string;
      impact: string;
    }>;
    recommendations: string[];         // 建議
  };
  conversation_count: number;
}

/**
 * Backend API 客戶端類
 */
export class BackendClient {
  private baseURL: string;
  private sessionId: string | null = null;
  private isConnected: boolean = false;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  /**
   * 檢查 Backend 連接狀態
   */
  async checkConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/game/v2/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        this.isConnected = data.status === 'ok';
        console.log('[BackendClient] Backend 連接成功:', data);
        return this.isConnected;
      }
      
      this.isConnected = false;
      return false;
    } catch (error) {
      console.error('[BackendClient] Backend 連接失敗:', error);
      this.isConnected = false;
      return false;
    }
  }

  /**
   * 開始新會話（RPGv2 遊戲模式）
   * @param config 模擬配置
   * @returns 會話 ID 和開場消息數組
   */
  async startThreeWaySession(config: SimulationConfig): Promise<{ 
    sessionId: string; 
    openingMessages: Array<{role: string, content: string}> 
  }> {
    try {
      console.log('[BackendClient] 開始 RPGv2 遊戲會話:', config);
      
      const response = await fetch(`${this.baseURL}/api/rpgv2/game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: config.playerRole,  // victim, expert, scammer
          scam_type: config.scamType,
          victim_persona: config.victimPersona || 'average'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.sessionId = data.session_id;
      
      console.log('[BackendClient] RPGv2 會話創建成功:', this.sessionId);
      console.log('[BackendClient] 開場消息:', data.opening_messages);
      
      // 返回開場消息數組
      return {
        sessionId: this.sessionId,
        openingMessages: data.opening_messages || []
      };
    } catch (error) {
      console.error('[BackendClient] 開始 RPGv2 會話失敗:', error);
      throw error;
    }
  }

  /**
   * 發送消息（RPGv2 遊戲模式）
   * 玩家發送消息後，AI 角色會回應
   * @param message 玩家消息
   * @returns AI 回應和遊戲狀態
   */
  async sendThreeWayMessage(message: string): Promise<ThreeWayMessageResponse> {
    if (!this.sessionId) {
      throw new Error('未初始化會話，請先調用 startThreeWaySession()');
    }

    try {
      console.log('[BackendClient] 發送 RPGv2 消息:', message);

      const response = await fetch(`${this.baseURL}/api/rpgv2/game/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          message: message
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[BackendClient] 收到 RPGv2 回應:', data);

      // 轉換格式以匹配前端期望
      return {
        session_id: data.session_id,
        replies: data.ai_responses.map((resp: any) => ({
          speaker: resp.role,
          message: resp.content
        })),
        trust_data: data.game_state,
        game_status: data.game_status,  // 🔥 添加遊戲狀態
        success: data.success
      };
    } catch (error) {
      console.error('[BackendClient] 發送 RPGv2 消息失敗:', error);
      throw error;
    }
  }

  /**
   * 獲取 RPGv2 遊戲的最終分析
   */
  async getThreeWayAnalysis(): Promise<any> {
    if (!this.sessionId) {
      throw new Error('未初始化會話');
    }

    try {
      console.log('[BackendClient] 請求 RPGv2 遊戲狀態...');

      const response = await fetch(`${this.baseURL}/api/rpgv2/game/state/${this.sessionId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[BackendClient] 收到 RPGv2 遊戲狀態:', data);

      return data;
    } catch (error) {
      console.error('[BackendClient] 獲取 RPGv2 遊戲狀態失敗:', error);
      throw error;
    }
  }

  /**
   * 開始新會話
   * @param config 模擬配置
   * @returns 會話 ID
   */
  async startSession(config: SimulationConfig): Promise<string> {
    try {
      console.log('[BackendClient] 開始新會話:', config);
      
      // 映射玩家角色到 persona_type
      const personaType = config.victimPersona || 'average';
      
      const response = await fetch(`${this.baseURL}/api/game/v2/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona_type: personaType
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.sessionId = data.session_id;
      
      console.log('[BackendClient] 會話創建成功:', this.sessionId);
      return this.sessionId;
    } catch (error) {
      console.error('[BackendClient] 開始會話失敗:', error);
      throw error;
    }
  }

  /**
   * 發送消息給 AI
   * @param message 用戶消息
   * @param targetAI 目標 AI（scammer 或 expert）
   * @returns AI 回覆
   */
  async sendMessage(
    message: string,
    targetAI: 'scammer' | 'expert'
  ): Promise<MessageResponse> {
    if (!this.sessionId) {
      throw new Error('未初始化會話，請先調用 startSession()');
    }

    try {
      console.log(`[BackendClient] 發送消息給 ${targetAI}:`, message);

      // 映射到 Backend 的 AI 標識
      const aiMapping = {
        scammer: 'AI-D',  // 騙徒
        expert: 'AI-C'    // 防詐專家
      };

      const response = await fetch(`${this.baseURL}/api/game/v2/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          message: message,
          target_ai: aiMapping[targetAI],
          persona_type: 'average'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`[BackendClient] 收到 ${targetAI} 回覆:`, data);

      return {
        reply: data.reply,
        trust_in_scammer: data.trust_in_scammer,
        trust_in_expert: data.trust_in_expert,
        metrics: data.metrics,
        success: data.success !== false
      };
    } catch (error) {
      console.error('[BackendClient] 發送消息失敗:', error);
      return {
        reply: '抱歉，系統暫時無法回應。請稍後再試。',
        success: false,
        error: error instanceof Error ? error.message : '未知錯誤'
      };
    }
  }

  /**
   * 獲取最終分析報告
   * @returns 分析結果
   */
  async getAnalysis(): Promise<AnalysisResponse> {
    if (!this.sessionId) {
      throw new Error('未初始化會話，請先調用 startSession()');
    }

    try {
      console.log('[BackendClient] 請求最終分析...');

      const response = await fetch(`${this.baseURL}/api/game/v2/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[BackendClient] 收到分析報告:', data);

      return data;
    } catch (error) {
      console.error('[BackendClient] 獲取分析失敗:', error);
      throw error;
    }
  }

  /**
   * 結束會話
   */
  async endSession(): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    try {
      console.log('[BackendClient] 結束會話:', this.sessionId);

      await fetch(`${this.baseURL}/api/rpgv2/game/session/${this.sessionId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });

      this.sessionId = null;
    } catch (error) {
      console.error('[BackendClient] 結束會話失敗:', error);
    }
  }

  /**
   * 切換角色模式
   * @param newMode 新的角色模式 ('victim' | 'expert' | 'scammer')
   * @returns 切換結果
   */
  async switchRole(newMode: 'victim' | 'expert' | 'scammer'): Promise<{
    success: boolean;
    old_mode: string;
    new_mode: string;
    mode_info: any;
    message: string;
  }> {
    if (!this.sessionId) {
      throw new Error('未初始化會話，請先調用 startThreeWaySession()');
    }

    try {
      console.log('[BackendClient] 切換角色模式:', newMode);

      const response = await fetch(`${this.baseURL}/api/rpgv2/game/switch-role`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          new_mode: newMode
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[BackendClient] 角色切換成功:', data);

      return data;
    } catch (error) {
      console.error('[BackendClient] 角色切換失敗:', error);
      throw error;
    }
  }

  /**
   * 獲取當前會話 ID
   */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * 檢查是否已連接
   */
  isBackendConnected(): boolean {
    return this.isConnected;
  }

  /**
   * 設置 Base URL（用於配置不同環境）
   */
  setBaseURL(url: string): void {
    this.baseURL = url;
    console.log('[BackendClient] Base URL 已更新:', url);
  }
}

/**
 * 創建單例 Backend 客戶端
 */
let backendClientInstance: BackendClient | null = null;

export function getBackendClient(): BackendClient {
  if (!backendClientInstance) {
    // 從環境變量讀取 Backend URL（如果有）
    const backendURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
    backendClientInstance = new BackendClient(backendURL);
  }
  return backendClientInstance;
}
