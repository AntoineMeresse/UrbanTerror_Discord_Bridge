import asyncio
import datetime
from typing import Any, List, Union
import discord
from lib.py3quake3 import PyQuake3
from src.ServerButtons import ServerButtons
from src.RequestObjects import DemoInfos, DiscordMessage, DiscordMessageEmbed
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import convertMessage, discordBlock, generateEmbed, generateEmbedToprun
import os

class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, urt_discord_bridge = None, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.urt_discord_bridge : UrtDiscordBridge = urt_discord_bridge
        self.interval = self.urt_discord_bridge.bridgeConfig.refresh
        if not os.path.exists('logs'):
            os.makedirs('logs')

    async def on_ready(self):
        print("----------------> Bridge Online <----------------")

    def getServInfos(self, channelId) -> str:
        for serv in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            print(f"--> {serv.discordChannelId}")
            if (serv.discordChannelId == channelId):
                return serv.mapname, serv.players
        return None,None
    
    def getRcon(self, channelId) -> PyQuake3:
        if (channelId in self.urt_discord_bridge.bridgeConfig.channelIdDict):
            return self.urt_discord_bridge.bridgeConfig.channelIdDict[channelId]
        return None
    
    def messageAuthorHasRole(self, message, roleId) -> bool:
        for role in message.author.roles:
            if (role.id == roleId):
                return True
        return False

    async def on_message(self, message : discord.Message):
        msg = message.content
        msg_channelId = message.channel.id
        if (len(msg) > 0 and msg[0] == "!"):
            s = msg.split(" ")
            cmd = s[0]
            if (cmd == "!rcon" and len(s) >= 2):
                if (self.messageAuthorHasRole(message, self.urt_discord_bridge.bridgeConfig.adminRole)):
                    args = " ".join(s[1:])
                    pyQuake3 = self.getRcon(msg_channelId)
                    if (pyQuake3 is not None):
                        author = str(message.author).split("#")[0]
                        pyQuake3.rcon(args)
                        await message.channel.send(f"{author} has sent rcon command ({args}).")
                    else:
                        await message.channel.send("Please use it in the appropriate server bridge channel.")
                else:
                    await message.channel.send("You are not an [UJM] Admin")
                return
            elif (cmd == "!restart"):
                if (self.messageAuthorHasRole(message, self.urt_discord_bridge.bridgeConfig.adminRole)):
                    pass
                else:
                    await message.channel.send("You are not an [UJM] Admin")
                return
            elif (cmd == "!help"):
                cmds = [
                    "Available commands :",
                    "   |-> !mapinfos or !mapinfo : To get map infos",
                    "   |-> !topruns : To get all runs for a given map",
                    "   |-> !top : To get only best runs for a given map",
                    "   |-> !status : To display latest server status (Only in #fliro-bridge)",
                ]
                await message.channel.send(discordBlock(cmds))
                return
            mapname = None
            players = None
            if (len(s) == 2):
                mapname : str = s[1]
                mapname = mapname.strip()
            if (mapname is None):
                mapname, players = self.getServInfos(msg_channelId)
                print(mapname)
                print(players)
            if (mapname is not None and mapname != ""):
                if (cmd in ["!topruns", "!tr"]):
                    emb = await generateEmbedToprun(mapname, bridgeConfig=self.urt_discord_bridge.bridgeConfig)
                    await message.channel.send(embed=emb)
                elif (cmd == "!top"):
                    emb = await generateEmbedToprun(mapname, allRuns=False, bridgeConfig=self.urt_discord_bridge.bridgeConfig)
                    await message.channel.send(embed=emb)
                elif (cmd == "!mapinfos" or cmd == "!mapinfo"):
                    emb = await generateEmbed(mapname, None, None, self.urt_discord_bridge.bridgeConfig)
                    await message.channel.send(embed=emb)
                elif (cmd == "!status"):
                    emb = await generateEmbed(mapname, None, players, self.urt_discord_bridge.bridgeConfig)
                    await message.channel.send(embed=emb)
        elif (message.author.bot):
            return
        else:
            author = str(message.author).split("#")[0]
            self.urt_discord_bridge.sendMessage(msg_channelId, f'[{author}]', message.content)

    def setupChannels(self) -> bool:
        cpt = 0
        for server in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            server.setChannel(self.get_channel(server.discordChannelId))
            if server.getChannel is not None:
                cpt+=1
        return cpt > 0

    async def setup_hook(self) -> None:
        print("setup_hook")
        if (len(self.urt_discord_bridge.bridgeConfig.serverAdressDict) > 0):
            self.messageTask = self.loop.create_task(self.send_message_task())
        if (self.urt_discord_bridge.bridgeConfig.demoChannelId):
            self.demoTask = self.loop.create_task(self.send_demos_task())
        if (self.urt_discord_bridge.bridgeConfig.statusChannelId):
            self.serverinfosTask = self.loop.create_task(self.set_discord_server_infos_task())
        

    async def send_message_task(self):
        await self.wait_until_ready()
        foundChannel = self.setupChannels()
        if (foundChannel):
            while not self.is_closed():
                queue = self.urt_discord_bridge.getListMessages()
                while (not queue.empty()):
                    with self.urt_discord_bridge.messagesLock:
                        currentMessage : Union[DiscordMessage, DiscordMessageEmbed] = queue.get(timeout=2)
                        channel = self.urt_discord_bridge.bridgeConfig.getChannel(currentMessage.serverAddress)
                        if (channel is not None):
                            if type(currentMessage) == DiscordMessageEmbed:
                                players = self.urt_discord_bridge.bridgeConfig.serverAdressDict[currentMessage.serverAddress].players
                                emb = await generateEmbed(currentMessage.mapname, None, players, self.urt_discord_bridge.bridgeConfig)
                                try:
                                    async with asyncio.timeout(10):
                                        await channel.send(embed=emb)
                                except asyncio.TimeoutError:
                                    with open("logs/sendEmbed_errors.txt", "a+") as fl:
                                        fl.write(f"{datetime.datetime.now()} | Error to send embed change map for : {currentMessage.mapname} (server : {currentMessage.serverAddress})\n\n") 
                            elif (type(currentMessage == DiscordMessage)):
                                msg = convertMessage(currentMessage)
                                try:
                                    async with asyncio.timeout(10):
                                        await channel.send(msg)
                                except asyncio.TimeoutError:
                                    with open("logs/sendMessage_errors.txt", "a+") as fl:
                                        fl.write(f"{datetime.datetime.now()} | Error to send message : {msg} (server : {currentMessage.serverAddress})\n\n") 
                await asyncio.sleep(self.interval)
        else:
            print("There was no valid channels found.")

    async def send_demos_task(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.demoChannelId)
        if (channel is not None):
            while not self.is_closed():
                queue = self.urt_discord_bridge.getListDemos()
                while (not queue.empty()):
                    demo : DemoInfos = queue.get(timeout=2)
                    serv_channel = self.urt_discord_bridge.bridgeConfig.getChannel(demo.serverAddress)
                    msg = demo.msg
                    if (serv_channel is not None):
                        msg += f"({serv_channel.jump_url})"
                    try:
                        async with asyncio.timeout(10):
                            post : discord.Message = await channel.send(msg, file = discord.File(fp=demo.path, filename=demo.name))
                            if (serv_channel is not None):
                                await serv_channel.send(f"{demo.chatMessage} {post.jump_url}")
                    except asyncio.TimeoutError:
                        with open("logs/sendDemoRuns_errors.txt", "a+") as fl:
                            fl.write(f"{datetime.datetime.now()} | Error uploading demo on discord : {demo}\n\n")    
                await asyncio.sleep(self.interval)
        else:
            print("Could not find channel for demos")

    async def deleteStatusMessage(self, channel : discord.TextChannel):
        messages = [message async for message in channel.history(limit=None)]
        for m in messages:
            if (m.author == self.user):
                await m.delete()
        
    async def initStatusMessage(self, channel : discord.TextChannel):
        for x in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            emb = await generateEmbed(x.mapname, None, x.players, self.urt_discord_bridge.bridgeConfig, servername=x.servername)
            x.status = await channel.send(embed=emb, content="test")
                                        #   view=ServerButtons(x.mapname, self.urt_discord_bridge.bridgeConfig))
    async def updateStatusServers(self):
        for x in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            if (x.status is not None):
                try:
                    emb = await generateEmbed(x.mapname, None, x.players, self.urt_discord_bridge.bridgeConfig, updated=datetime.datetime.now(),
                                    servername=x.servername)
                    async with asyncio.timeout(10):
                        await x.status.edit(embed=emb, view=ServerButtons(x.mapname, self.urt_discord_bridge.bridgeConfig))
                except asyncio.TimeoutError:
                    with open("logs/updateStatusServers_errors.txt", "a+") as fl:
                        fl.write(f"{datetime.datetime.now()} | Error to update map {x.mapname} ({x.address}) for messageId : {x.status.id}\n")

    async def set_discord_server_infos_task(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.statusChannelId)
        if (channel is not None):
            await self.deleteStatusMessage(channel)
            await self.initStatusMessage(channel)
            while not self.is_closed():
                await self.updateStatusServers()
                await asyncio.sleep(10) # Params
            
