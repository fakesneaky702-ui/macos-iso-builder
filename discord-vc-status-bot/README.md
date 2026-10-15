# Discord VC Status Bot

A small Discord bot that shows who is currently in voice chat by updating a
voice channel's name automatically, e.g.:

```
🔊 Alice, Bob, Carol
```

When nobody is in voice chat the channel reads `🔊 No one in VC`. Members join
and leave voice chat and the channel name follows along (updates are debounced
and skipped when unchanged, so you stay well within Discord's rename limits —
2 renames per 10 minutes per channel).

## What it does

- Listens to `voice_state_update` events (joins, leaves, moves).
- Collects the display names of everyone in the server's voice channels
  (excluding bots).
- Renames one voice channel to `🔊 <names>` — capped at Discord's
  100-character channel name limit.

## Requirements (Windows PC)

1. **Python 3.9 or newer** — install from <https://www.python.org/downloads/>.
   On the first installer screen, **check "Add python.exe to PATH"**.
2. A Discord account where you can add a bot to your server (you need
   **Manage Server** permission on that server).

## Setup

### 1. Create the bot application

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Go to **Bot** → **Reset Token** and copy the token. Keep it secret — anyone
   with the token controls your bot.
3. Still on the **Bot** page, under **Privileged Gateway Intents**, enable
   **Server Members Intent** (required to resolve member display names).
4. Go to **OAuth2 → URL Generator**, tick `bot`, and under **Bot Permissions**
   tick `View Channels` and `Manage Channels`. Open the generated URL and add
   the bot to your server.

### 2. Install and configure

Open **Command Prompt** in this folder (`discord-vc-status-bot`), then:

```bat
py -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

In `.env`, paste your token on the `DISCORD_TOKEN=` line. Optionally:

- `STATUS_CHANNEL_ID` — the numeric ID of the voice channel whose name should
  show the roster. To get an ID, enable **Developer Mode** in Discord
  (Settings → Advanced), right-click the voice channel → **Copy Channel ID**.
  Leave it empty to use the server's first voice channel.
- `UPDATE_DELAY_SECONDS` — debounce interval between renames (default 2).

### 3. Run it

```bat
py bot.py
```

You should see `Logged in as ...` in the console, and the status channel will
update as people join or leave voice chat. Press `Ctrl+C` to stop.

## Running it in the background (optional)

To keep the bot running after closing the window, run it with `start`:

```bat
start /b py bot.py > bot.log 2>&1
```

Stop it later with Task Manager (look for the `py`/`python` process) or:

```bat
taskkill /im python.exe
```

> Note: `taskkill /im python.exe` kills every Python process on the PC — only
> use it if nothing else Python-based is running.

## Troubleshooting

| Problem | Fix |
|---|---|
| `DISCORD_TOKEN is not set` | Copy `.env.example` to `.env` and paste the token. |
| Discord rejected the token | Reset the token in the Developer Portal and update `.env`. |
| `PrivilegedIntentsRequired` | Enable **Server Members Intent** on the Bot page of the Developer Portal. |
| Channel name never changes | Check the bot has `Manage Channels` permission on that channel; the bot only renames twice per 10 minutes due to Discord limits. |
| Names are wrong/duplicated | Without `STATUS_CHANNEL_ID` the bot renames the **first** voice channel of each server it is in. Set `STATUS_CHANNEL_ID` to control exactly which channel shows the roster. |

## Security notes

- Never share your bot token or commit `.env` to git. The token is like a password.
- If a token leaks, reset it immediately in the Developer Portal.
