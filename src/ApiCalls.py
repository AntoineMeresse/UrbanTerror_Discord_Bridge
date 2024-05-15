import aiohttp

from src.BridgeConfig import BridgeConfig
import random

async def getApiInfos(mapName, url, apikey):
    if (mapName is not None and mapName != ""):
        url = url
        p = {
            "mapname" : mapName,
            "apikey": apikey
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.post(url=url, json=p) as response:
                try:
                    res = await response.json()
                    return res
                except:
                    return None
    return None

async def getMapInfo(mapName, bridgeConfig : BridgeConfig):
    return await getApiInfos(mapName, bridgeConfig.mapinfoUrl, bridgeConfig.apikey)

async def getToprunsInfo(mapName, bridgeConfig : BridgeConfig):
    return await getApiInfos(mapName, bridgeConfig.toprunsUrl, bridgeConfig.apikey)

async def getServerStatus(ws_url : str, address : str):
    url = f"http://{ws_url}/local/server-status"
    p = {
        "serverAddress" : address
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
        async with session.post(url=url, json=p) as response:
            try:
                res = await response.json()
                return res
            except:
                return False
            
async def getRandomMap(apikey) -> str: 
    url = 'https://urtjumpmaps.com/mapinfo/getallmapnames'
    p = {'apikey': apikey}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
        async with session.get(url=url, json=p) as response:
            try:
                maps = await response.json()
                return random.choice(maps)
            except:
                return None