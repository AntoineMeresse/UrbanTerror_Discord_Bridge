import discord
from src.BridgeConfig import BridgeConfig

from src.utils import generateEmbedToprun

class ServerButtons(discord.ui.View):

    def __init__(self, mapname : str, bridgeConfig : BridgeConfig):
        super().__init__()
        self.mapname = mapname
        self.bridgeConfig : BridgeConfig = bridgeConfig
        self.delayInSecondsBeforeDelete = 30

    @discord.ui.button(label="Top", style=discord.ButtonStyle.secondary, emoji="🥇")
    async def topInfoButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = await generateEmbedToprun(self.mapname, False, self.bridgeConfig)
        await interaction.response.send_message(embed=emb, ephemeral=True, delete_after=30)    

    @discord.ui.button(label="Topruns", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def toprunInfoButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = await generateEmbedToprun(self.mapname, True, self.bridgeConfig)
        await interaction.response.send_message(embed=emb, ephemeral=True, delete_after=30)