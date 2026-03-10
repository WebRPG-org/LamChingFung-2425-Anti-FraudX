# Feature: Voice Input (Web Speech API)

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

Players can **speak their messages** in the battle scene instead of typing. The browser's built-in Web Speech API handles recognition. Cantonese (`zh-HK`) is the primary language, with auto-stop on silence.

---

## Implementation

File: `rpg-platform-v2/src/scenes/BattleScene.ts`

```typescript
const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const recognition = new SpeechRecognition();
recognition.lang = 'zh-HK';           // Cantonese
recognition.continuous = false;        // Stop after one utterance
recognition.interimResults = true;     // Show partial text while speaking

recognition.onresult = (event) => {
  const transcript = Array.from(event.results)
    .map(r => r[0].transcript).join('');
  inputBox.value = transcript;          // Fill input box in real-time
};

recognition.onend = () => {
  // Auto-triggered after ~2s of silence
  if (inputBox.value.trim()) submitMessage();
};
```

---

## User Flow

1. Player clicks the microphone button in BattleScene
2. Browser requests microphone permission (first time only)
3. Partial transcript appears in the input box as player speaks
4. After ~2 seconds of silence, recognition stops automatically
5. If input box is non-empty, message is submitted automatically
6. Player can also click send manually before the silence timeout

---

## Requirements

| Requirement | Detail |
|-------------|--------|
| Protocol | HTTPS or `localhost` (browser security requirement) |
| Browser | Chrome or Edge (best support); Firefox has limited support |
| Permission | Microphone access must be granted by user |
| Language | `zh-HK` (Cantonese); can be changed in code for other locales |

---

## Limitations

- Not available in Safari on macOS/iOS
- Recognition accuracy varies with background noise
- No server-side processing — entirely browser-native
- No fallback if `window.SpeechRecognition` is undefined (feature is silently disabled)

---

## Relevant Files

```
rpg-platform-v2/src/scenes/BattleScene.ts   Voice input logic (search: SpeechRecognition)
```

---

## Related Features

- [battle-scene.md](battle-scene.md) — BattleScene that hosts voice input
