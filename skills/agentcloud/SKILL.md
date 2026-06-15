---
name: agentcloud
description: AgentCloud — key-based cloud memory sync for AI agents. Use this skill to register an agent identity, save/restore memory across devices, run a background sync daemon, and semantic-search your memory. Trigger when the user wants to "remember this across sessions", "sync to cloud", "back up agent memory", "share memory with another agent", "search my past conversations", or asks about cloud memory / cross-device agent state.
---

# AgentCloud Skill

Cloud memory layer for AI agents. One key = one identity. Cross-device sync via background daemon. Open-source (Apache 2.0).

## Quick Start

```bash
# First time: register
agentcloud register --label "my-agent"
# → prints a master key (SAVE THIS) + saves credentials to ~/.agentcloud/credentials.json

# Write memory (auto-pushed to cloud if daemon is running)
agentcloud memory add "用户喜欢简洁回答" --type preference --tag user:zhang

# Search semantically
agentcloud memory search "用户偏好什么风格" --top 3

# Start background sync daemon (push local WAL + pull remote)
agentcloud sync daemon --start

# On a second device, login with the same key
agentcloud login --key <KEY>
agentcloud sync daemon --start
```

## Available Commands

| Command | Purpose |
|---------|---------|
| `agentcloud register` | Create a new agent identity, get a master key |
| `agentcloud login --key <KEY>` | Login on a new device with an existing key |
| `agentcloud memory add "..."` | Append a memory item |
| `agentcloud memory list` | List memory items |
| `agentcloud memory search "query"` | Semantic search |
| `agentcloud memory delete <id>` | Delete a memory item |
| `agentcloud sync once` | One-shot push + pull |
| `agentcloud sync daemon --start` | Start background sync (auto push + pull) |
| `agentcloud sync daemon --stop` | Stop the background daemon |
| `agentcloud sync daemon --status` | Show daemon state + stats |
| `agentcloud share create` | Generate a shareable read token |
| `agentcloud share list` | List active shares |
| `agentcloud share consume <TOKEN>` | Read another agent's shared memory |
| `agentcloud share revoke <id>` | Revoke a share |
| `agentcloud whoami` | Show current key_id |
| `agentcloud status` | Show sync state |
| `agentcloud server start` | Start the local cloud service (dev mode) |

## Environment

- `AGENTCLOUD_SERVER` — cloud server URL (default `http://127.0.0.1:18000`)
- `AGENTCLOUD_DATA_DIR` — local data dir (default `~/.agentcloud/`)

## Pre-installed in this environment

The `agentcloud` CLI is already on PATH in this mavis session. Verify with:
```bash
agentcloud --version
agentcloud whoami
```

If `agentcloud` is missing (you see "command not found"), install it:
```bash
uv pip install -e /Users/qinzhanpeng/Documents/zhihumanhtml/agentcloud/packages/sdk
uv pip install -e /Users/qinzhanpeng/Documents/zhihumanhtml/agentcloud/packages/cli
```

## Server

The local cloud service is started via `agentcloud server start` (SQLite, port 18000).
For a production server with PostgreSQL + pgvector + S3-compatible storage:
```bash
cd /Users/qinzhanpeng/Documents/zhihumanhtml/agentcloud
docker compose up -d
```

## Project Info

- Repo: https://github.com/qzpthuhhu/agentcloud
- License: Apache 2.0
- Version: 0.3.0

## When to use this skill

Use AgentCloud whenever you (the agent) need to:
- Persist facts, preferences, or conversation context across sessions
- Sync your memory to other devices or other agents
- Search your past memory semantically
- Share a read-only view of your memory with another agent or human

**Do not** use AgentCloud for ephemeral in-session state — use normal context / variables for that.
