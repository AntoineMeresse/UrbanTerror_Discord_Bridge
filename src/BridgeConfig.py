from typing import Any, Dict
import json

from lib.py3quake3 import PyQuake3
from src.UrtDiscordServer import UrtDiscordServer


class BridgeConfig():

    def __init__(self, server_config_file_path : str) -> None:
        self.config = server_config_file_path

        self.discordKey : str = None
        self.demoChannelId : int = None
        self.demoFileLog : str = None
        self.demoUrl : str = None
        self.refresh : int = None
        self.logoUrl : str = None

        self.apikey : str = None
        self.apiUrl : str = None
        self.toprunsUrl : str = None
        self.mapinfoUrl : str = None
        self.mappageUrl : str = None
        self.levelshotUrl : str = None
        
        self.serverAdressDict : Dict[str, UrtDiscordServer] = dict()
        self.channelIdDict : Dict[int, PyQuake3] = dict()

        self.loadConfig()

    def loadConfig(self):
        print(f"Load config : {self.config}")
        with open(self.config) as file:
            datas = json.load(file)
            
            self.discordKey = datas['discordKey']
            self.demoChannelId = datas['demoChannelId']
            self.demoFileLog = datas['demoFileLog']
            self.demoUrl = datas['demoUrl']
            self.refresh = datas['refreshInterval']
            self.logoUrl = datas['logo']
            for serv in datas['servers']:
                self.addServer(serv)
            
            self.apikey = datas['api']['apikey']
            self.apiUrl = datas['api']['urls']['global']
            self.toprunsUrl = datas['api']['urls']['topruns']
            self.mapinfoUrl = datas['api']['urls']['mapinfo']
            self.mappageUrl = datas['api']['urls']['mappage']
            self.levelshotUrl = datas['api']['urls']['levelshot']
            

    def addServer(self, serverInfos : Dict):
        ip = serverInfos["ip"]
        port = serverInfos["port"]
        rconpassword = serverInfos["rconpassword"]
        discordChannelId = serverInfos["channelId"]
        address = f"{ip}:{port}"

        self.serverAdressDict[address] = UrtDiscordServer(discordChannelId) 
        self.channelIdDict[discordChannelId] = PyQuake3(address, rconpassword)

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
        res += f"\n|------> demoFileLog : {self.demoFileLog}"
        res += f"\n|------> demoUrl : {self.demoUrl}"
        res += f"\n|------> refresh : {self.refresh}"
        res += f"\n|------> Servers :"
        for server in self.serverAdressDict:
            res += f"\n|-----------> {self.serverAdressDict[server]}"
        res += "\n============================================================================"
        return res


