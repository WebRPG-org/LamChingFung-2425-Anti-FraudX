import { localization } from './LocalizationManager';

export type RoleType = 'victim' | 'scammer' | 'expert';

export interface Role {
  id: RoleType;
  name: string;
  nameZh: string;
  color: string;
  colorHex: number;
  description: string;
  descriptionZh: string;
  aiOpponents: string[];
  icon: string;
}

export class RoleManager {
  private static instance: RoleManager;
  private currentRole: Role;
  private listeners: Set<(role: Role) => void> = new Set();
  
  // 角色順序：1=受害人, 2=騙徒, 3=專家
  private roles: Map<RoleType, Role> = new Map([
    ['victim', {
      id: 'victim',
      name: 'Victim',
      nameZh: '受害者',
      color: '#0984E3',
      colorHex: 0x0984E3,
      description: 'Defend against scam attempts and identify red flags',
      descriptionZh: '防禦詐騙攻擊，識別危險信號',
      aiOpponents: ['scammer', 'expert', 'recorder'],
      icon: '🛡️'
    }],
    ['scammer', {
      id: 'scammer',
      name: 'Scammer',
      nameZh: '騙徒',
      color: '#FF6B6B',
      colorHex: 0xFF6B6B,
      description: 'Manipulate victims using psychological tactics',
      descriptionZh: '使用心理戰術操縱受害者',
      aiOpponents: ['victim', 'expert', 'recorder'],
      icon: '🎭'
    }],
    ['expert', {
      id: 'expert',
      name: 'Expert',
      nameZh: '防詐專家',
      color: '#00B894',
      colorHex: 0x00B894,
      description: 'Intervene in scams and educate victims',
      descriptionZh: '介入詐騙並教育受害者',
      aiOpponents: ['scammer', 'victim', 'recorder'],
      icon: '👮'
    }]
  ]);

  private constructor() {
    this.currentRole = this.roles.get('victim')!;
    this.applyLocalization();
  }

  static getInstance(): RoleManager {
    if (!RoleManager.instance) {
      RoleManager.instance = new RoleManager();
    }
    return RoleManager.instance;
  }

  getCurrentRole(): Role {
    return this.currentRole;
  }

  getAllRoles(): Role[] {
    return Array.from(this.roles.values());
  }

  switchRole(roleType: RoleType): void {
    const newRole = this.roles.get(roleType);
    if (newRole && newRole.id !== this.currentRole.id) {
      this.currentRole = newRole;
      this.notifyListeners();
      console.log(`[RoleManager] Switched to role: ${newRole.nameZh}`);
    }
  }

  onRoleChange(callback: (role: Role) => void): void {
    this.listeners.add(callback);
  }

  offRoleChange(callback: (role: Role) => void): void {
    this.listeners.delete(callback);
  }

  private notifyListeners(): void {
    this.listeners.forEach(callback => callback(this.currentRole));
  }

  applyLocalization(): void {
    const victim = this.roles.get('victim');
    const scammer = this.roles.get('scammer');
    const expert = this.roles.get('expert');

    if (victim) {
      victim.nameZh = localization.t('roleVictim');
      victim.descriptionZh = localization.t('roleDescVictim');
    }
    if (scammer) {
      scammer.nameZh = localization.t('roleScammer');
      scammer.descriptionZh = localization.t('roleDescScammer');
    }
    if (expert) {
      expert.nameZh = localization.t('roleExpert');
      expert.descriptionZh = localization.t('roleDescExpert');
    }

    this.notifyListeners();
  }
}
