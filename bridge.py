import asyncio
import os
import discord
import uvicorn

from contextlib import asynccontextmanager
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile

from typing import Tuple
from src.map_repository import getAllMaps, getMapPath, getMapsWithPattern
from src.BridgeConfig import BridgeConfig
from src.DiscordClient import DiscordClient
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import DiscordMessage
from src.RequestObjects import DemoInfos, DiscordMessageEmbed, PingInfos, ServerInfos, ServerMessage
from src.RateLimiter import RateLimiter
from src.ApiCalls import getRandomMap

import sys

from src.logger import setup_logger, get_logger
setup_logger()
logger = get_logger("bridge")

####################################### Discord Bot #######################################

def initDiscordBot() -> Tuple[BridgeConfig, UrtDiscordBridge, DiscordClient]:
    args = sys.argv
    if (len(args) < 2):
        logger.error("Specify a correct path for config file.")
        exit()
    # bridgeConfig : BridgeConfig = BridgeConfig("config/server_config.json")
    bridgeConfig : BridgeConfig = BridgeConfig(sys.argv[1])
    logger.info(str(bridgeConfig))

    bridge : UrtDiscordBridge = UrtDiscordBridge(bridgeConfig=bridgeConfig)

    intents = discord.Intents.default()
    intents.message_content = True
    return bridgeConfig, bridge, DiscordClient(intents=intents, urt_discord_bridge=bridge)

def mb(n: int) -> int:
    return n * 1024 * 1024

bridgeConfig, bridge, bot = initDiscordBot()

####################################### FastAPI #######################################

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(bot.start(bridgeConfig.discordKey))
    try:
        await asyncio.wait_for(bot.wait_until_ready(), timeout=30)
        logger.info(f"{bot.user} has connected to Discord!")
    except asyncio.TimeoutError:
        logger.warning("Discord bot did not connect within 30 seconds, continuing anyway")
    yield

templates = Jinja2Templates(directory="templates")
app = FastAPI(lifespan=lifespan)
local = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['GET'],
)

local.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost', bridgeConfig.url],
    allow_methods=['GET', 'POST'],
)

# In-memory storage for request counters
request_counters = {}

@app.get("/")
async def root():
    return RedirectResponse(url="/q3ut4")

@app.get("/health")
async def health():
    return {"Bridge working"}

@local.get("/localstatus")
async def localStatus():
    return {"Bridge local working"}

@local.post("/message")
async def localSendMessage(message: DiscordMessage):
    bridge.addMessages(message)
    return message

@local.post("/emb")
async def sendMessageEmbed(message: DiscordMessageEmbed):
    bridge.addMessages(message)
    return message

@local.post("/demo")
async def sendDemo(demo : DemoInfos):
    bridge.addDemos(demosInfos= demo)
    return demo

@local.post("/demo/upload")
async def uploadDemo(
    file: UploadFile,
    serverAddress: str = Form(...),
    msg: str = Form(...),
    chatMessage: str = Form(...),
):
    if not (file.filename.endswith(".dm_68") or file.filename.endswith(".urtdemo")):
        raise HTTPException(status_code=400, detail="Only .dm_68 and .urtdemo demo files are accepted")
    content = await file.read()
    if len(content) > mb(50):
        raise HTTPException(status_code=413, detail="Demo file exceeds the 50MB limit")
    bridge.addDemoFromUpload(content, file.filename, serverAddress, msg, chatMessage)

@local.post("/server")
async def updateServer(infos : ServerInfos):
    bridge.setServerInfo(infos)
    return infos

@local.post("/mapsync")
async def mapSync():
    bridge.mapSync()
    return "Map sync : ok"

@local.post("/server-status")
async def isServerOk(infos : PingInfos) -> bool:
    return bridge.bridgeConfig.isServerStatusOk(infos)

@app.get("/status", dependencies=[Depends(
            RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))]
        )
async def getStatus() -> list:
    return [serv.get_infos() for serv in bridgeConfig.serverAdressDict.values()]

@local.get("/status")
async def getStatusLocal() -> list:
    return [serv.get_infos() for serv in bridgeConfig.serverAdressDict.values()]

@app.get("/q3ut4/{mapfile}", dependencies=[Depends(
            RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))]
        )
async def getMap(mapfile : str):
    if not mapfile.endswith(".pk3"):
        raise HTTPException(status_code=400, detail="Only .pk3 files are served")
    path = getMapPath(mapfile, bridgeConfig.mapfolder)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Map not found")
    return FileResponse(path=path, media_type="application/octet-stream")

@app.get("/q3ut4", dependencies=[Depends(RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))])
async def getMapList(request: Request):
    maps = getAllMaps(bridgeConfig.mapfolder)
    return templates.TemplateResponse("maplist.html", {"request": request, "maps": maps, "number" : len(maps)})

@local.get("/maps/download/{mapname}")
async def searchMaps(mapname: str):
    return {"matching" : getMapsWithPattern(mapname, bridgeConfig.mapfolder)}

@local.get("/maps/random")
async def getRandomMapRoute():
    return await getRandomMap(bridgeConfig.apikey)

@app.post("/message/all", dependencies=[Depends(RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))])
async def sendMessageToAll(message: ServerMessage):
    if (bridgeConfig.isGlobalMessageApikey(message.apikey)):
        bridge.sendServerMessages(message)
        return message.message
    return "Not a correct apikey."

@app.post("/message", dependencies=[Depends(RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))])
async def sendMessage(message: ServerMessage):
    if (bridgeConfig.isGlobalMessageApikey(message.apikey)):
        info = bridge.sendServerMessage(message)
        return info
    return "Not a correct apikey."

app.mount('/local', local)

if __name__ == "__main__":
    # uvicorn.run(app, port=bridgeConfig.port)
    uvicorn.run(app, host=bridgeConfig.url, port=bridgeConfig.port)
