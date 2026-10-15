"""Voice status cog: mirrors current voice-channel occupants into a
channel's name, updating automatically as people join and leave.

Rename behavior and rate limits:
- Discord allows only 2 channel-name edits per 10 minutes per channel.
  Updates are debounced (UPDATE_DELAY_SECONDS) and skipped when the name
  would not change, so real changes still go through as soon as the
  limit allows.
- Discord caps channel names at 100 characters; long member lists are
  truncated.
"""

import logging
import os
from typing import Optional, Tuple

import discord
from discord.ext import commands, tasks

log = logging.getLogger("vcstatus.voice")

EMPTY_LABEL = "No one in VC"
NAME_LIMIT = 100


class VoiceStatusCog(commands.Cog):
    def __init__(self, bot: discord.Client) -> None:
        self.bot = bot
        self.status_channel_id = _int_env("STATUS_CHANNEL_ID")
        self._pending = None  # type: Optional[Tuple[discord.Guild, discord.VoiceChannel]]
        self._last_name = None  # type: Optional[str]
        self._warned_missing = False
        self.update_channel_name.change_interval(
            seconds=max(1, _int_env("UPDATE_DELAY_SECONDS", "2") or 2)
        )
        self.update_channel_name.start()

    async def cog_unload(self) -> None:
        self.update_channel_name.cancel()

    @tasks.loop(seconds=2)
    async def update_channel_name(self) -> None:
        """Coalesce pending voice updates into at most one rename."""
        pending = self._pending
        if pending is None:
            return
        guild, channel = pending
        self._pending = None
        new_name = self._build_name(guild)
        if new_name is None or new_name == self._last_name:
            return
        try:
            await channel.edit(name=new_name)
        except discord.HTTPException as exc:
            log.warning("Rename failed for channel %s: %s", channel.id, exc)
            return
        self._last_name = new_name
        log.info("Renamed channel %s to %r", channel.id, new_name)

    @update_channel_name.before_loop
    async def before_update(self) -> None:
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot:
            return
        # Compare IDs: channel objects do not define value equality.
        before_id = before.channel.id if before.channel else None
        after_id = after.channel.id if after.channel else None
        if before_id == after_id:
            return  # mute/deafen/stream changes do not affect the roster

        channel = self._resolve_channel(after.channel or before.channel)
        if channel is None:
            return
        self._pending = (channel.guild, channel)

    def _resolve_channel(self, hint):
        # type: (Optional[discord.VoiceChannel]) -> Optional[discord.VoiceChannel]
        """Find the status channel: the configured one, or the first voice
        channel of the guild the event came from."""
        guild = hint.guild if hint else None
        if guild is None:
            guild = next(iter(self.bot.guilds), None)
            if guild is None:
                return None

        if self.status_channel_id:
            channel = guild.get_channel(self.status_channel_id)
            if isinstance(channel, discord.VoiceChannel):
                return channel
            # Do not fall back here: the event may come from another server
            # and we must not rename an unrelated channel there.
            if not self._warned_missing:
                self._warned_missing = True
                log.warning(
                    "STATUS_CHANNEL_ID %s was not found as a voice channel in "
                    "guild %s (bot may be in multiple servers). No updates "
                    "will be made until it points at a valid voice channel.",
                    self.status_channel_id,
                    guild.id,
                )
            return None
        return guild.voice_channels[0] if guild.voice_channels else None

    def _build_name(self, guild):
        # type: (discord.Guild) -> Optional[str]
        names = [
            member.display_name
            for vc in guild.voice_channels
            for member in vc.members
            if not member.bot
        ]
        if names:
            base = "\U0001f50a " + ", ".join(names)
        else:
            base = "\U0001f50a " + EMPTY_LABEL
        return base[:NAME_LIMIT]


def _int_env(key, default=None):
    # type: (str, Optional[str]) -> Optional[int]
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return int(default) if default is not None else None
    try:
        return int(raw.strip())
    except ValueError:
        log.warning("%s=%r is not an integer; ignoring.", key, raw)
        return None
