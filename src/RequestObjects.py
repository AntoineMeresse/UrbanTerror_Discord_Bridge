from typing import List, Union
from pydantic import BaseModel

class DiscordMessageEmbed(BaseModel):
    serverAddress : str
    mapname : str
    embed : str

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

class Player(BaseModel):
    name : str
    ingame : bool
    running : bool
class ServerInfos(BaseModel):
    serverAddress : str
    playersList: Union[List[Player], None]
    mapname: Union[str, None]