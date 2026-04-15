# garmin-workouts — Claude Plugin

Create, schedule and manage structured running workouts on **Garmin Connect** using natural language inside Claude (Cowork or Claude Code).

> **Example:** "Create an easy 8km run in HR zone 2 and schedule it for tomorrow"  
> Claude builds the full structured workout and pushes it straight to your Garmin calendar.

---

## What you get

| Capability | Description |
|---|---|
| Create workouts | Easy runs, tempo, intervals, long runs — just describe in plain language |
| Schedule to calendar | Push workout to a specific date on Garmin Connect |
| List saved workouts | See all workouts with IDs |
| Delete workouts | Remove workouts from Garmin Connect |

Supports: warmup / cooldown, HR zone targets, repeat intervals (e.g. 5×1km), time-based and distance-based steps.

---

## Requirements

- macOS (tested on macOS 14+)
- Python 3.12 (`python3.12 --version` to check — install via [python.org](https://www.python.org/downloads/) if missing)
- Claude desktop app (Cowork mode) with the **Garmin MCP connector** connected

---

## Installation

### Step 1 — Connect the Garmin MCP Connector in Claude

In Claude → Settings → Connectors → find **Garmin** → connect with your Garmin account credentials.

This creates `~/.garth` OAuth tokens that this plugin reuses. Without this step the plugin won't work.

### Step 2 — Run the install script

```bash
curl -fsSL https://raw.githubusercontent.com/bvg123/garmin-workouts/main/install.sh | bash
```

Or manually:

```bash
# 1. Clone the repo
git clone https://github.com/bvg123/garmin-workouts.git
cd garmin-workouts

# 2. Run install
bash install.sh
```

The script will:
- Create a Python venv at `~/.garmin-venv`
- Install all dependencies (`mcp[cli]`, `garminconnect`, `pydantic`)
- Copy the MCP server to `~/.garmin-workouts/garmin_workouts_mcp.py`
- Build a ready-to-install `garmin-workouts.plugin` file in the current folder

### Step 3 — Install the plugin in Claude

Open the `garmin-workouts.plugin` file — Claude will show an **Install plugin** button. Click it.

Done! Restart Claude if needed.

---

## Usage examples

```
Create an easy run 8km in zone 2 and schedule it for tomorrow
```
```
Make a tempo run 10km for Saturday
```
```
Build an interval session: 5×1km in zone 4 with 400m recovery, schedule for Friday
```
```
Long run 90 minutes in zone 2
```
```
Show me all my saved workouts
```
```
Delete workout 12345678
```

---

## How it works

This plugin provides an MCP server (`garmin_workouts_mcp.py`) that:
1. Reads your Garmin OAuth tokens from `~/.garth` (created by the main Garmin MCP connector)
2. Translates structured workout parameters into the Garmin Connect API format
3. Uploads the workout and optionally schedules it on the calendar

The `create-garmin-workout` skill teaches Claude how to parse natural language workout descriptions and map them to the correct API parameters (HR zones, step types, distances, durations).

---

## Updating

To get the latest version:

```bash
cd garmin-workouts
git pull
bash install.sh
```

Then reinstall the updated `.plugin` file in Claude.

---

## Troubleshooting

**"No saved Garmin session found at ~/.garth"**  
→ Reconnect the Garmin MCP connector in Claude Settings.

**"Failed to authenticate with saved tokens"**  
→ The tokens may have expired. Reconnect the Garmin MCP connector to refresh them.

**"python3.12: command not found"**  
→ Install Python 3.12 from [python.org](https://www.python.org/downloads/macos/).

**Plugin not appearing after install**  
→ Restart the Claude desktop app.
