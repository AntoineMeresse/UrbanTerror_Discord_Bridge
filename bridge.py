import asyncio
from typing import Tuple
import discord
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from fastapi import Depends, FastAPI
from src.BridgeConfig import BridgeConfig
from src.DiscordClient import DiscordClient
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import DiscordMessage
from src.RequestObjects import DemoInfos, DiscordMessageEmbed, PingInfos, ServerInfos
from src.RateLimiter import RateLimiter

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

app = FastAPI()
local = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] ,
    allow_methods=['GET'],
)

local.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost'] ,
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
    return {"Bridge working"}

@local.get("/")
async def root(): 
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

@app.get("/q3ut4/{name_file}", dependencies=[Depends(
            RateLimiter(requests_limit=30, time_window=60, request_counters=request_counters, whitelisted_urls=[bridgeConfig.url]))]
        )
async def getMap(name_file : str):
    mapfile = name_file
    if (not ".pk3" in mapfile):
        mapfile+=".pk3"
    path = f"{bridgeConfig.mapfolder}/{mapfile}"
    return FileResponse(path=path)

app.mount('/local', local)

if __name__ == "__main__":
    uvicorn.run(app, host=bridgeConfig.url, port=bridgeConfig.port)