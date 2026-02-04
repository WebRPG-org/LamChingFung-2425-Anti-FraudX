/**
 * 騙案類型定義系統
 * 
 * 每個 NPC 代表一種真實的詐騙類型，而非使用人名
 */

// 騙案類型接口
export interface ScamType {
  id: string;                    // 唯一標識
  nameZh: string;                // 中文名稱
  nameEn: string;                // 英文名稱
  icon: string;                  // 圖標 emoji
  description: string;           // 簡短描述
  targetVictims: string[];       // 目標受害者類型
  dangerLevel: 1 | 2 | 3 | 4 | 5; // 危險等級 (1=低, 5=極高)
  color: string;                 // 主題顏色 (hex)
  spriteKey: string;             // 精靈圖鍵名
  tactics: string[];             // 常用詐騙手法
}

/**
 * 10+ 種真實騙案類型
 * 基於香港警方和消費者委員會的真實案例
 */
export const SCAM_TYPES: Record<string, ScamType> = {
  investment: {
    id: 'investment',
    nameZh: '虛假投資詐騙',
    nameEn: 'Investment Scam',
    icon: '💰',
    description: '聲稱有穩賺不賠的投資機會，誘騙受害者投入大量金錢',
    targetVictims: ['elderly', 'average', 'overconfident'],
    dangerLevel: 5,
    color: '#FFD700',
    spriteKey: 'npc-investment-scam',
    tactics: [
      '承諾高回報低風險',
      '展示虛假收益證明',
      '製造緊迫感（限時優惠）',
      '利用從眾心理（很多人已投資）'
    ]
  },
  
  phishing: {
    id: 'phishing',
    nameZh: '釣魚短訊詐騙',
    nameEn: 'Phishing SMS',
    icon: '📱',
    description: '假冒銀行、政府機構發送短訊，誘騙點擊惡意連結或提供個人資料',
    targetVictims: ['elderly', 'average', 'student'],
    dangerLevel: 4,
    color: '#FF6B6B',
    spriteKey: 'npc-phishing-scam',
    tactics: [
      '假冒銀行發送緊急通知',
      '聲稱帳戶異常需驗證',
      '提供虛假連結',
      '要求輸入密碼或驗證碼'
    ]
  },
  
  romance: {
    id: 'romance',
    nameZh: '愛情詐騙',
    nameEn: 'Romance Scam',
    icon: '💕',
    description: '在交友平台建立虛假感情關係，取得信任後騙取金錢',
    targetVictims: ['average', 'student'],
    dangerLevel: 5,
    color: '#FF69B4',
    spriteKey: 'npc-romance-scam',
    tactics: [
      '建立長期虛假關係',
      '表達強烈感情',
      '編造困難需要幫助',
      '承諾見面但總有藉口'
    ]
  },
  
  impersonation: {
    id: 'impersonation',
    nameZh: '假冒官員詐騙',
    nameEn: 'Impersonation Scam',
    icon: '👮',
    description: '假冒警察、法官、檢察官，聲稱受害者涉及刑事案件',
    targetVictims: ['elderly', 'average'],
    dangerLevel: 5,
    color: '#4169E1',
    spriteKey: 'npc-impersonation-scam',
    tactics: [
      '假冒執法人員',
      '聲稱涉及嚴重罪行',
      '要求保密不能告訴他人',
      '要求轉帳到「安全帳戶」'
    ]
  },
  
  shopping: {
    id: 'shopping',
    nameZh: '虛假購物詐騙',
    nameEn: 'Shopping Scam',
    icon: '🛒',
    description: '在網上販賣不存在的商品，收款後不發貨或發送假貨',
    targetVictims: ['average', 'student'],
    dangerLevel: 3,
    color: '#32CD32',
    spriteKey: 'npc-shopping-scam',
    tactics: [
      '超低價吸引',
      '要求先付款',
      '使用一次性帳戶',
      '收款後失聯'
    ]
  },
  
  job: {
    id: 'job',
    nameZh: '求職詐騙',
    nameEn: 'Job Scam',
    icon: '💼',
    description: '發布虛假招聘廣告，騙取培訓費、保證金或個人資料',
    targetVictims: ['student', 'average'],
    dangerLevel: 3,
    color: '#FF8C00',
    spriteKey: 'npc-job-scam',
    tactics: [
      '承諾高薪輕鬆工作',
      '要求先付培訓費',
      '收集個人敏感資料',
      '無正式合約'
    ]
  },
  
  prize: {
    id: 'prize',
    nameZh: '中獎詐騙',
    nameEn: 'Prize Scam',
    icon: '🎁',
    description: '聲稱受害者中獎，要求先支付稅金、手續費或運費',
    targetVictims: ['elderly', 'average'],
    dangerLevel: 3,
    color: '#FFD700',
    spriteKey: 'npc-prize-scam',
    tactics: [
      '聲稱中大獎',
      '要求先付稅金/手續費',
      '製造緊迫感（限時領取）',
      '要求保密'
    ]
  },
  
  whatsapp: {
    id: 'whatsapp',
    nameZh: 'WhatsApp 詐騙',
    nameEn: 'WhatsApp Scam',
    icon: '💬',
    description: '假冒親友在 WhatsApp 要求緊急匯款或借錢',
    targetVictims: ['elderly', 'average'],
    dangerLevel: 4,
    color: '#25D366',
    spriteKey: 'npc-whatsapp-scam',
    tactics: [
      '假冒親友',
      '聲稱緊急情況',
      '要求立即匯款',
      '不接電話只用文字'
    ]
  },
  
  banking: {
    id: 'banking',
    nameZh: '假冒銀行詐騙',
    nameEn: 'Banking Scam',
    icon: '🏦',
    description: '假冒銀行職員，聲稱帳戶有問題需要驗證或更新資料',
    targetVictims: ['elderly', 'average'],
    dangerLevel: 5,
    color: '#1E90FF',
    spriteKey: 'npc-banking-scam',
    tactics: [
      '假冒銀行來電',
      '聲稱帳戶異常',
      '要求提供密碼/驗證碼',
      '要求安裝遠程軟件'
    ]
  },
  
  crypto: {
    id: 'crypto',
    nameZh: '加密貨幣詐騙',
    nameEn: 'Crypto Scam',
    icon: '₿',
    description: '虛假加密貨幣投資平台或龐氏騙局，承諾暴利回報',
    targetVictims: ['overconfident', 'average', 'student'],
    dangerLevel: 5,
    color: '#F7931A',
    spriteKey: 'npc-crypto-scam',
    tactics: [
      '承諾暴利回報',
      '展示虛假交易記錄',
      '利用 FOMO 心理',
      '無法提款'
    ]
  },
  
  rental: {
    id: 'rental',
    nameZh: '租屋詐騙',
    nameEn: 'Rental Scam',
    icon: '🏠',
    description: '發布虛假租屋廣告，騙取訂金後失聯',
    targetVictims: ['student', 'average'],
    dangerLevel: 3,
    color: '#8B4513',
    spriteKey: 'npc-rental-scam',
    tactics: [
      '超低租金吸引',
      '聲稱人在外地無法看房',
      '要求先付訂金',
      '收款後失聯'
    ]
  },
  
  tech_support: {
    id: 'tech_support',
    nameZh: '技術支援詐騙',
    nameEn: 'Tech Support Scam',
    icon: '💻',
    description: '假冒技術支援人員，聲稱電腦有病毒需要付費修復',
    targetVictims: ['elderly', 'average'],
    dangerLevel: 4,
    color: '#4B0082',
    spriteKey: 'npc-tech-support-scam',
    tactics: [
      '假冒微軟/蘋果支援',
      '聲稱電腦有嚴重問題',
      '要求遠程控制',
      '收取高額費用'
    ]
  },
  
  charity: {
    id: 'charity',
    nameZh: '虛假慈善詐騙',
    nameEn: 'Charity Scam',
    icon: '❤️',
    description: '假冒慈善機構募款，利用同情心騙取捐款',
    targetVictims: ['elderly', 'average'],
    dangerLevel: 2,
    color: '#DC143C',
    spriteKey: 'npc-charity-scam',
    tactics: [
      '假冒知名慈善機構',
      '編造悲慘故事',
      '要求現金捐款',
      '無正式收據'
    ]
  }
};

/**
 * 獲取所有騙案類型列表
 */
export function getAllScamTypes(): ScamType[] {
  return Object.values(SCAM_TYPES);
}

/**
 * 根據 ID 獲取騙案類型
 */
export function getScamTypeById(id: string): ScamType | undefined {
  return SCAM_TYPES[id];
}

/**
 * 根據危險等級篩選騙案類型
 */
export function getScamTypesByDangerLevel(level: number): ScamType[] {
  return getAllScamTypes().filter(scam => scam.dangerLevel === level);
}

/**
 * 獲取隨機騙案類型
 */
export function getRandomScamType(): ScamType {
  const types = getAllScamTypes();
  return types[Math.floor(Math.random() * types.length)];
}

/**
 * 根據目標受害者類型獲取適合的騙案
 */
export function getScamTypesForVictim(victimType: string): ScamType[] {
  return getAllScamTypes().filter(scam => 
    scam.targetVictims.includes(victimType)
  );
}
