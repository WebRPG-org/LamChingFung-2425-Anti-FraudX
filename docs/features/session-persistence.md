# Feature: Session State Persistence

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Battle session state is saved to `sessionStorage` after every interaction. If the player refreshes the page or the scene is recreated, the state is automatically restored — the player continues exactly where they left off, with all messages and trust values intact.

---

## Saved State Shape

```typescript
interface BattleState {
  session_id: string;       // Backend session UUID
  scamType: string;         // e.g. "investment"
  messages: ChatMessage[];  // Full message history
  trustData: {
    scammer: number;        // 0–100
    expert: number;         // 0–100
    alertness: number;      // 0–100
  };
  round: number;            // Current round count
}
```

Key: `battle_state` in `sessionStorage`.

---

## Save / Restore Flow

```
Every state change (send message, receive response, trust update)
  → BattleScene.saveState()
  → sessionStorage.setItem('battle_state', JSON.stringify(state))

BattleScene.create() on scene launch
  → BattleScene.tryRestoreState()
  → sessionStorage.getItem('battle_state')
  → Parse and validate:
      if saved.scamType === current.scamType:
        restore messages, trust, round, session_id
        renderAllBubbles()    ← re-render all chat bubbles
      else:
        discard (different NPC / scam type)
```

---

## Key Methods in `BattleScene.ts`

| Method | Purpose |
|--------|---------|
| `saveState()` | Serialises current state to `sessionStorage` |
| `tryRestoreState()` | Reads `sessionStorage`, restores if `scamType` matches |
| `renderAllBubbles()` | Re-renders all `messages[]` as chat bubbles after restore |
| `clearState()` | Clears `sessionStorage` on session end (win/loss) |

---

## Cross-NPC Contamination Prevention

The restore check `saved.scamType === current.scamType` prevents restoring a previous session when the player walks up to a **different NPC** (different scam type). Each NPC encounter always starts fresh if the scam type differs.

---

## Scope: sessionStorage vs localStorage

`sessionStorage` is used intentionally:
- Cleared automatically when the browser tab is closed
- Not shared across tabs
- No persistent login state needed — sessions are ephemeral by design

---

## Relevant Files

```
rpg-platform-v2/src/scenes/BattleScene.ts   saveState(), tryRestoreState(), clearState()
```

---

## Related Features

- [battle-scene.md](battle-scene.md) — BattleScene that owns session persistence
- [trust-meter.md](trust-meter.md) — Trust values included in saved state
