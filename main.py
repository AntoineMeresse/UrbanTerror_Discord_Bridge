import asyncio
from typing import Tuple
import discord
import uvicorn

from fastapi import FastAPI

from src.BridgeConfig import BridgeConfig
from src.FliservClient import FliservClient
from src.UrtDiscordBridge import UrtDiscordBridge
from src.utils import DiscordMessage
from src.RequestObjects import DemoInfos, ServerInfos

####################################### Discord Bot #######################################

def initDiscordBot() -> Tuple[BridgeConfig, UrtDiscordBridge, FliservClient]:
    bridgeConfig : BridgeConfig = BridgeConfig("config/server_config.json")
    print(bridgeConfig)

    bridge : UrtDiscordBridge = UrtDiscordBridge(bridgeConfig=bridgeConfig)

    intents = discord.Intents.default()
    intents.message_content = True
    return bridgeConfig, bridge, FliservClient(intents=intents, urt_discord_bridge=bridge)

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
    print(message)
    bridge.addMessages(message)
    print(bridge.messages.qsize())
    return message

@app.post("/demo")
async def sendDemo(demo : DemoInfos):
    bridge.addDemos(demosInfos= demo)
    print(bridge.demos)
    return demo

@app.post("/server")
async def updateServer(infos : ServerInfos):
    bridge.setServerInfo(infos)
    return infos

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=5000)