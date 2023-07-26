from typing import List, Optional, Union
import discord
from src.RequestObjects import Player

class UrtDiscordServer():

    def __init__(self, address : str, discordChannelId : int) -> None:
        self.address : str = address
        self.discordChannelId = discordChannelId
        
        self.channel : Optional[Union[discord.GuildChannel, discord.Thread, discord.PrivateChannel]] = None
        
        self.mapname : str = None
        self.players : List[Player] = list()

    def setChannel(self, channel):
        self.channel = channel

    def getChannel(self):
        return self.channel

    def __str__(self) -> str:
        res = "```"
        res += f"{self.address} | {self.discordChannelId} | {self.channel} | {self.mapname}"
        res += "\nPlayers : "
        for p in self.players:
            res += f"\n   ----> {p}"
        res += "```"
        return res