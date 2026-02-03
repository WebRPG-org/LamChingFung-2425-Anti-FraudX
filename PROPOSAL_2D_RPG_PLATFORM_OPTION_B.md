# Proposal: Alternative 2D RPG Platform (Option B)
## AI Anti-Scam Training System - Custom Web-Based Engine

**Date:** 2026-02-04  
**Status:** 📋 Proposal  
**Priority:** High  
**Estimated Development Time:** 4-6 weeks

---

## Executive Summary

This proposal outlines a custom-built 2D web-based RPG engine as an alternative to the existing RPG Maker MV implementation. The new platform prioritizes:

- **High-freedom role-playing** with dynamic identity switching
- **Automated AI observation** for continuous training data generation
- **Multi-modal communication** (text + voice input)
- **Living Lab environment** for autonomous scam simulations
- **Modern web technologies** for better performance and flexibility

---

## 1. Core Engine and Visuals

### Technology Stack

#### Primary Engine Options

**Option A: Phaser.js (Recommended)**
- ✅ Mature, battle-tested 2D game framework
- ✅ Excellent performance with WebGL/Canvas rendering
- ✅ Built-in physics, animations, and sprite management
- ✅ Large community and extensive documentation
- ✅ TypeScript support
- ⚠️ Larger bundle size (~1.5MB)

**Option B: PixiJS**
- ✅ Lightweight, fast 2D rendering engine
- ✅ Excellent for custom game logic
- ✅ Smaller bundle size (~500KB)
- ⚠️ Requires more custom implementation
- ⚠️ No built-in game loop or scene management

**Recommendation:** **Phaser.js 3.x** for faster development and built-in features.

#### Supporting Technologies

```javascript
{
  "engine": "Phaser 3.60+",
  "language": "TypeScript",
  "bundler": "Vite",
  "ui": "React (for HUD/menus)",
  "state": "Zustand or Redux Toolkit",
  "networking": "WebSocket (existing backend)",
  "audio": "Howler.js",
  "speech": "Web Speech API (STT/TTS)"
}
```

### Visual Design

#### Art Style
- **Top-down 2D perspective** (similar to classic RPGs)
- **Pixel art or vector graphics** (32x32 or 64x64 tiles)
- **Hong Kong urban environment** (streets, MTR stations, cafes, banks)
- **Diverse NPC sprites** representing different demographics

#### Map Structure
```
Game World
├── Central District (Business/Banking)
├── Mong Kok (Shopping/Street)
├── Tsim Sha Tsui (Tourist/Mixed)
├── Residential Area (Elderly/Families)
└── University Campus (Students)
```

---

## 2. Dynamic Identity System

### Role Switching Mechanism

#### Three Playable Identities

**1. The Victim (受害者)**
- **Goal:** Survive scam attempts, identify red flags
- **Mechanics:** Defend against manipulation, ask clarifying questions
- **Win Condition:** Maintain low trust in scammer, high alertness
- **UI Color:** Blue

**2. The Scammer (騙徒)**
- **Goal:** Manipulate NPCs/AI to gain trust and extract information
- **Mechanics:** Use psychological tactics, create urgency
- **Win Condition:** Achieve high trust from victim
- **UI Color:** Red

**3. The Anti-Fraud Expert (防詐專家)**
- **Goal:** Intervene in ongoing scams, educate victims
- **Mechanics:** Provide evidence, counter scammer arguments
- **Win Condition:** Lower victim's trust in scammer, increase alertness
- **UI Color:** Green

### HUD Design

```
┌─────────────────────────────────────────────────────┐
│ [🛡️ Role: Victim ▼]  [💬 Chat]  [🎤 Voice]  [⚙️]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│              [Game World View]                      │
│                                                     │
│  Trust Meter: ████████░░ 80%                       │
│  Alertness:   ██████████ 100%                      │
└─────────────────────────────────────────────────────┘
```

### Role Switching Implementation

