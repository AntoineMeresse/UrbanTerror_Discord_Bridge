from typing import List, Optional, Union
import discord
from src.RequestObjects import Player

class UrtDiscordServer():

    def __init__(self, address : str, discordChannelId : int, servername : str = "Server", rconpassword : str = "", domain : str = None) -> None:
        self.address : str = address
        self.displayedAddress : str = domain if domain is not None else address
        self.rconpassword = rconpassword
        self.discordChannelId = discordChannelId
        
        self.channel : Optional[Union[discord.GuildChannel, discord.Thread, discord.PrivateChannel]] = None
        
        self.servername : str = servername
        self.mapname : str = None
        self.players : List[Player] = list()

        # Status
        self.status : discord.Message = None

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
    
    def get_infos(self):
        ingame = [x.name for x in self.players if x.ingame]
        spec = [x.name for x in self.players if not x.ingame]
        nbPlayers = len(self.players)
        return {
            self.servername : {
                "mapname" : self.mapname,
                "nbPlayers" : nbPlayers,
                "ingame" : ingame,
                "spec" : spec
            }
        }