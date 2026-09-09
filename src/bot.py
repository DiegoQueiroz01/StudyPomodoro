import os
import sys
import asyncio
import discord
from pathlib import Path
from discord.ext import commands
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True


class StudyBot(commands.Bot):
    """Bot de estudos com carregamento assíncrono de Cogs."""

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Método nativo invocado antes do bot conectar, ideal para carregar Cogs."""
        # Carrega a Cog de Pomodoro
        await self.load_extension("cogs.pomodoro_cog")
        
        # Sincroniza a árvore de comandos Slash
        synced = await self.tree.sync()
        print(f"Comandos Slash sincronizados via Cogs: {len(synced)} comando(s)")


bot = StudyBot()


@bot.event
async def on_ready():
    print("========================================")
    print(f"Bot conectado como: {bot.user.name}")
    print("========================================")


# TRATAMENTO GLOBAL DE ERROS EM COMANDOS SLASH
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print(f"[ERRO DE COMANDO] {error}")

    if interaction.response.is_done():
        await interaction.followup.send(
            "❌ **Ocorreu um erro ao processar o comando.** Tente novamente.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "❌ **Ocorreu um erro inesperado.** O suporte já foi notificado.",
            ephemeral=True,
        )


if __name__ == "__main__":
    bot.run(TOKEN)