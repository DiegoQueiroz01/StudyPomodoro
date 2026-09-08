import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# 1. Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Verificação de segurança: garante que o Token foi encontrado
if not TOKEN:
    raise ValueError("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")

# 2. Configura as permissões/eventos (Intents) do Bot
intents = discord.Intents.default()
intents.members = True  # Necessário para rastrear membros nos canais de voz
intents.message_content = False  # Mantemos desativado por enquanto (usaremos Slash Commands)

# 3. Instancia o cliente do Bot
# command_prefix define o prefixo para comandos legados (usaremos '!' temporariamente para testes)
bot = commands.Bot(command_prefix="!", intents=intents)


# 4. Evento disparado quando o bot se conecta com sucesso ao Discord
@bot.event
async def on_ready():
    print(f"========================================")
    print(f"Bot conectado com sucesso!")
    print(f"Nome do Bot: {bot.user.name}")
    print(f"ID do Bot:   {bot.user.id}")
    print(f"========================================")


# 5. Executa o bot utilizando o Token do .env
if __name__ == "__main__":
    bot.run(TOKEN)