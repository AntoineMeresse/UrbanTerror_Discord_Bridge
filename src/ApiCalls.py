import requests

from src.BridgeConfig import BridgeConfig

def getApiInfos(mapName, url, apikey):
    if (mapName != ""):
        url = url
        p = {
            "mapname" : mapName,
            "apikey": apikey
        }
        res = requests.post(url, json = p, timeout=2)
        try:
            return res.json()
        except:
            return None
    return None

def getMapInfo(mapName, bridgeConfig : BridgeConfig):
    return getApiInfos(mapName, bridgeConfig.mapinfoUrl, bridgeConfig.apikey)

def getToprunsInfo(mapName, bridgeConfig : BridgeConfig):
    return getApiInfos(mapName, bridgeConfig.toprunsUrl, bridgeConfig.apikey)