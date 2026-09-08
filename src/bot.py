import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# 1. Carrega as variáveis de ambiente
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")

# 2. Configura as Intents
intents = discord.Intents.default()
intents.members = True

# 3. Instancia o Bot
bot = commands.Bot(command_prefix="!", intents=intents)


# 4. Evento quando o bot conecta
@bot.event
async def on_ready():
    print(f"========================================")
    print(f"Bot conectado como: {bot.user.name}")
    print(f"ID do Bot:         {bot.user.id}")
    
    # Sincroniza a árvore de comandos Slash com o Discord
    tryPlugin = await bot.tree.sync()
    print(f"Comandos Slash sincronizados: {len(tryPlugin)} comando(s)")
    print(f"========================================")


# 5. Criando o primeiro Slash Command simples: /ping
@bot.tree.command(name="ping", description="Responde com Pong! e a latência do bot.")
async def ping(interaction: discord.Interaction):
    # Calcula a latência em milissegundos
    latency = round(bot.latency * 1000)
    
    # ephemerally = True faz a mensagem ser visível APENAS para quem usou o comando
    await interaction.response.send_message(
        f"🏓 **Pong!** Latência atual: `{latency}ms`", 
        ephemeral=True
    )


# 6. Criando um Slash Command com parâmetros: /pomodoro_teste
@bot.tree.command(name="pomodoro_teste", description="Teste de configuração de tempo do Pomodoro.")
@app_commands.describe(foco="Tempo de foco em minutos", pausa="Tempo de pausa em minutos")
async def pomodoro_teste(interaction: discord.Interaction, foco: int = 25, pausa: int = 5):
    await interaction.response.send_message(
        f"⏱️ **Configuração recebida!**\n"
        f"• Tempo de Foco: `{foco}` minutos\n"
        f"• Tempo de Pausa: `{pausa}` minutos"
    )


# 7. Inicia o bot
if __name__ == "__main__":
    bot.run(TOKEN)