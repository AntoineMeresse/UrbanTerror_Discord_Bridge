from typing import List, Union
from pydantic import BaseModel

class DiscordMessageEmbed(BaseModel):
    serverAddress : str
    mapname : str

class DiscordMessage(BaseModel):
    serverAddress : str
    message :str
    team : Union[str, None]

class DemoInfos(BaseModel):
    serverAddress : str
    msg : str
    path : str
    name : str
    chatMessage : str

    def __str__(self):
        return f"{self.serverAddress} | {self.msg} | {self.path} | {self.name} | {self.chatMessage}"
    
class Player(BaseModel):
    name : str
    ingame : bool
    running : bool

class ServerInfos(BaseModel):
    serverAddress : str
    playersList: Union[List[Player], None]
    mapname: Union[str, None]

class PingInfos(BaseModel):
    serverAddress : str

class PlayerPenInfos(BaseModel):
    qkey : str
    name : str
    size : float