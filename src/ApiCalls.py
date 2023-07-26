import requests

from src.BridgeConfig import BridgeConfig

def getMapInfo(mapName, bridgeConfig : BridgeConfig):
    if (mapName != ""):
        url = bridgeConfig.mapinfoUrl
        p = {
            "mapname" : mapName,
            "apikey": bridgeConfig.apikey
        }
        res = requests.post(url, json = p, timeout=2)
        try:
            return res.json()
        except:
            return None
    return None