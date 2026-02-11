export class RoleManager {
    constructor() {
        this.listeners = new Set();
        this.roles = new Map([
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
        this.currentRole = this.roles.get('victim');
    }
    static getInstance() {
        if (!RoleManager.instance) {
            RoleManager.instance = new RoleManager();
        }
        return RoleManager.instance;
    }
    getCurrentRole() {
        return this.currentRole;
    }
    getAllRoles() {
        return Array.from(this.roles.values());
    }
    switchRole(roleType) {
        const newRole = this.roles.get(roleType);
        if (newRole && newRole.id !== this.currentRole.id) {
            this.currentRole = newRole;
            this.notifyListeners();
            console.log(`[RoleManager] Switched to role: ${newRole.nameZh}`);
        }
    }
    onRoleChange(callback) {
        this.listeners.add(callback);
    }
    offRoleChange(callback) {
        this.listeners.delete(callback);
    }
    notifyListeners() {
        this.listeners.forEach(callback => callback(this.currentRole));
    }
}
