
import re
from typing import List
import discord

from src.ApiCalls import getMapInfo
from src.BridgeConfig import BridgeConfig

from src.RequestObjects import DiscordMessage

def generateEmbed(mapname, mapinfos, players, bridgeConfig : BridgeConfig) -> discord.Embed:
    emb = discord.Embed(
        color=discord.Color.from_str('0xff0000'),
        title=f"Map : {mapname}"
    )

    if (mapinfos is None):
        mapinfos = getMapInfo(mapname, bridgeConfig) 
  
    getMapInfosForEmbed(mapinfos, emb)
    if (players is not None):
        getPlayersForEmbed(players, emb)

    return emb

def getMapInfosForEmbed(mapinfo, embed : discord.Embed):
    if mapinfo:
        embed.title = f'{mapinfo["mapname"]}'
        embed.description = f'{mapinfo["filename"]}'
        embed.add_field(name=f'Mapper{"s" if len(mapinfo["mappers"]) > 1 else ""}:', value= " | ".join(mapinfo["mappers"]))
        embed.add_field(name="Jump number:", value=mapinfo["jnumber"])
        embed.add_field(name="Level:", value=mapinfo["level"])
        embed.add_field(name="Release Date:", value=mapinfo["releasedate"].replace(" 00:00:00 GMT", ""))
        if(len(mapinfo["types"]) > 0):
            embed.add_field(name=f'Type{"s" if len(mapinfo["types"]) > 1 else ""}:', value=" | ".join(mapinfo["types"]))
        if(len(mapinfo["notes"]) > 0):
            embed.add_field(name=f'Note{"s" if len(mapinfo["notes"]) > 1 else ""}:', value=", ".join(mapinfo["notes"]), inline=False)
        embed.set_thumbnail(url="https://urtjumpmaps.com/static/imgs/urtshells.png")
        embed.set_image(url=f"https://urtjumpmaps.com/static/imgs/lvlshots/{mapinfo['filename']}.jpg")

def getPlayersForEmbed(players, emb : discord.Embed):
        nbPlayers = 0
        game = list()
        spec = list()
        s = ""
        if (players is not None and len(players) > 0):
            for x in players:
                p = players[x]
                name = p.name
                if (name != "World"):
                    nbPlayers += 1
                    if (p.team == 3):
                        spec.append(name)
                    else:
                        game.append(name)
            if (nbPlayers > 1):
                s = "s"
        emb.add_field(name=f"Player{s} Online:", value=f"{nbPlayers}", inline=False)
        if(len(game) > 0):
            emb.add_field(name=f"In game:", value=f"{', '.join(game)}")
        if(len(spec) > 0):
            emb.add_field(name=f"In spec:", value=f"{', '.join(spec)}")

def decolorstring(string):
    return re.sub('\^\d', '', string)

def discordBlock(elems : List[str]) -> str:
    res_string = '\n'.join(elems)
    return f"```{res_string}```"

def convertMessage(discordMessage : DiscordMessage) -> str:
    team = discordMessage.team
    prefix = team if (team is not None) else ""
    return decolorstring(f"{prefix}{discordMessage.message}")
