import asyncio
import datetime
import os
import queue
import subprocess
import discord
from discord.ext import tasks
import zipfile

from typing import Any, Union
from lib.py3quake3 import PyQuake3
from src.ApiCalls import getRandomMap
from src.ServerButtons import ServerButtons
from src.RequestObjects import DemoInfos, DiscordMessage, DiscordMessageEmbed
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import convertMessage, discordBlock, generateEmbed, generateEmbedToprun, getProgressiveImages
from src.PenDB import pen_of_today, pen_of_yesterday, pen_hall_of_fame, pen_hall_of_shame
from src.ApiCalls import getServerStatus
from src.logger import get_logger

logger = get_logger("discord")

class DiscordClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, urt_discord_bridge = None, **options: Any) -> None:
        super().__init__(intents=intents, **options)
        self.urt_discord_bridge : UrtDiscordBridge = urt_discord_bridge
        self.interval = self.urt_discord_bridge.bridgeConfig.refresh

    async def on_ready(self):
        logger.info("----------------> Bridge Online <----------------")
        self.urt_discord_bridge.reloadMapInfos()

    def getServInfos(self, channelId) -> str:
        for serv in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            logger.debug(f"--> {serv.discordChannelId}")
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
        elif (cmd in ["!roll", "!random"]):
            mapname = await getRandomMap(self.urt_discord_bridge.bridgeConfig.apikey)
            if mapname is not None:
                emb = await generateEmbed(mapname, None, None, self.urt_discord_bridge.bridgeConfig)
                emb.title = "Random map: " + emb.title
                await message.channel.send(embed=emb)
            else:
                await message.channel.send("Error trying to find a random map")
        elif (cmd in ["!potd", "!phof", "!phos"]):
            uri = self.urt_discord_bridge.bridgeConfig.postgresql_uri
            if uri is None:
                await message.channel.send("No database configured.")
                return
            try:
                if cmd == "!potd":
                    lines = await asyncio.to_thread(pen_of_today, uri)
                elif cmd == "!phof":
                    lines = await asyncio.to_thread(pen_hall_of_fame, uri)
                else:
                    lines = await asyncio.to_thread(pen_hall_of_shame, uri)
                await message.channel.send(discordBlock(lines))
            except Exception as e:
                logger.error(f"Pen DB query failed: {e}")
                await message.channel.send("Failed to retrieve data from database.")
            return
        elif (cmd == "!help"):
            cmds = [
                "Available commands :",
                "Everyone :"
                "   |-> !mapinfos or !mapinfo : To get map infos",
                "   |-> !topruns, !tr : To get all runs for a given map",
                "   |-> !top : To get only best runs for a given map",
                "   |-> !status : To display latest server status (Only in server bridges)",
                "[UJM] Admins :",
                "   |-> !restart : Restart the server and bot (Only in server bridges)"
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
                        if (file_exists):
                            await message.channel.send(f"{filename} is already on the repository.```yaml\nIf you want to replace it :\n - !delete {filename}\n - Upload it again\n```") 
                        else:
                            await uploadedFile.save(path)

                            with zipfile.ZipFile(path, 'r') as zip_file:
                                file_list = zip_file.namelist()
                                bspname = filename.replace(".pk3", ".bsp")
                                bsppath = f"maps/{bspname}"
                                progressiveImages = getProgressiveImages(path)
                                
                                errorMsg = ""
                                if ("!force" not in msg): 
                                    if (not bsppath in file_list):
                                        errorMsg += f"\n- `{bsppath}` missing inside the pk3."
                                    
                                    if (len(progressiveImages) > 0):
                                        errorMsg += f"\n- Progressive image(s) [{len(progressiveImages)}]: `{progressiveImages}`. Can be force by uploading the file using `!force`"
                                
                                if(errorMsg == ""):
                                    url = f"https://{self.urt_discord_bridge.bridgeConfig.getWsUrl()}/q3ut4/{filename}"
                                    cleanname = filename.replace(".pk3", "")
                                    await message.channel.send(f"`{filename}` has been successfully uploaded.\n- Download link: {url}\n- In UJM servers: `!mapget {cleanname}`")
                                    if len(msg) > 0 and "!force" not in msg:
                                        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.mappingChannelId)
                                        if (channel is not None):
                                            await channel.send(content=msg, file = discord.File(fp=path))
                                else:
                                    file_exists = os.path.isfile(path)
                                    if file_exists:
                                        os.remove(path)
                                    await message.channel.send(f"`{filename}` has not been uploaded: {errorMsg}") 
                    else:
                        await message.channel.send("Please provide a pk3 file")
            else:
                if not message.author.bot:
                    s = msg.split(" ")
                    cmd : str = s[0]
                    if (cmd.lower() == "!delete"):
                        if len(s) == 2:
                            filename : str = s[1]
                            if ".pk3" not in filename:
                                filename = filename + ".pk3"
                            path = f"{self.urt_discord_bridge.bridgeConfig.mapfolder}/{filename}"
                            file_exists = os.path.isfile(path)
                            if file_exists:
                                os.remove(path)
                                await message.channel.send(f"`{filename}` has been deleted.")
                                return
                            else:
                                await message.channel.send(f"`{filename}` doesn't exist.")  
                        else:
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
            att = ", ".join([f"{x.filename}" for x in message.attachments])
            f = "^6Files^7" if len(att) > 1 else "^6File^7"
            attMessage = f" [{f}: {att}]" if len(att) > 0 else ""
            messageToDisplay = f"{message.content}{attMessage}"
            self.urt_discord_bridge.sendMessage(msg_channelId, f'[{author}]', messageToDisplay)

    def setupChannels(self) -> bool:
        cpt = 0
        for server in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            server.setChannel(self.get_channel(server.discordChannelId))
            if server.getChannel is not None:
                cpt+=1
        return cpt > 0

    async def _run_supervised(self, coro_factory, name: str):
        while not self.is_closed():
            try:
                await coro_factory()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error(f"Task '{name}' crashed, restarting in 5s", exc_info=True)
                await asyncio.sleep(5)
                continue
            if not self.is_closed():
                logger.warning(f"Task '{name}' exited unexpectedly, restarting in 5s")
                await asyncio.sleep(5)

    async def setup_hook(self) -> None:
        logger.debug("setup_hook")
        if (len(self.urt_discord_bridge.bridgeConfig.serverAdressDict) > 0):
            self.messageTask = self.loop.create_task(self._run_supervised(self.send_message_task, "send_message_task"))
        if (self.urt_discord_bridge.bridgeConfig.demoChannelId):
            self.demoTask = self.loop.create_task(self._run_supervised(self.send_demos_task, "send_demos_task"))
        if (self.urt_discord_bridge.bridgeConfig.statusChannelId):
            self.set_discord_server_infos_task.start()
        if (self.urt_discord_bridge.bridgeConfig.potdChannelId):
            self.send_potd_task.start()
        
    async def send_message_task(self):
        await self.wait_until_ready()
        foundChannel = self.setupChannels()
        if (foundChannel):
            while not self.is_closed():
                try:
                    msg_queue = self.urt_discord_bridge.getListMessages()
                    while (not msg_queue.empty()):
                        with self.urt_discord_bridge.messagesLock:
                            try:
                                currentMessage : Union[DiscordMessage, DiscordMessageEmbed] = msg_queue.get_nowait()
                            except queue.Empty:
                                break
                        channel = self.urt_discord_bridge.bridgeConfig.getChannel(currentMessage.serverAddress)
                        if (channel is not None):
                            if type(currentMessage) == DiscordMessageEmbed:
                                players = self.urt_discord_bridge.bridgeConfig.serverAdressDict[currentMessage.serverAddress].players
                                emb = await generateEmbed(currentMessage.mapname, None, players, self.urt_discord_bridge.bridgeConfig)
                                try:
                                    async with asyncio.timeout(10):
                                        await channel.send(embed=emb)
                                except asyncio.TimeoutError:
                                    logger.error(f"Error to send embed change map for : {currentMessage.mapname} (server : {currentMessage.serverAddress})")
                            elif isinstance(currentMessage, DiscordMessage):
                                msg = convertMessage(currentMessage)
                                try:
                                    async with asyncio.timeout(10):
                                        await channel.send(msg)
                                except asyncio.TimeoutError:
                                    logger.error(f"Error to send message : {msg} (server : {currentMessage.serverAddress})")
                                except Exception as e:
                                    logger.error("Error sending message to discord", exc_info=True)
                        else:
                            logger.warning("Could not find a channel. (None)")
                except Exception as e:
                    logger.error(f"Unexpected error in send_message_task: {e}", exc_info=True)
                await asyncio.sleep(self.interval)
        else:
            logger.warning("There was no valid channels found.")

    async def send_demos_task(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.demoChannelId)
        if (channel is not None):
            while not self.is_closed():
                try:
                    demo_queue = self.urt_discord_bridge.getListDemos()
                    while (not demo_queue.empty()):
                        try:
                            demo : DemoInfos = demo_queue.get_nowait()
                        except queue.Empty:
                            break
                        if os.path.isfile(demo.path):
                            serv_channel = self.urt_discord_bridge.bridgeConfig.getChannel(demo.serverAddress)
                            msg = demo.msg
                            if (serv_channel is not None):
                                msg = f"({serv_channel.jump_url}) " + msg
                            try:
                                async with asyncio.timeout(10):
                                    post : discord.Message = await channel.send(msg, file = discord.File(fp=demo.path, filename=demo.name))
                                    if (serv_channel is not None):
                                        await serv_channel.send(f"{demo.chatMessage} {post.jump_url}")
                            except asyncio.TimeoutError:
                                logger.error(f"Error uploading demo on discord : {demo}")
                            except Exception as e:
                                logger.error("Error sending demos to discord", exc_info=True)
                            finally:
                                if demo.tmp and os.path.isfile(demo.path):
                                    os.remove(demo.path)
                                    logger.debug(f"Deleted tmp demo file: {demo.path}")
                        else:
                            logger.error(f"Error uploading demo on discord : {demo}. File doesn't exist: {demo.path}")
                except Exception as e:
                    logger.error(f"Unexpected error in send_demos_task: {e}", exc_info=True)
                await asyncio.sleep(self.interval)
        else:
            logger.warning("Could not find channel for demos")

    async def deleteStatusMessage(self, channel : discord.TextChannel):
        try:
            messages = [message async for message in channel.history(limit=None)]
            for m in messages:
                if (m.author == self.user):
                    await m.delete()
        except Exception as e:
            logger.error(f"Error deleting status messages: {e}", exc_info=True)

    async def initStatusMessage(self, channel : discord.TextChannel):
        for x in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            try:
                emb = await generateEmbed(x.mapname, None, x.players, self.urt_discord_bridge.bridgeConfig, servername=x.servername, servAvailable=False)
                x.status = await channel.send(embed=emb)
            except Exception as e:
                logger.error(f"Error initializing status message for {x.servername}: {e}", exc_info=True)
                                      
    async def updateStatusServers(self):
        for serv in self.urt_discord_bridge.bridgeConfig.serverAdressDict.values():
            if (serv.status is not None):
                # await asyncio.sleep(5)
                try:
                    async with asyncio.timeout(10):
                        available = await getServerStatus(self.urt_discord_bridge.bridgeConfig.ws_url,serv.address)
                        emb = await generateEmbed(serv.mapname, None, serv.players, self.urt_discord_bridge.bridgeConfig, updated=datetime.datetime.now(),
                                    servername=serv.servername, servAvailable=available, connectMessage=f"/connect {serv.displayedAddress}")
                        await serv.status.edit(embed=emb, view=ServerButtons(serv.mapname, self.urt_discord_bridge.bridgeConfig))
                except asyncio.TimeoutError as e:
                    logger.error(f"[asyncio.TimeoutError] Error to update map {serv.mapname} ({serv.address}) for messageId : {serv.status.id}", exc_info=True)
                except discord.NotFound as e:
                    logger.error(f"[discord.NotFound] Error to update map {serv.mapname} ({serv.address}) for messageId : {serv.status.id}", exc_info=True)
                except discord.HTTPException as e:
                    logger.error(f"[discord.HTTPException] Error to update map {serv.mapname} ({serv.address}) for messageId : {serv.status.id}", exc_info=True)
                except Exception as e:
                    logger.error(f"[Other] Error to update map {serv.mapname} ({serv.address}) for messageId : {serv.status.id}", exc_info=True)

    @tasks.loop(seconds=30)
    async def set_discord_server_infos_task(self):
        await self.updateStatusServers()

    @tasks.loop(time=datetime.time(hour=0, minute=0, second=30))
    async def send_potd_task(self):
        uri = self.urt_discord_bridge.bridgeConfig.postgresql_uri
        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.potdChannelId)
        if uri is None or channel is None:
            return
        try:
            lines = await asyncio.to_thread(pen_of_yesterday, uri)
            await channel.send(discordBlock(lines))
        except Exception as e:
            logger.error(f"Failed to publish POTD: {e}")

    @set_discord_server_infos_task.error
    async def set_discord_server_infos_task_error(self, error):
        logger.error("Status update task crashed, restarting", exc_info=error)
        self.set_discord_server_infos_task.restart()

    @set_discord_server_infos_task.before_loop
    async def set_discord_server_infos_task_before(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.urt_discord_bridge.bridgeConfig.statusChannelId)
        if channel is None:
            logger.warning(f"Could not find status channel (id: {self.urt_discord_bridge.bridgeConfig.statusChannelId}). Status loop will not start.")
            self.set_discord_server_infos_task.cancel()
            return
        await self.deleteStatusMessage(channel)
        await self.initStatusMessage(channel)
                
            
