import discord
from src.BridgeConfig import BridgeConfig

from src.utils import generateEmbedToprun

class ServerButtons(discord.ui.View):

    def __init__(self, mapname : str, bridgeConfig : BridgeConfig):
        super().__init__()
        self.mapname = mapname
        self.bridgeConfig : BridgeConfig = bridgeConfig

    @discord.ui.button(label="Top", style=discord.ButtonStyle.secondary, emoji="🥇")
    async def topInfoButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=generateEmbedToprun(self.mapname, False, self.bridgeConfig), ephemeral=True, delete_after=10)    

    @discord.ui.button(label="Topruns", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def toprunInfoButton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=generateEmbedToprun(self.mapname, True, self.bridgeConfig), ephemeral=True, delete_after=10)