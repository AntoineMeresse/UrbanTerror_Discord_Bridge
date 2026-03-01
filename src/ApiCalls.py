import aiohttp
import random

from src.BridgeConfig import BridgeConfig
from src.logger import get_logger

logger = get_logger("api")

async def getApiInfos(mapName, url, apikey):
    if (mapName is not None and mapName != ""):
        p = {
            "mapname" : mapName,
            "apikey": apikey
        }
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                async with session.post(url=url, json=p) as response:
                    res = await response.json()
                    return res
        except Exception as e:
            logger.warning(f"Failed to fetch API response for {mapName}: {e}")
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
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.post(url=url, json=p) as response:
                try:
                    res = await response.json()
                    return res
                except Exception as e:
                    logger.debug(f"Failed to parse server status response for {address}: {e}")
                    return False
    except Exception as e:
        logger.debug(f"Failed to reach server status endpoint for {address}: {e}")
        return False

async def getRandomMap(apikey) -> str:
    url = 'https://urtjumpmaps.com/mapinfo/getallmapnames'
    p = {'apikey': apikey}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
        async with session.get(url=url, json=p) as response:
            try:
                maps = await response.json()
                return random.choice(maps)
            except Exception as e:
                logger.warning(f"Failed to get random map: {e}")
                return None
