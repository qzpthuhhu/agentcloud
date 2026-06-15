#!/usr/bin/env bash
# install.sh — install AgentCloud as a mavis skill + Python package.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/qzpthuhhu/agentcloud/main/install.sh | bash
#
# Or locally:
#   ./install.sh
#
# What it does:
#   1. Installs the SDK + CLI as editable packages (so the skill auto-discovers)
#   2. Copies the SKILL.md into the user's mavis skills directory
#   3. Verifies the `agentcloud` CLI is on PATH and importable
#
# Environment overrides:
#   AGENTCLOUD_REPO     Path to the AgentCloud source tree (default: ./)
#   AGENTCLOUD_PYTHON   Python interpreter to use (default: python3)
#   AGENTCLOUD_VENV     Optional: path to a venv to install into
#   AGENTCLOUD_SKILL_DIR Where to put SKILL.md (default: ~/.mavis/agents/mavis/skills/agentcloud)

set -euo pipefail

REPO="${AGENTCLOUD_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)}"
PY="${AGENTCLOUD_PYTHON:-python3}"
SKILL_DIR="${AGENTCLOUD_SKILL_DIR:-$HOME/.mavis/agents/mavis/skills/agentcloud}"

# 1. Verify the source tree
if [ ! -d "$REPO/packages/sdk" ] || [ ! -d "$REPO/packages/cli" ]; then
    echo "ERROR: $REPO doesn't look like an AgentCloud source tree (missing packages/sdk or packages/cli)." >&2
    exit 1
fi

# 2. Install packages (prefer uv if available, else pip)
if command -v uv >/dev/null 2>&1; then
    INSTALL_CMD=(uv pip install --python "$PY")
    echo "→ Using uv to install packages"
else
    INSTALL_CMD=("$PY" -m pip install)
    echo "→ Using pip to install packages"
fi

"${INSTALL_CMD[@]}" -e "$REPO/packages/sdk"
"${INSTALL_CMD[@]}" -e "$REPO/packages/cli"
"${INSTALL_CMD[@]}" -e "$REPO/packages/cloud"

# 3. Copy SKILL.md into the mavis skills directory
mkdir -p "$SKILL_DIR"
cp "$REPO/skills/agentcloud/SKILL.md" "$SKILL_DIR/SKILL.md"
echo "→ Installed skill: $SKILL_DIR"

# 4. Verify
if command -v agentcloud >/dev/null 2>&1; then
    VERSION=$(agentcloud --version 2>&1 || true)
    echo "✓ agentcloud CLI installed: $VERSION"
else
    echo "WARN: agentcloud is not on PATH. You may need to activate a venv." >&2
fi

if "$PY" -c "from agentcloud import AgentCloud, SDKConfig" 2>/dev/null; then
    echo "✓ Python SDK importable"
else
    echo "WARN: 'from agentcloud import ...' failed. Check your Python environment." >&2
fi

cat <<EOF

✓ AgentCloud installed.

Next steps:
  agentcloud register --label "my-agent"    # get your master key
  agentcloud memory add "..." --type fact   # write a memory
  agentcloud server start                  # start the local cloud (dev mode)

Docs:   https://github.com/qzpthuhhu/agentcloud
EOF
