#!/usr/bin/env bash
# garmin-workouts install script
# Creates the Python venv, installs deps, and builds a ready-to-install .plugin file.

set -euo pipefail

# ── Colours ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo ""
echo "  garmin-workouts plugin installer"
echo "  ================================"
echo ""

# ── 1. Check Python 3.12 ──────────────────────────────────────────────────────
if ! command -v python3.12 &>/dev/null; then
  error "python3.12 not found. Install it from https://www.python.org/downloads/macos/ and re-run."
fi
info "Python 3.12 found: $(python3.12 --version)"

# ── 2. Create / update venv ───────────────────────────────────────────────────
VENV="$HOME/.garmin-venv"
if [ ! -d "$VENV" ]; then
  info "Creating venv at $VENV …"
  python3.12 -m venv "$VENV"
else
  info "Venv already exists at $VENV"
fi

info "Installing / upgrading dependencies …"
"$VENV/bin/pip" install --quiet --upgrade "mcp[cli]" garminconnect pydantic
info "Dependencies ready."

# ── 3. Copy MCP server to a stable location ───────────────────────────────────
INSTALL_DIR="$HOME/.garmin-workouts"
mkdir -p "$INSTALL_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/garmin_workouts_mcp.py" "$INSTALL_DIR/garmin_workouts_mcp.py"
info "MCP server copied to $INSTALL_DIR/garmin_workouts_mcp.py"

# ── 4. Generate .mcp.json with paths for THIS user ───────────────────────────
cat > "$SCRIPT_DIR/.mcp.json" <<MCPJSON
{
  "mcpServers": {
    "garmin-workouts": {
      "command": "$VENV/bin/python",
      "args": ["$INSTALL_DIR/garmin_workouts_mcp.py"]
    }
  }
}
MCPJSON
info ".mcp.json written with your paths."

# ── 5. Build the .plugin file (zip) ──────────────────────────────────────────
PLUGIN_OUT="$SCRIPT_DIR/garmin-workouts.plugin"
rm -f "$PLUGIN_OUT"
cd "$SCRIPT_DIR"

zip -qr "$PLUGIN_OUT" \
  .claude-plugin/ \
  .mcp.json \
  garmin_workouts_mcp.py \
  skills/ \
  README.md

info "Plugin file built: $PLUGIN_OUT"

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "  Next step:"
echo "  Open 'garmin-workouts.plugin' in Claude — click 'Install plugin'."
echo ""
echo "  Requirements:"
echo "  • The Garmin MCP connector must be connected in Claude Settings → Connectors"
echo "    (it creates ~/.garth tokens that this plugin reuses)."
echo ""
