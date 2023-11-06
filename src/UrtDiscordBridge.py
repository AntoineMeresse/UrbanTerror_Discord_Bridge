from queue import Queue
import textwrap
from threading import RLock

from src.RequestObjects import DemoInfos, DiscordMessage, ServerInfos, ServerMessage
from src.BridgeConfig import BridgeConfig

class UrtDiscordBridge():

    def __init__(self, bridgeConfig : BridgeConfig = None) -> None:
        self.bridgeConfig = bridgeConfig
        
        self.messages = Queue()
        self.demos = Queue()

        # Locks
        self.messagesLock = RLock()
        self.demosLock = RLock()

    def addEmbed(self, embedInfos):
        with self.messagesLock:
            #build embed
            self.messages.put(embedInfos)

    def addMessages(self, discordMessage : DiscordMessage):
        with self.messagesLock:
            self.messages.put(discordMessage)

    def getListMessages(self) -> Queue:
        return self.messages

    def sendMessage(self, channelId: int, author: str, message : str) -> None:
        # print(f"{message} by {author} in {channelId}")
        if (channelId in self.bridgeConfig.channelIdDict):
            pyquake3 = self.bridgeConfig.channelIdDict[channelId]
            msgs = textwrap.wrap(message, 70)
            for msg in msgs:
                msg = f"^5{author}^7 {msg}"
                pyquake3.rcon("saybot %s" % msg) #check why saybot isn't working correctly
        # else:
        #     print(f"Channel : {channelId} was not found in self.bridgeConfig.channelIdDict")

    ################################################################### Demos

    def addDemos(self, demosInfos : DemoInfos) -> None:
        self.demos.put(demosInfos)
    
    def getListDemos(self) -> Queue[DemoInfos]:
        return self.demos
        
    ###########################################################

    def setServerInfo(self, infos : ServerInfos):
        if (infos.serverAddress is not None):
            for serverInfo in self.bridgeConfig.serverAdressDict.values():
                if serverInfo.address == infos.serverAddress:
                    if (infos.playersList is not None):
                        serverInfo.players = infos.playersList
                    if (infos.mapname is not None):
                        serverInfo.mapname = infos.mapname
                    return

    def mapSync(self):
        for server in self.bridgeConfig.channelIdDict.values():
            try:
                server.rcon("reloadMaps")
                print(f"{server.address}:{server.port} | Reloadmaps OK")
                # server.rcon("Maps have been reloaded.")
            except:
                print(f"{server.address}:{server.port} | Reloadmaps KO (Server probably down)")

    def sendServerMessages(self, serverMessage : ServerMessage):
        msg = f"^6[ALL] ^3{serverMessage.name}^7: {serverMessage.message}"
        for server in self.bridgeConfig.channelIdDict.values():
            if server.get_address() != serverMessage.serverAddress:
                try:
                    server.rcon(f"saybot {msg}")
                except:
                    pass
   