```typescript
interface PlayerRole {
  id: 'victim' | 'scammer' | 'expert';
  name: string;
  color: string;
  abilities: string[];
  aiOpponents: AgentType[];
}

class RoleManager {
  private currentRole: PlayerRole;
  
  switchRole(newRole: PlayerRole): void {
    // Save current state
    this.saveRoleState(this.currentRole);
    
    // Switch role
    this.currentRole = newRole;
    
    // Update UI
    this.updateHUD();
    
    // Reconfigure AI agents
    this.reconfigureAIAgents();
  }
  
  private reconfigureAIAgents(): void {
    switch(this.currentRole.id) {
      case 'victim':
        // Deploy ScammerAgent + ExpertAgent + RecorderAgent
        break;
      case 'scammer':
        // Deploy VictimAgent + ExpertAgent + RecorderAgent
        break;
      case 'expert':
        // Deploy ScammerAgent + VictimAgent + RecorderAgent
        break;
    }
  }
}
```

---

## 3. Interaction and Combat Mechanics

### Proximity-Based Interaction

#### Detection System

```typescript
class InteractionSystem {
  private readonly INTERACTION_RADIUS = 64; // pixels
  
  checkNearbyNPCs(player: Player): NPC[] {
    return this.npcs.filter(npc => {
      const distance = Phaser.Math.Distance.Between(
        player.x, player.y,
        npc.x, npc.y
      );
      return distance <= this.INTERACTION_RADIUS;
    });
  }
  
  triggerScamSimulation(npc: NPC, scamType?: string): void {
    // Transition to Battle Scene
    this.scene.start('BattleScene', {
      npc: npc,
      scamType: scamType || this.randomScamType(),
      playerRole: this.roleManager.getCurrentRole()
    });
  }
}
```

### Battle Scene (Dialogue Interface)

#### Scene Structure

```
┌─────────────────────────────────────────────────────┐
│ [← Back to Map]              Scam Type: 投資詐騙    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Scammer Avatar]  [Victim Avatar]  [Expert Avatar]│
│                                                     │
│  ┌─────────────────────────────────────────────┐  │
│  │ Scammer: 我有一個穩賺不賠的投資機會...        │  │
│  │                                              │  │
│  │ Expert: 小心！這可能是詐騙...                │  │
│  │                                              │  │
│  │ You (Victim): [Your response here]           │  │
│  └─────────────────────────────────────────────┘  │
│                                                     │
│  Trust in Scammer: ████████░░ 80%                 │
│  Trust in Expert:  ██████░░░░ 60%                 │
│  Alertness:        ████░░░░░░ 40%                 │
│                                                     │
│  [Text Input] ────────────────────── [Send] [🎤]  │
└─────────────────────────────────────────────────────┘
```

#### Dialogue Flow

```typescript
class BattleScene extends Phaser.Scene {
  private dialogueManager: DialogueManager;
  private aiAgents: Map<AgentType, AIAgent>;
  private trustSystem: TrustSystem;
  
  async startDialogue(): Promise<void> {
    // Initialize agents based on player role
    this.initializeAgents();
    
    // Start dialogue loop
    while (!this.isSimulationComplete()) {
      // AI agents take turns
      for (const [type, agent] of this.aiAgents) {
        const response = await agent.generateResponse(
          this.dialogueManager.getHistory()
        );
        
        this.displayMessage(type, response);
        this.updateTrustMeters(response);
      }
      
      // Wait for player input
      const playerInput = await this.waitForPlayerInput();
      this.processPlayerInput(playerInput);
      
      // Check win/loss conditions
      this.checkOutcome();
    }
  }
  
  private checkOutcome(): SimulationOutcome {
    const scammerTrust = this.trustSystem.getTrust('scammer');
    const expertTrust = this.trustSystem.getTrust('expert');
    const alertness = this.trustSystem.getAlertness();
    
    if (scammerTrust >= 80) {
      return { result: 'SCAMMER_WIN', reason: 'High trust in scammer' };
    } else if (expertTrust >= 75 || alertness >= 80) {
      return { result: 'EXPERT_WIN', reason: 'Victim protected' };
    }
    
    return { result: 'ONGOING' };
  }
}
```

### Scam Type Selection

#### Manual Selection Menu

```typescript
const SCAM_TYPES = [
  { id: 'investment', name: '虛假投資詐騙', icon: '💰' },
  { id: 'phishing', name: '釣魚短訊', icon: '📱' },
  { id: 'romance', name: '愛情詐騙', icon: '💕' },
  { id: 'impersonation', name: '假冒官員', icon: '👮' },
  { id: 'shopping', name: '虛假購物', icon: '🛒' },
  { id: 'job', name: '求職詐騙', icon: '💼' },
  { id: 'prize', name: '中獎詐騙', icon: '🎁' },
  { id: 'whatsapp', name: 'WhatsApp詐騙', icon: '💬' },
  { id: 'banking', name: '假冒銀行', icon: '🏦' },
  { id: 'random', name: '隨機選擇', icon: '🎲' }
];
```

