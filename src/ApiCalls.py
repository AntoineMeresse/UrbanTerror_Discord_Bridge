import aiohttp

from src.BridgeConfig import BridgeConfig

async def getApiInfos(mapName, url, apikey):
    if (mapName is not None and mapName != ""):
        url = url
        p = {
            "mapname" : mapName,
            "apikey": apikey
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.post(url=url, json=p) as response:
                res = await response.json()
                return res
    return None

async def getMapInfo(mapName, bridgeConfig : BridgeConfig):
    return await getApiInfos(mapName, bridgeConfig.mapinfoUrl, bridgeConfig.apikey)

async def getToprunsInfo(mapName, bridgeConfig : BridgeConfig):
    return await getApiInfos(mapName, bridgeConfig.toprunsUrl, bridgeConfig.apikey)