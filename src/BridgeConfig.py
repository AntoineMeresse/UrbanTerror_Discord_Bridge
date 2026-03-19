from typing import Dict
import json

import psycopg2
from lib.py3quake3 import PyQuake3
from src.UrtDiscordServer import UrtDiscordServer
from src.RequestObjects import PingInfos
from src.logger import get_logger

logger = get_logger("config")

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

        self.postgresql_uri : str = None

        self.globalChatKeys = list()

        self.serverAdressDict : Dict[str, UrtDiscordServer] = dict()
        self.channelIdDict : Dict[int, PyQuake3] = dict()
        self.restartWithChannelId : Dict[int, str] = dict()

        self.loadConfig()

    def loadConfig(self):
        logger.debug(f"Load config : {self.config}")
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
            self.globalChatKeys = datas['api']['global-message-apikey']

            self.mapfolder = datas['mapfolder']
            self.mapUploadChannelId = datas['mapUploadChannelId']

            self.url = datas['uvicorn']['url']
            self.port = datas['uvicorn']['port']
            self.ws_url = f"{self.url}:{self.port}"
            if "domain" in datas['uvicorn']:
                self.domain = datas['uvicorn']['domain']

            if "postgresql_uri" in datas:
                self.postgresql_uri = datas['postgresql_uri']

            # Setup all servs
            for serv in datas['servers']:
                self.addServer(serv)

            self.loadServersFromDB()

    def addServer(self, serverInfos : Dict):
        servername = serverInfos.get("name", "Server")
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

    def loadServersFromDB(self):
        if self.postgresql_uri is None:
            logger.debug("No postgresql_uri configured, skipping DB server load")
            return
        logger.info("Loading servers from database...")
        try:
            conn = psycopg2.connect(self.postgresql_uri, connect_timeout=1, options="-c default_transaction_read_only=on")
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT ip, port, rconpassword, channel_id, name FROM server")
                    rows = cur.fetchall()
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to load servers from DB: {e}")
            return

        added = 0
        for ip, port, rconpassword, channel_id, name in rows:
            address = f"{ip}:{port}"
            if address not in self.serverAdressDict:
                self.addServer({
                    "ip": ip,
                    "port": port,
                    "rconpassword": rconpassword,
                    "channelId": channel_id,
                    "name": name,
                })
                added += 1
                logger.info(f"Added server from DB: {address}")
        logger.info(f"DB server load complete: {added} new server(s) added")

    def getChannel(self, serverAdress):
        logger.debug(f"Get channel for : {serverAdress}")
        if (serverAdress in self.serverAdressDict):
            return self.serverAdressDict[serverAdress].getChannel()
        logger.warning("Channel not found")
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
                        except Exception:
                            pass
                    return True
                except Exception as e:
                    logger.debug(f"RCON status failed for {infos.serverAddress}: {e}")
        return False

    def getWsUrl(self):
        return self.ws_url.replace(f"{self.url}:{self.port}", self.domain) if self.domain is not None else self.ws_url
    
    def isGlobalMessageApikey(self, key):
        return key in self.globalChatKeys
    

