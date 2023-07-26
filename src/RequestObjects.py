from typing import Union
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