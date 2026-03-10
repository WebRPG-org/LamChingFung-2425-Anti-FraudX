# Feature: Personal Chat Mode

> Category: Secondary | Version: 4.1 | Last Updated: 2026-03-11

---

## Overview

A standalone **one-on-one chat interface** outside the RPG game. Users talk directly with a single AI agent (scammer or expert) for focused educational practice — no game mechanics, no trust meter, no NPC interactions.

---

## Interface

File: `frontend/personal_chat.html`

- Plain HTML/JS chat UI served by FastAPI
- Accessible at `/personal-chat` (via `frontend_routes.py`)
- Single-agent conversation — user selects scammer or expert at start
- No session persistence across page refreshes (by design — lightweight mode)

---

## API

File: `backend/api/personal_chat_routes.py`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/personal-chat/start` | Start a new personal chat session |
| POST | `/api/personal-chat/message` | Send message, receive agent response |
| DELETE | `/api/personal-chat/end` | End session and clear history |

---

## Relevant Files

```
backend/api/personal_chat_routes.py   REST API
frontend/personal_chat.html           Chat UI
```

---

## Related Features

- [multi-agent-system.md](multi-agent-system.md) — Agents used in personal chat
- [battle-scene.md](battle-scene.md) — Full RPG battle mode (vs personal chat)
