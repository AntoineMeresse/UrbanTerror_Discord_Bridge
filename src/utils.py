
import datetime
import re
from typing import List
import discord

from src.ApiCalls import getMapInfo, getToprunsInfo
from src.BridgeConfig import BridgeConfig

from src.RequestObjects import DiscordMessage, Player

import zipfile
from PIL import Image

async def generateEmbed(mapname, mapinfos, players, bridgeConfig : BridgeConfig, updated : datetime = None, servername : str = "", 
                        servAvailable : bool = True, connectMessage : str = None) -> discord.Embed:
    emb = discord.Embed(
        color=discord.Color.from_str('0xff0000'),
        title=f"{servername}"
    )

    if (updated is not None):
        emb.timestamp = updated
        emb.set_footer(text='\u200b', icon_url="https://www.iconsdb.com/icons/preview/soylent-red/sinchronize-xxl.png")

    if (not servAvailable):
        emb.title = f"{servername}"
        emb.set_image(url="https://media.tenor.com/u7LmCHI89N8AAAAd/server-offline.gif")
        text = f"```yaml\nAsk someone with UJM Admin role to :\n- Go in {servername.lower()}-bridge\n- !restart\n```"
        emb.add_field(name="What to do ?", value=text)
        return emb
    else:
        if mapname is not None and mapname != "":
            emb.title = f"{servername} - {mapname}"

    if (mapinfos is None):
        mapinfos = await getMapInfo(mapname, bridgeConfig) 

    getMapInfosForEmbed(mapinfos, emb, bridgeConfig, servername)
    
    if (players is not None):
        getPlayersForEmbed(players, emb)

    if (connectMessage is not None):
        text = f"```\n{connectMessage}\n```"
        emb.add_field(name="Join this server:", value=text, inline=False)

    return emb

def getMapInfosForEmbed(mapinfo, embed : discord.Embed, bridgeConfig : BridgeConfig, servername : str = ""):
    if mapinfo:
        if (servername == ""):
            embed.title = f'{mapinfo["mapname"]}'
        else:
            embed.title = f'{servername} - {mapinfo["mapname"]}'
        url = bridgeConfig.mappageUrl.format(mapinfo['id']) 
        embed.description = f'[{mapinfo["filename"]}]({url})'
        embed.add_field(name=f'Mapper{"s" if len(mapinfo["mappers"]) > 1 else ""}:', value= " | ".join(mapinfo["mappers"]))
        embed.add_field(name="Jump number:", value=mapinfo["jnumber"])
        embed.add_field(name="Level:", value=mapinfo["level"])
        embed.add_field(name="Release Date:", value=mapinfo["releasedate"].replace(" 00:00:00 GMT", ""))
        if(len(mapinfo["types"]) > 0):
            embed.add_field(name=f'Type{"s" if len(mapinfo["types"]) > 1 else ""}:', value=" | ".join(mapinfo["types"]))
        if(len(mapinfo["notes"]) > 0):
            embed.add_field(name=f'Note{"s" if len(mapinfo["notes"]) > 1 else ""}:', value=", ".join(mapinfo["notes"]), inline=False)
        embed.set_thumbnail(url=bridgeConfig.logoUrl)
        embed.set_image(url=bridgeConfig.levelshotUrl.format(mapinfo['filename']))

def getPlayersForEmbed(players : List[Player], emb : discord.Embed):
        nbPlayers = 0
        game = list()
        spec = list()
        s = ""
        if (players is not None and len(players) > 0):
            for p in players:
                name = p.name
                if (name != "World"):
                    nbPlayers += 1
                    if (not p.ingame):
                        spec.append(name)
                    else:
                        game.append(name)
            if (nbPlayers > 1):
                s = "s"
        emb.add_field(name=f"Player{s} Online:   `{nbPlayers} / 24`", value="", inline=False)
        if(len(game) > 0):
            emb.add_field(name=f"In game:", value=f"{', '.join(game)}")
        if(len(spec) > 0):
            emb.add_field(name=f"In spec:", value=f"{', '.join(spec)}")

async def generateEmbedToprun(mapname, allRuns = True, bridgeConfig : BridgeConfig = None) -> discord.Embed:
    t = "Topruns" if allRuns else "Top"
    mapinfo = await getToprunsInfo(mapname, bridgeConfig)
    emb = discord.Embed(
        color=discord.Color.from_str('0xff0000'),
        title=f"{t} - {mapinfo['mapname']}"
    )
    emb.set_thumbnail(url=bridgeConfig.logoUrl)
    space = "\u1CBC\u1CBC[...]"
    if mapinfo:
        url = bridgeConfig.mappageUrl.format(mapinfo['mapid'])
        emb.description = f'[{mapinfo["mapfilename"]}]({url})'
        runs = mapinfo["runs"]
        runsNumber = len(runs)
        emb.add_field(name=f"Number of ways : {runsNumber}",value="")
        emb.set_image(url=bridgeConfig.levelshotUrl.format(mapinfo['mapfilename']))
        if (len(runs) > 0):
            for x in runs:
                tmp = ""
                i = 1
                r = runs[x]
                if not allRuns:
                    r = r[:1]
                for time in r:
                    if (i == 1):
                        place = ":first_place:"
                    elif (i == 2):
                        place = ":second_place:"
                    elif (i == 3):
                        place = ":third_place:"
                    else:
                        place = f"<:rafiqz:1095672297643319316>"
                    r = f'{place} {time["time"]} | {time["rundate"]} | {time["playername"]}\n'
                    if ((len(tmp) + len(r)) < (1023 - len(space))):
                        tmp += r
                    else:
                        tmp += space
                        break
                    i+=1
                emb.add_field(name=f"Way {x}", value=tmp, inline=False)
    return emb

def decolorstring(string):
    return re.sub('\^\d', '', string)

def discordBlock(elems : List[str]) -> str:
    res_string = '\n'.join(elems)
    return f"```{res_string}```"

def convertMessage(discordMessage : DiscordMessage) -> str:
    team = discordMessage.team
    prefix = team if (team is not None) else ""
    return decolorstring(f"{prefix}{discordMessage.message}")

def getProgressiveImages(file) -> list[str]:
    res = list()
    pk3 = zipfile.ZipFile(file)
    files = pk3.infolist()
    for f in files:
        if not f.is_dir() and not f.filename.endswith((".bsp", ".map", ".shader")):
            try:
                currentFile = pk3.open(f)
                img = Image.open(currentFile)
                if "progressive" in img.info: 
                    res.append(f.filename)
            except:
                pass
    return res