---

## 4. Multi-Modal Communication

### Text Input (Primary)

```typescript
class TextInputHandler {
  private inputField: HTMLInputElement;
  
  async getPlayerInput(): Promise<string> {
    return new Promise((resolve) => {
      this.inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          resolve(this.inputField.value);
          this.inputField.value = '';
        }
      });
    });
  }
}
```

### Voice Input (Speech-to-Text)

```typescript
class VoiceInputHandler {
  private recognition: SpeechRecognition;
  private isListening: boolean = false;
  
  constructor() {
    // Initialize Web Speech API
    const SpeechRecognition = window.SpeechRecognition || 
                              window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.lang = 'zh-HK'; // Cantonese
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
  }
  
  async startListening(): Promise<string> {
    return new Promise((resolve, reject) => {
      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        resolve(transcript);
      };
      
      this.recognition.onerror = (event) => {
        reject(new Error(`Speech recognition error: ${event.error}`));
      };
      
      this.recognition.start();
      this.isListening = true;
    });
  }
  
  stopListening(): void {
    this.recognition.stop();
    this.isListening = false;
  }
}
```

### Voice Output (Text-to-Speech)

```typescript
class VoiceOutputHandler {
  private synth: SpeechSynthesis;
  private voice: SpeechSynthesisVoice | null = null;
  
  constructor() {
    this.synth = window.speechSynthesis;
    this.loadVoices();
  }
  
  private loadVoices(): void {
    const voices = this.synth.getVoices();
    // Prefer Cantonese voice
    this.voice = voices.find(v => v.lang === 'zh-HK') || voices[0];
  }
  
  speak(text: string, agentType: AgentType): void {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = this.voice;
    utterance.lang = 'zh-HK';
    
    // Adjust voice characteristics by agent type
    switch(agentType) {
      case 'scammer':
        utterance.rate = 1.1; // Slightly faster (urgency)
        utterance.pitch = 1.0;
        break;
      case 'victim':
        utterance.rate = 0.9; // Slower (confused)
        utterance.pitch = 1.1;
        break;
      case 'expert':
        utterance.rate = 1.0; // Normal (confident)
        utterance.pitch = 0.9;
        break;
    }
    
    this.synth.speak(utterance);
  }
}
```

### Unified Input Manager

```typescript
class InputManager {
  private textHandler: TextInputHandler;
  private voiceHandler: VoiceInputHandler;
  private currentMode: 'text' | 'voice' = 'text';
  
  async getPlayerInput(): Promise<string> {
    if (this.currentMode === 'voice') {
      try {
        return await this.voiceHandler.startListening();
      } catch (error) {
        console.error('Voice input failed, falling back to text:', error);
        this.currentMode = 'text';
        return await this.textHandler.getPlayerInput();
      }
    } else {
      return await this.textHandler.getPlayerInput();
    }
  }
  
  toggleInputMode(): void {
    this.currentMode = this.currentMode === 'text' ? 'voice' : 'text';
  }
}
```

---

## 5. Autonomous Observation Mode (Auto-Training)

### Living Lab Environment

#### Auto Mode Architecture

```typescript
class AutoModeController {
  private isRunning: boolean = false;
  private player: AIControlledPlayer;
  private statistics: AutoModeStats;
  
  async start(): Promise<void> {
    this.isRunning = true;
    this.statistics = new AutoModeStats();
    
    while (this.isRunning) {
      // 1. Navigate to random NPC
      const targetNPC = this.selectRandomNPC();
      await this.player.navigateTo(targetNPC);
      
      // 2. Randomize persona and tactic
      const persona = this.randomPersona();
      const tactic = this.randomScamTactic();
      
      // 3. Initiate scam simulation
      const simulation = await this.startAutonomousSimulation({
        npc: targetNPC,
        persona: persona,
        tactic: tactic
      });
      
      // 4. Run full dialogue cycle
      const result = await simulation.runToCompletion();
      
      // 5. Generate analysis report
      const report = await this.generateReport(result);
      
      // 6. Save training data
      await this.saveTrainingData(result, report);
      
      // 7. Update statistics
      this.statistics.recordSimulation(result);
      
      // 8. Brief pause before next iteration
      await this.delay(2000);
    }
  }
  
  stop(): void {
    this.isRunning = false;
  }
  
  getStatistics(): AutoModeStats {
    return this.statistics;
  }
}
```

