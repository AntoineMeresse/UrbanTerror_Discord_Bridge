from typing import Optional, Union
import discord
from lib.py3quake3 import PyQuake3

class UrtDiscordServer():

    def __init__(self, discordChannelId : int = None) -> None:
        self.discordChannelId = discordChannelId
        self.channel : Optional[Union[discord.GuildChannel, discord.Thread, discord.PrivateChannel]] = None

    def setChannel(self, channel):
        self.channel = channel

    def getChannel(self):
        return self.channel

    def __str__(self) -> str:
        return f"{self.discordChannelId} | {self.channel}"