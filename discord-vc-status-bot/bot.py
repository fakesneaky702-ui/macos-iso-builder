"""Entry point for the Discord VC status bot.

Reads configuration from a .env file (or the environment), builds the bot,
loads the voice status cog, and starts the client.
"""

import asyncio
import logging
import os

import discord
from dotenv import load_dotenv

from voice_status import VoiceStatusCog

log = logging.getLogger("vcstatus")


def build_intents() -> discord.Intents:
    intents = discord.Intents.none()
    intents.guilds = True          # needed to see channels
    intents.voice_states = True    # needed for join/leave events
    intents.members = True         # needed to resolve member names (privileged)
    return intents


class VCStatusBot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=build_intents())

    async def setup_hook(self) -> None:
        await self.add_cog(VoiceStatusCog(self))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id %s)", self.user, self.user.id)


async def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "DISCORD_TOKEN is not set. Copy .env.example to .env and paste "
            "your bot token from the Discord Developer Portal."
        )

    bot = VCStatusBot()
    try:
        await bot.start(token)
    except discord.errors.LoginFailure:
        raise SystemExit("Discord rejected the token. Check DISCORD_TOKEN in .env.")
    except discord.errors.PrivilegedIntentsRequired:
        raise SystemExit(
            "The bot is missing privileged intents. Enable 'Server Members "
            "Intent' for this application in the Developer Portal "
            "(Bot -> Privileged Gateway Intents), then restart."
        )


if __name__ == "__main__":
    load_dotenv()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
