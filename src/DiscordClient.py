import asyncio
import datetime
import os
import subprocess
import discord
from discord.ext import tasks
import zipfile

from typing import Any, Union
from lib.py3quake3 import PyQuake3
from src.ServerButtons import ServerButtons
from src.RequestObjects import DemoInfos, DiscordMessage, DiscordMessageEmbed
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import convertMessage, discordBlock, generateEmbed, generateEmbedToprun
from src.ApiCalls import getServerStatus

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
    
    def getRestart(self, channelId) -> str:
        if (channelId in self.urt_discord_bridge.bridgeConfig.restartWithChannelId):
            return self.urt_discord_bridge.bridgeConfig.restartWithChannelId[channelId]
        return None
    
    def messageAuthorHasRole(self, message, roleId) -> bool:
        for role in message.author.roles:
            if (role.id == roleId):
                return True
        return False
    
    async def on_message_handle_commands(self, message: discord.Message, msg, msg_channelId):
        s = msg.split(" ")
        cmd : str = s[0]
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
                restart_cmd = self.getRestart(msg_channelId)
                if (restart_cmd is not None):
                    subprocess.Popen(restart_cmd, preexec_fn=os.setpgrp)
                    statusChannel = self.get_channel(self.urt_discord_bridge.bridgeConfig.statusChannelId)
                    restart_message = "Server restarted."
                    if (statusChannel is not None):
                        url = statusChannel.jump_url
                        if (url):
                            restart_message = f"Server restarted. Check status in {url}"
                    await message.channel.send(restart_message)                        
                else:
                    await message.channel.send("No restart command provided for this server.")
            else:
                await message.channel.send("You are not an [UJM] Admin")
            return
        # elif (cmd.lower() == "!resetstatus"):
        #     if (self.messageAuthorHasRole(message, self.urt_discord_bridge.bridgeConfig.adminRole)):
        #         await self.restartStatus(message)
        # elif (cmd.lower() == "!resetbridges"):
        #     if (self.messageAuthorHasRole(message, self.urt_discord_bridge.bridgeConfig.adminRole)):
        #          await self.restartBridges(message)
        elif (cmd == "!help"):
            cmds = [
                "Available commands :",
                "Everyone :"
                "   |-> !mapinfos or !mapinfo : To get map infos",
                "   |-> !topruns, !tr : To get all runs for a given map",
                "   |-> !top : To get only best runs for a given map",
                "   |-> !status : To display latest server status (Only in server bridges)",
                "[UJM] Admins :",
                "   |-> !restart : Restart the server and bot (Only in server bridges)",
                # "   |-> !resetbridges : Try to reset bridges messages", 
                # "   |-> !resetstatus : Try to reset status channel", 
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

    async def on_message_handle_fileUpload(self, message: discord.Message, msg_channelId):
        if (msg_channelId == self.urt_discord_bridge.bridgeConfig.mapUploadChannelId):
            attachements = message.attachments
            msg = message.content
            if (len(attachements) > 0):
                for uploadedFile in attachements:
                    filename = uploadedFile.filename
                    if (filename.endswith(".pk3")): 
                        path = f"{self.urt_discord_bridge.bridgeConfig.mapfolder}/{filename}"
                        file_exists = os.path.isfile(path)
                        replace = "replace" in msg.lower()
                        if (file_exists and not replace):
                            await message.channel.send(f"{filename} is already on the repository.```yaml\nIf you want to replace it :\n - Upload it again with 'replace' in the message\n```") 
                        else:
                            await uploadedFile.save(path)
                            with zipfile.ZipFile(path, 'r') as zip_file:
                                file_list = zip_file.namelist()
                                bspname = filename.replace(".pk3", ".bsp")
                                bsppath = f"maps/{bspname}"
                                if (bsppath in file_list):
                                    url = f"http://{self.urt_discord_bridge.bridgeConfig.ws_url}/q3ut4/{filename}"
                                    if (replace):
                                        await message.channel.send(f"{filename} has been updated. Donwload link : {url}") 
                                    else:
                                        await message.channel.send(f"{filename} has been successfuly uploaded. Donwload link : {url}") 
                                else:
                                    file_exists = os.path.isfile(path)
                                    if file_exists:
                                        os.remove(path)
                                    await message.channel.send(f"{filename} has not been uploaded.\n`{bsppath}` missing inside the pk3.") 
                    else:
                        await message.channel.send("Please provide a pk3 file")
            else:
                if not message.author.bot:
                    s = msg.split(" ")
                    if len(s) >= 2: 
                        cmd : str = s[0]
                        filename : str = s[1]
                        if (cmd.lower() == "!delete"):
                            path = f"{self.urt_discord_bridge.bridgeConfig.mapfolder}/{filename}"
                            file_exists = os.path.isfile(path)
                            if file_exists:
                                os.remove(path)
                                await message.channel.send(f"{filename} has been deleted.")
                                return
                            else:
                                await message.channel.send(f"{filename} doesn't exist.")  
                    await message.channel.send("Please specify a mapname. (example : `!delete ut4_example.pk3`)")

                    
    async def on_message(self, message : discord.Message):
        msg = message.content
        msg_channelId = message.channel.id
        
        await self.on_message_handle_fileUpload(message, msg_channelId)

        if (len(msg) > 0 and msg[0] == "!"):
            await self.on_message_handle_commands(message, msg, msg_channelId)
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
            self.set_discord_server_infos_task.start()
        
    # async def restartStatus(self, message: discord.Message) -> None:
    #     if (self.serverinfosTask):
    #         try:
    #             cancel = self.serverinfosTask.cancel()
    #             await message.channel.send(f"Status was cancel : {cancel}")
    #             if (cancel):
    #                 self.serverinfosTask = self.loop.create_task(self.set_discord_server_infos_task())
    #                 # await message.delete()
    #             else:
    #                 await message.channel.send("[Debug] It was not possible to cancel the current task.")
    #         except:
    #             await message.channel.send("[Debug] Couldn't restart status")
    #     else:
    #         await message.channel.send("[Debug] There was no task. Starting a new one.")
    #         self.serverinfosTask = self.loop.create_task(self.set_discord_server_infos_task())

    # async def restartBridges(self, message: discord.Message) -> None:
    #     if (self.messageTask):
    #         try:
    #             cancel = self.messageTask.cancel()
    #             await message.channel.send(f"Bridge was cancel : {cancel}")
    #             if (cancel):
    #                 self.messageTask = self.loop.create_task(self.send_message_task())
    #                 # await message.delete()
    #             else:
    #                 await message.channel.send("[Debug] It was not possible to cancel the current task.")
    #         except:
    #             await message.channel.send("[Debug] Couldn't restart bridges")
    #     else:
    #         await message.channel.send("[Debug] There was no task. Starting a new one.")
    #         self.messageTask = self.loop.create_task(self.send_message_task())

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
            emb = await generateEmbed(x.mapname, None, x.players, self.urt_discord_bridge.bridgeConfig, servername=x.servername, servAvailable=False)
            x.status = await channel.send(embed=emb)
                                      
    async def updateStatusServers(self):
        for serv in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            if (serv.status is not None):
                try:
                    async with asyncio.timeout(10):
                        available = await getServerStatus(self.urt_discord_bridge.bridgeConfig.ws_url,serv.address)
                        emb = await generateEmbed(serv.mapname, None, serv.players, self.urt_discord_bridge.bridgeConfig, updated=datetime.datetime.now(),
                                    servername=serv.servername, servAvailable=available, connectMessage=f"/connect {serv.address}")
                        await serv.status.edit(embed=emb, view=ServerButtons(serv.mapname, self.urt_discord_bridge.bridgeConfig))
                except asyncio.TimeoutError:
                    with open("logs/updateStatusServers_errors.txt", "a+") as fl:
                        fl.write(f"{datetime.datetime.now()} | Error to update map {serv.mapname} ({serv.address}) for messageId : {serv.status.id}\n")

    # async def set_discord_server_infos_task(self):
    #     await self.wait_until_ready()
    #     channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.statusChannelId)
    #     if (channel is not None):
    #         await self.deleteStatusMessage(channel)
    #         await self.initStatusMessage(channel)
    #         while not self.is_closed():
    #             await self.updateStatusServers()
    #             await asyncio.sleep(15) # Params

    @tasks.loop(seconds=30)
    async def set_discord_server_infos_task(self):
        await self.updateStatusServers()

    @set_discord_server_infos_task.before_loop
    async def set_discord_server_infos_task_before(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.statusChannelId)
        await self.deleteStatusMessage(channel)
        await self.initStatusMessage(channel)
                
            
