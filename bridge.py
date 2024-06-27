import asyncio
import discord
import uvicorn

from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi import Depends, FastAPI, Request

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

####################################### Discord Bot #######################################

def initDiscordBot() -> Tuple[BridgeConfig, UrtDiscordBridge, DiscordClient]:
    args = sys.argv
    if (len(args) < 2):
        print("Specify a correct path for config file.")
        exit()
    # bridgeConfig : BridgeConfig = BridgeConfig("config/server_config.json")
    bridgeConfig : BridgeConfig = BridgeConfig(sys.argv[1])
    print(bridgeConfig)

    bridge : UrtDiscordBridge = UrtDiscordBridge(bridgeConfig=bridgeConfig)

    intents = discord.Intents.default()
    intents.message_content = True
    return bridgeConfig, bridge, DiscordClient(intents=intents, urt_discord_bridge=bridge)

bridgeConfig, bridge, bot = initDiscordBot() 

####################################### FastAPI #######################################

templates = Jinja2Templates(directory="templates")
app = FastAPI()
local = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] ,
    allow_methods=['GET'],
)

local.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost', bridgeConfig.url] ,
    allow_methods=['GET', 'POST'],
)

# In-memory storage for request counters
request_counters = {}

@app.on_event("startup")
async def startup_event(): #this fucntion will run before the main API starts
    asyncio.create_task(bot.start(bridgeConfig.discordKey))
    await asyncio.sleep(4) #optional sleep for established connection with discord
    print(f"{bot.user} has connected to Discord!")

@app.get("/")
async def root():
    return RedirectResponse(url="/q3ut4")

@app.get("/status")
async def status(): 
    return {"Bridge working"}

@local.get("/localstatus")
async def status(): 
    return {"Bridge local working"}

@local.post("/message")
async def sendMessage(message: DiscordMessage):
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
    return FileResponse(path=getMapPath(mapfile, bridgeConfig.mapfolder), media_type="application/octet-stream")

@app.get("/q3ut4", dependencies=[Depends(RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))])
async def getMapList(request: Request):
    maps = getAllMaps(bridgeConfig.mapfolder)
    return templates.TemplateResponse("maplist.html", {"request": request, "maps": maps, "number" : len(maps)})

@local.get("/maps/download/{mapname}")
async def getMapListWithPattern(mapname: str):
    return {"matching" : getMapsWithPattern(mapname, bridgeConfig.mapfolder)}

@local.get("/maps/random")
async def getMapListWithPattern():
    return await getRandomMap(bridgeConfig.apikey)

@app.post("/message/all", dependencies=[Depends(RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))])
async def sendMessage(message: ServerMessage):
    if (bridgeConfig.isGlobalMessageApikey(message.apikey)):
        bridge.sendServerMessages(message)
        return message.message
    return "Not a correct apikey."

app.mount('/local', local)

if __name__ == "__main__":
    # uvicorn.run(app, port=bridgeConfig.port)
    uvicorn.run(app, host=bridgeConfig.url, port=bridgeConfig.port)