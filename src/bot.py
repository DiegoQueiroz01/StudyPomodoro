import os
import sys
import asyncio
import discord
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Garante que a pasta 'src' está no caminho de importação
sys.path.append(str(Path(__file__).parent))

from services.pomodoro_service import PomodoroSession, PomodoroStatus, PhaseType

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
sessions = {}


@bot.event
async def on_ready():
    print("========================================")
    print(f"Bot conectado como: {bot.user.name}")
    try:
        # Sincronização forçada dos comandos Slash
        synced = await bot.tree.sync()
        print(f"Comandos Slash sincronizados com sucesso: {len(synced)} comando(s)")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    print("========================================")


@bot.tree.command(name="ping", description="Responde com Pong! e a latência do bot.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 **Pong!** Latência atual: `{latency}ms`", ephemeral=True
    )


@bot.tree.command(name="pomodoro_iniciar", description="Inicia uma sessão de Pomodoro completa.")
@app_commands.describe(
    foco="Tempo de foco em minutos (padrão: 25)",
    pausa_curta="Tempo de pausa curta em minutos (padrão: 5)",
    pausa_longa="Tempo de pausa longa em minutos (padrão: 15)",
)
async def pomodoro_iniciar(
    interaction: discord.Interaction,
    foco: int = 25,
    pausa_curta: int = 5,
    pausa_longa: int = 15,
):
    guild_id = interaction.guild_id

    if guild_id in sessions and sessions[guild_id].status == PomodoroStatus.RUNNING:
        await interaction.response.send_message(
            "⚠️ Já existe uma sessão Pomodoro ativa neste servidor!", ephemeral=True
        )
        return

    session = PomodoroSession(
        work_minutes=foco,
        short_break_minutes=pausa_curta,
        long_break_minutes=pausa_longa,
    )
    session.start()
    sessions[guild_id] = session

    await interaction.response.send_message(
        f"🚀 **Sessão Pomodoro Iniciada!**\n"
        f"• **Fase Atual:** {session.phase.value}\n"
        f"• **Ciclo:** `{session.current_cycle}`\n"
        f"• **Duração:** `{session.format_time()}`"
    )

    channel = interaction.channel

    # Loop contínuo que transita automaticamente entre Foco e Pausas
    while session.status == PomodoroStatus.RUNNING:
        while session.remaining_seconds > 0 and session.status == PomodoroStatus.RUNNING:
            await asyncio.sleep(1)
            session.remaining_seconds -= 1

        # Transição de fase se a contagem zerar
        if session.status == PomodoroStatus.RUNNING and session.remaining_seconds == 0:
            nova_fase = session.next_phase()

            if nova_fase == PhaseType.WORK:
                msg = (
                    f"🔔 **Hora de voltar ao trabalho!**\n"
                    f"🎯 **Ciclo {session.current_cycle} iniciado** | Duração: `{foco}` min."
                )
            elif nova_fase == PhaseType.SHORT_BREAK:
                msg = (
                    f"☕ **Hora de descansar!**\n"
                    f"🌴 **Pausa Curta iniciada** | Duração: `{pausa_curta}` min."
                )
            else:
                msg = (
                    f"🎉 **Excelente progresso! Você completou 4 ciclos!**\n"
                    f"🛌 **Pausa Longa iniciada** | Duração: `{pausa_longa}` min."
                )

            await channel.send(msg)


@bot.tree.command(name="pomodoro_parar", description="Cancela a sessão Pomodoro atual.")
async def pomodoro_parar(interaction: discord.Interaction):
    guild_id = interaction.guild_id

    if guild_id not in sessions or sessions[guild_id].status == PomodoroStatus.STOPPED:
        await interaction.response.send_message(
            "❌ Nenhuma sessão ativa encontrada para este servidor.", ephemeral=True
        )
        return

    sessions[guild_id].stop()
    await interaction.response.send_message("🛑 **Sessão Pomodoro encerrada!**")


if __name__ == "__main__":
    bot.run(TOKEN)