#### AI-Controlled Player

```typescript
class AIControlledPlayer {
  private pathfinding: PathfindingSystem;
  private sprite: Phaser.GameObjects.Sprite;
  
  async navigateTo(target: NPC): Promise<void> {
    const path = this.pathfinding.findPath(
      this.sprite.x, this.sprite.y,
      target.x, target.y
    );
    
    for (const point of path) {
      await this.moveTo(point.x, point.y);
    }
  }
  
  private async moveTo(x: number, y: number): Promise<void> {
    return new Promise((resolve) => {
      this.scene.tweens.add({
        targets: this.sprite,
        x: x,
        y: y,
        duration: 500,
        onComplete: () => resolve()
      });
    });
  }
}
```

#### Statistics Dashboard

```typescript
interface AutoModeStats {
  totalSimulations: number;
  scammerWins: number;
  expertWins: number;
  averageDuration: number;
  personaBreakdown: Map<string, number>;
  tacticBreakdown: Map<string, number>;
  trainingDataGenerated: number; // MB
}

class StatsDashboard {
  render(stats: AutoModeStats): HTMLElement {
    return `
      <div class="stats-dashboard">
        <h2>🤖 Auto Mode Statistics</h2>
        <div class="stat-grid">
          <div class="stat-card">
            <span class="stat-value">${stats.totalSimulations}</span>
            <span class="stat-label">Total Simulations</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">${stats.scammerWins}</span>
            <span class="stat-label">Scammer Wins</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">${stats.expertWins}</span>
            <span class="stat-label">Expert Wins</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">${stats.averageDuration}s</span>
            <span class="stat-label">Avg Duration</span>
          </div>
        </div>
        <button onclick="stopAutoMode()">⏹️ Stop Auto Mode</button>
      </div>
    `;
  }
}
```

---

## 6. Technical Architecture

### Project Structure

```
frontend/
├── rpg-platform-v2/
│   ├── src/
│   │   ├── scenes/
│   │   │   ├── BootScene.ts
│   │   │   ├── MainMenuScene.ts
│   │   │   ├── WorldMapScene.ts
│   │   │   ├── BattleScene.ts
│   │   │   └── AutoModeScene.ts
│   │   ├── entities/
│   │   │   ├── Player.ts
│   │   │   ├── NPC.ts
│   │   │   └── AIControlledPlayer.ts
│   │   ├── systems/
│   │   │   ├── RoleManager.ts
│   │   │   ├── DialogueManager.ts
│   │   │   ├── TrustSystem.ts
│   │   │   ├── InputManager.ts
│   │   │   ├── VoiceHandler.ts
│   │   │   └── AutoModeController.ts
│   │   ├── ui/
│   │   │   ├── HUD.tsx
│   │   │   ├── RoleSwitcher.tsx
│   │   │   ├── TrustMeter.tsx
│   │   │   └── StatsDashboard.tsx
│   │   ├── api/
│   │   │   └── BackendClient.ts
│   │   ├── assets/
│   │   │   ├── sprites/
│   │   │   ├── tilesets/
│   │   │   ├── audio/
│   │   │   └── ui/
│   │   └── main.ts
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
```

### Backend Integration

