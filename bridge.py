import asyncio
from typing import Tuple
import discord
from fastapi.responses import FileResponse
import uvicorn

from fastapi import FastAPI

from src.BridgeConfig import BridgeConfig
from src.DiscordClient import DiscordClient
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import DiscordMessage
from src.RequestObjects import DemoInfos, DiscordMessageEmbed, ServerInfos

import sys

####################################### Discord Bot #######################################

def initDiscordBot() -> Tuple[BridgeConfig, UrtDiscordBridge, DiscordClient]:
    args = sys.argv
    if (len(args) < 2):
        print("Specify a correct path for config file.")
        exit()
    bridgeConfig : BridgeConfig = BridgeConfig(sys.argv[1])
    print(bridgeConfig)

    bridge : UrtDiscordBridge = UrtDiscordBridge(bridgeConfig=bridgeConfig)

    intents = discord.Intents.default()
    intents.message_content = True
    return bridgeConfig, bridge, DiscordClient(intents=intents, urt_discord_bridge=bridge)

bridgeConfig, bridge, bot = initDiscordBot() 

####################################### FastAPI #######################################

app = FastAPI()

@app.on_event("startup")
async def startup_event(): #this fucntion will run before the main API starts
    asyncio.create_task(bot.start(bridgeConfig.discordKey))
    await asyncio.sleep(4) #optional sleep for established connection with discord
    print(f"{bot.user} has connected to Discord!")

@app.get("/")
async def root(): 
    return {"Main"}

@app.post("/message")
async def sendMessage(message: DiscordMessage):
    bridge.addMessages(message)
    return message

@app.post("/emb")
async def sendMessageEmbed(message: DiscordMessageEmbed):
    bridge.addMessages(message)
    return message

@app.post("/demo")
async def sendDemo(demo : DemoInfos):
    bridge.addDemos(demosInfos= demo)
    return demo

@app.post("/server")
async def updateServer(infos : ServerInfos):
    bridge.setServerInfo(infos)
    return infos

# @app.get("/q3ut4/{name_file}")
# async def getFile(name_file : str):
#     return FileResponse(path=f"/home/antoine/dev/UrbanTerror_Discord_Bridge/test/{name_file}")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5000)