# Feature: RPGv2 Battle Scene (Overlay Mode)

> Category: Core | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

The Battle Scene is the **primary player-facing interface** of the platform. It renders as an HTML overlay on top of the live 2D world map — the Phaser.js scene keeps running underneath. Players type or speak messages and receive responses from multiple AI agents in real-time chat bubbles, while a live trust meter tracks the simulation outcome.

---

## Scene Lifecycle

```
WorldMapScene (Phaser — running continuously)
  │
  │  Player walks into NPC collision zone
  │  WorldMapScene.handleNPCInteraction(npc)
  │    → scene.launch('BattleScene', { scamType, npcData })
  │    → scene.pause('WorldMapScene')           ← map frozen, not destroyed
  ▼
BattleScene.create()
  ├── tryRestoreState()                         ← restore sessionStorage if same scamType
  ├── injectHTML()                              ← creates overlay div + CSS (once per page load)
  ├── POST /api/rpgv2/game-modes/start          ← initialise session on backend
  └── renderAllBubbles()                        ← replay saved messages if restored
  │
  │  Player sends message (text or voice)
  │  POST /api/rpgv2/game-modes/chat
  │    ← receives scammer_response + expert_response + trust_changes
  │  updateTrustMeter(trust_changes)
  │  checkOutcome() → if outcome: showResult() → scene.stop('BattleScene')
  │
  │  Player presses ESC or clicks "Return to Map"
  │  scene.stop('BattleScene')
  │  scene.resume('WorldMapScene')              ← map resumes from exact same position
  ▼
WorldMapScene (resumed)
```

---

## HTML Overlay Construction

The entire battle UI is a programmatically-created HTML element injected into `#game-container`.

| Property | Value |
|----------|-------|
| z-index | 900 |
| Background | `rgba(10, 14, 39, 0.75)` + `backdrop-filter: blur(6px)` |
| CSS injection | Single `<style id="bo-css">` tag; checked before injection to avoid duplicates |
| Layout | Flex column: header → chat area → trust sidebar → input bar |

---

## Chat Bubble System

| Bubble Type | Alignment | Trigger |
|-------------|-----------|--------|
| Player message | Right | Player sends text/voice |
| ScammerAgent response | Left (red accent) | API response |
| ExpertAgent response | Left (green accent) | API response |
| System message | Centre | Round count, outcome, errors |
| Typing indicator | Left | While API call is in-flight |

Typing indicator: three-dot bounce CSS animation displayed immediately on send, removed on response arrival.

---

## Voice Input

Integrated directly in `BattleScene.ts`. See [voice-input.md](voice-input.md) for full detail.

- Language: `zh-HK` (Cantonese)
- Auto-stops after 2 seconds of silence
- Partial results shown in input box while speaking
- Requires HTTPS or localhost + microphone permission

---

## Trust Meter

Sidebar panel with three animated progress bars:

| Bar | Colour | Tracks |
|-----|--------|-------|
| Scammer trust | Red gradient | `trust_data.scammer` |
| Expert trust | Green gradient | `trust_data.expert` |
| Alertness | Yellow gradient | `trust_data.alertness` |

- Hidden on mobile (responsive CSS)
- Updated after every API response
- Values animate smoothly via CSS `transition`

See [trust-meter.md](trust-meter.md) for backend trust calculation.

---

## Keyboard Shortcuts

| Key | Action |
|-----|-------|
| `Enter` | Send message |
| `ESC` | Return to World Map |
| `F1` | Switch active display to ScammerAgent |
| `F2` | Switch active display to ExpertAgent |
| `F3` | Switch active display to both (three-way view) |

---

## Session Persistence

All battle state is saved to `sessionStorage` on every update. On `BattleScene.create()`, `tryRestoreState()` checks if a saved session exists for the same `scamType` and restores it.

Saved state shape:
```typescript
{
  session_id: string,
  scamType: string,
  messages: ChatMessage[],
  trustData: { scammer: number, expert: number, alertness: number },
  round: number
}
```

See [session-persistence.md](session-persistence.md) for full detail.

---

## API Contract

### Start Session
**POST** `/api/rpgv2/game-modes/start`

```json
// Request
{ "scam_type": "investment", "mode": "three_way", "victim_persona": "elderly" }

// Response
{ "session_id": "uuid", "initial_trust": { "scammer": 70, "expert": 50, "alertness": 30 } }
```

### Send Message
**POST** `/api/rpgv2/game-modes/chat`

```json
// Request
{
  "session_id": "uuid",
  "player_message": "你係邊間銀行?",
  "scam_type": "investment",
  "mode": "three_way",
  "trust_data": { "scammer": 65, "expert": 55, "alertness": 35 }
}

// Response
{
  "scammer_response": "我係恆生銀行理財部...",
  "expert_response": "請注意，合法銀行不會主動聯絡你...",
  "trust_changes": { "scammer": 3, "expert": -2, "alertness": 1 },
  "round": 4,
  "outcome": null
}
```

File: `backend/api/rpgv2_game_modes_routes.py`

---

## Game Modes

| Mode | Active Agents | Use Case |
|------|--------------|----------|
| `three_way` | Scammer + Expert | Standard play — player decides who to trust |
| `scammer_only` | Scammer only | Focused scam recognition training |
| `expert_only` | Expert only | Learning anti-fraud advice |

---

## Relevant Files

```
rpg-platform-v2/src/
  scenes/BattleScene.ts       Main battle UI — HTML overlay, chat, voice, trust
  scenes/WorldMapScene.ts     Triggers BattleScene, handles resume
  scenes/ResultScene.ts       Displays RecorderAgent post-game report
  systems/TrustSystem.ts      Frontend trust delta calculation
  ui/TrustMeter.ts            Animated trust bar component
  services/BackendClient.ts   All HTTP calls to FastAPI :8000
backend/api/
  rpgv2_game_modes_routes.py  /api/rpgv2/game-modes/* endpoints
```

---

## Related Features

- [trust-meter.md](trust-meter.md) — Trust state and outcome logic
- [voice-input.md](voice-input.md) — Web Speech API integration
- [session-persistence.md](session-persistence.md) — sessionStorage save/restore
- [parallel-generation.md](parallel-generation.md) — Scammer + Expert parallel asyncio
- [multi-agent-system.md](multi-agent-system.md) — Agent architecture