```typescript
class BackendClient {
  private ws: WebSocket;
  private baseURL: string = 'http://localhost:8000';
  
  async startSimulation(config: SimulationConfig): Promise<string> {
    const response = await fetch(`${this.baseURL}/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    return data.simulation_id;
  }
  
  connectWebSocket(simulationId: string): void {
    this.ws = new WebSocket(
      `ws://localhost:8000/ws/simulation/${simulationId}`
    );
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
  }
  
  sendPlayerMessage(message: string): void {
    this.ws.send(JSON.stringify({
      type: 'player_message',
      content: message
    }));
  }
}
```

---

## 7. Development Roadmap

### Phase 1: Core Engine Setup (Week 1-2)
- [ ] Initialize Phaser.js project with TypeScript
- [ ] Set up Vite build system
- [ ] Create basic scene structure
- [ ] Implement player movement and camera
- [ ] Design and import tileset/sprites
- [ ] Create world map with multiple zones

### Phase 2: Role System (Week 2-3)
- [ ] Implement RoleManager class
- [ ] Create role switching UI
- [ ] Design HUD for each role
- [ ] Implement trust/alertness meters
- [ ] Add role-specific abilities

### Phase 3: Battle Scene (Week 3-4)
- [ ] Create dialogue interface
- [ ] Integrate with existing AI agents
- [ ] Implement trust calculation system
- [ ] Add win/loss condition detection
- [ ] Create transition animations

### Phase 4: Multi-Modal Input (Week 4-5)
- [ ] Implement text input handler
- [ ] Add Web Speech API integration
- [ ] Create voice input UI
- [ ] Implement TTS for AI responses
- [ ] Add input mode toggle

### Phase 5: Auto Mode (Week 5-6)
- [ ] Implement AI-controlled player
- [ ] Create pathfinding system
- [ ] Build auto mode controller
- [ ] Add statistics dashboard
- [ ] Implement continuous loop logic

### Phase 6: Polish & Testing (Week 6)
- [ ] Add sound effects and music
- [ ] Optimize performance
- [ ] Cross-browser testing
- [ ] Mobile responsiveness
- [ ] User testing and feedback

---

## 8. Comparison: Option A vs Option B

| Feature | Option A (RPG Maker MV) | Option B (Custom Engine) |
|---------|-------------------------|--------------------------|
| **Development Time** | 2-3 weeks | 4-6 weeks |
| **Flexibility** | Limited by RPG Maker | Fully customizable |
| **Performance** | Good | Excellent |
| **File Size** | ~200MB | ~20MB |
| **Role Switching** | Difficult | Native support |
| **Voice Input** | Plugin required | Native Web API |
| **Auto Mode** | Complex scripting | Clean implementation |
| **Mobile Support** | Poor | Excellent |
| **Maintenance** | RPG Maker dependent | Full control |
| **Cost** | RPG Maker license | Free (open source) |

---

## 9. Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Browser compatibility issues | Medium | Medium | Polyfills, fallbacks |
| Voice API limitations | High | Low | Text fallback always available |
| Performance on low-end devices | Medium | Medium | Optimization, quality settings |
| WebSocket connection issues | Low | High | Reconnection logic, error handling |

### Development Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | High | Strict phase-based development |
| Asset creation delays | Medium | Medium | Use placeholder assets initially |
| Integration complexity | Medium | High | Early backend integration testing |
| Team skill gaps | Low | Medium | Training, documentation |

---

## 10. Recommendations

### Immediate Next Steps

1. **Prototype Development** (1 week)
   - Create minimal Phaser.js prototype
   - Test basic movement and NPC interaction
   - Validate WebSocket integration
   - Test voice input on target browsers

2. **Stakeholder Review**
   - Present prototype to team
   - Gather feedback on UX/UI
   - Confirm technical feasibility
   - Get approval for full development

3. **Resource Allocation**
   - Assign frontend developer(s)
   - Identify asset creation needs
   - Plan backend API extensions
   - Set up development environment

### Long-Term Vision

- **Multiplayer Mode:** Allow multiple players to interact in the same world
- **Leaderboards:** Track player performance and learning progress
- **Custom Scenarios:** Let users create and share custom scam scenarios
- **VR Support:** Extend to VR for even more immersive training
- **Analytics Dashboard:** Track learning outcomes and effectiveness

---

## Conclusion

Option B provides a **modern, flexible, and scalable** platform for anti-scam training. While it requires more initial development effort than Option A, it offers:

✅ **Superior user experience** with dynamic role switching  
✅ **Better performance** and smaller file size  
✅ **Native multi-modal input** without plugins  
✅ **Elegant auto mode** implementation  
✅ **Full customization** and control  
✅ **Future-proof** technology stack  

**Recommendation:** Proceed with **Option B** if resources and timeline permit. The investment will pay off in flexibility, performance, and user engagement.

---

**Next Steps:** Create prototype and schedule stakeholder review meeting.
