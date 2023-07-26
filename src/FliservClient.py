import asyncio
from typing import Any, Union
import discord
from src.RequestObjects import DemoInfos, DiscordMessage, DiscordMessageEmbed
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import convertMessage, discordBlock, generateEmbed, generateEmbedToprun

class FliservClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, urt_discord_bridge = None, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.urt_discord_bridge : UrtDiscordBridge = urt_discord_bridge
        self.interval = self.urt_discord_bridge.bridgeConfig.refresh

    async def on_ready(self):
        print("----------------> Bridge Online <----------------")

    async def on_message(self, message : discord.Message):
        msg = message.content
        msg_channelId = message.channel.id
        if (len(msg) > 0 and msg[0] == "!"):
            s = msg.split(" ")
            cmd = s[0]
            mapname = None
            if (len(s) == 2):
                mapname = s[1]
            if (not cmd in ["!topruns", "!mapinfos", "!mapinfo", "!top", "!status", "!help"]):
                return
            if (mapname is None):
                pass
                # Voir en fonction du channelId
            if (cmd == "!topruns"):
                emb = generateEmbedToprun(mapname, bridgeConfig=self.urt_discord_bridge.bridgeConfig)
                await message.channel.send(embed=emb)
            elif (cmd == "!top"):
                emb = generateEmbedToprun(mapname, allRuns=False, bridgeConfig=self.urt_discord_bridge.bridgeConfig)
                await message.channel.send(embed=emb)
            elif (cmd == "!mapinfos" or cmd == "!mapinfo"):
                emb = generateEmbed(mapname, None, None, self.urt_discord_bridge.bridgeConfig)
                await message.channel.send(embed=emb)
            # if (cmd == "!status" and message.channel.id == self.channelId):
            #     emb = self.urt_discord_bridge.generateEmbedWithCurrentInfos()
            #     await message.channel.send(embed=emb)
            elif (cmd == "!help"):
                cmds = [
                    "Available commands :",
                    "   |-> !mapinfos or !mapinfo : To get map infos",
                    "   |-> !topruns : To get all runs for a given map",
                    "   |-> !top : To get only best runs for a given map",
                    "   |-> !status : To display latest server status (Only in #fliro-bridge)",
                ]
                await message.channel.send(discordBlock(cmds))
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
            # self.serverinfosTask = self.loop.create_task(self.set_discord_server_infos_task())
        if (self.urt_discord_bridge.bridgeConfig.demoChannelId):
            self.demoTask = self.loop.create_task(self.send_demos_task())
        

    async def send_message_task(self):
        await self.wait_until_ready()
        foundChannel = self.setupChannels()
        if (foundChannel):
            while not self.is_closed():
                queue = self.urt_discord_bridge.getListMessages()
                while (not queue.empty()):
                    print(f"Queue size : {queue.qsize()}")
                    with self.urt_discord_bridge.messagesLock:
                        currentMessage : Union[DiscordMessage, DiscordMessageEmbed] = queue.get(timeout=2)
                        channel = self.urt_discord_bridge.bridgeConfig.getChannel(currentMessage.serverAddress)
                        if (channel is not None):
                            if type(currentMessage) == DiscordMessageEmbed:
                                await channel.send(embed=currentMessage.embed)
                            elif (type(currentMessage == DiscordMessage)):
                                await channel.send(convertMessage(currentMessage))
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
                    print(msg)
                    post : discord.Message = await channel.send(msg, file = discord.File(fp=demo.path, filename=demo.name))
                    if (serv_channel is not None):
                        await serv_channel.send(f"{demo.chatMessage} -> {post.jump_url}")
                await asyncio.sleep(self.interval)
        else:
            print("Could not find channel for demos")
