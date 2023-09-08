from typing import Dict
import json

from lib.py3quake3 import PyQuake3
from src.UrtDiscordServer import UrtDiscordServer
from src.RequestObjects import PingInfos

class BridgeConfig():

    def __init__(self, server_config_file_path : str) -> None:
        self.config = server_config_file_path

        self.discordKey : str = None
        self.demoChannelId : int = None
        self.statusChannelId : str = None
        self.mappingChannelId : str = None
        self.adminRole : int = None

        self.refresh : int = None
        self.logoUrl : str = None

        self.apikey : str = None
        self.apiUrl : str = None
        self.toprunsUrl : str = None
        self.mapinfoUrl : str = None
        self.mappageUrl : str = None
        self.levelshotUrl : str = None

        self.mapfolder : str = None
        self.mapUploadChannelId : int = None

        self.url : str = None
        self.port : int = None
        self.ws_url : str = None
        self.domain : str = None
        
        self.serverAdressDict : Dict[str, UrtDiscordServer] = dict()
        self.channelIdDict : Dict[int, PyQuake3] = dict()
        self.restartWithChannelId : Dict[int, str] = dict()

        self.loadConfig()

    def loadConfig(self):
        print(f"Load config : {self.config}")
        with open(self.config) as file:
            datas = json.load(file)
            
            self.discordKey = datas['discordKey']
            self.demoChannelId = datas['demoChannelId']
            self.statusChannelId = datas['statusChannelId']
            self.mappingChannelId = datas['mappingChannelId']
            self.adminRole = datas['adminRole']
            self.refresh = datas['refreshInterval']
            self.logoUrl = datas['logo']
            
            self.apikey = datas['api']['apikey']
            self.apiUrl = datas['api']['urls']['global']
            self.toprunsUrl = datas['api']['urls']['topruns']
            self.mapinfoUrl = datas['api']['urls']['mapinfo']
            self.mappageUrl = datas['api']['urls']['mappage']
            self.levelshotUrl = datas['api']['urls']['levelshot']

            self.mapfolder = datas['mapfolder']
            self.mapUploadChannelId = datas['mapUploadChannelId']

            self.url = datas['uvicorn']['url']
            self.port = datas['uvicorn']['port']
            self.ws_url = f"{self.url}:{self.port}"
            if "domain" in datas['uvicorn']:
                self.domain = datas['uvicorn']['domain']

            # Setup all servs
            for serv in datas['servers']:
                self.addServer(serv)

    def addServer(self, serverInfos : Dict):
        servername = serverInfos["name"]
        ip = serverInfos["ip"]
        port = serverInfos["port"]
        rconpassword = serverInfos["rconpassword"]
        discordChannelId = serverInfos["channelId"]
        address = f"{ip}:{port}"
        domain = f"{self.domain}:{port}" if (ip == self.url and self.domain is not None) else None

        self.serverAdressDict[address] = UrtDiscordServer(address, discordChannelId, servername, rconpassword=rconpassword, domain=domain) 
        self.channelIdDict[discordChannelId] = PyQuake3(address, rconpassword)
        
        if ("restart" in serverInfos):
            self.restartWithChannelId[discordChannelId] = serverInfos["restart"]

    def getChannel(self, serverAdress):
        # print(f"Get channel for : {serverAdress}")
        if (serverAdress in self.serverAdressDict):
            return self.serverAdressDict[serverAdress].getChannel()
        return None

    def __str__(self) -> str:
        res = ""
        res += "=============================== BridgeConfig ==============================="     
        res += f"\n|------> discordKey : {self.discordKey}"
        res += f"\n|------> demoChannelId : {self.demoChannelId}"
        res += f"\n|------> statusChannelId : {self.statusChannelId}"
        res += f"\n|------> refresh : {self.refresh}"
        res += f"\n|------> Servers :"
        for server in self.serverAdressDict:
            res += f"\n|-----------> {self.serverAdressDict[server]}"
        res += "\n============================================================================"
        return res
    
    def isServerStatusOk(self, infos : PingInfos) -> bool:
        if (infos.serverAddress in self.serverAdressDict):
            server : UrtDiscordServer = self.serverAdressDict[infos.serverAddress]
            if server.discordChannelId in self.channelIdDict:
                pyQuake3 = self.channelIdDict[server.discordChannelId]
                try:
                    status = pyQuake3.rcon("status")
                    if (server.mapname is None):
                        try:
                            servMap : str = status[1].split("\n")[0].split("map: ")[1].strip()
                            server.mapname = servMap
                        except:
                            pass
                    return True
                except:
                   pass
        return False

    def getWsUrl(self):
        return self.ws_url.replace(self.url, self.domain) if self.domain is not None else self.ws_url

