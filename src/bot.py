import os
import sys
import asyncio
import discord
from pathlib import Path
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent))

from services.pomodoro_service import PomodoroSession, PomodoroStatus, PhaseType

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True  # Permite escutar entradas/saídas do canal de voz

bot = commands.Bot(command_prefix="!", intents=intents)
sessions = {}


@bot.event
async def on_ready():
    print("========================================")
    print(f"Bot conectado como: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Comandos Slash sincronizados com sucesso: {len(synced)} comando(s)")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    print("========================================")


# EVENTO: Escuta quando alguém entra, sai ou troca de canal de voz
@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if member.bot:
        return  # Ignora outros bots

    guild_id = member.guild.id

    # Se não há sessão ativa neste servidor, não precisamos fazer nada
    if guild_id not in sessions or sessions[guild_id].status != PomodoroStatus.RUNNING:
        return

    session = sessions[guild_id]

    # Caso 1: O usuário ENTROU no canal onde o Pomodoro está rodando
    if after.channel and after.channel.id == session.voice_channel_id:
        if before.channel is None or before.channel.id != session.voice_channel_id:
            session.add_participant(member.id)
            print(f"[VOZ] {member.display_name} entrou na sessão do canal {after.channel.name}")

    # Caso 2: O usuário SAIU do canal onde o Pomodoro está rodando
    elif before.channel and before.channel.id == session.voice_channel_id:
        if after.channel is None or after.channel.id != session.voice_channel_id:
            session.remove_participant(member.id)
            print(f"[VOZ] {member.display_name} saiu da sessão do canal {before.channel.name}")


@bot.tree.command(name="ping", description="Responde com Pong! e a latência do bot.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 **Pong!** Latência atual: `{latency}ms`", ephemeral=True
    )


@bot.tree.command(
    name="pomodoro_iniciar",
    description="Inicia uma sessão Pomodoro no seu canal de voz.",
)
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
    user = interaction.user

    if not user.voice or not user.voice.channel:
        await interaction.response.send_message(
            "❌ **Você precisa estar conectado a um canal de voz** para iniciar o Pomodoro!",
            ephemeral=True,
        )
        return

    if guild_id in sessions and sessions[guild_id].status == PomodoroStatus.RUNNING:
        await interaction.response.send_message(
            "⚠️ Já existe uma sessão Pomodoro em andamento neste servidor!",
            ephemeral=True,
        )
        return

    voice_channel = user.voice.channel
    initial_member_ids = [m.id for m in voice_channel.members if not m.bot]

    session = PomodoroSession(
        voice_channel_id=voice_channel.id,
        initial_participants=initial_member_ids,
        work_minutes=foco,
        short_break_minutes=pausa_curta,
        long_break_minutes=pausa_longa,
    )
    session.start()
    sessions[guild_id] = session

    mentions = [f"<@{uid}>" for uid in session.participants]
    participants_text = ", ".join(mentions) if mentions else "Nenhum participante."

    await interaction.response.send_message(
        f"🚀 **Sessão Pomodoro Iniciada!**\n"
        f"🔊 **Canal de Voz:** {voice_channel.mention}\n"
        f"👥 **Estudantes ({len(session.participants)}):** {participants_text}\n"
        f"• **Fase Atual:** {session.phase.value}\n"
        f"• **Ciclo:** `{session.current_cycle}`\n"
        f"• **Duração:** `{session.format_time()}`"
    )

    channel = interaction.channel

    while session.status == PomodoroStatus.RUNNING:
        while session.remaining_seconds > 0 and session.status == PomodoroStatus.RUNNING:
            await asyncio.sleep(1)
            session.remaining_seconds -= 1

        if session.status == PomodoroStatus.RUNNING and session.remaining_seconds == 0:
            nova_fase = session.next_phase()

            # Gera as menções atualizadas dos membros que estão no canal
            current_mentions = [f"<@{uid}>" for uid in session.participants]
            mentions_text = " ".join(current_mentions) if current_mentions else ""

            if nova_fase == PhaseType.WORK:
                msg = (
                    f"🔔 **Hora de voltar ao foco em {voice_channel.mention}!** {mentions_text}\n"
                    f"🎯 **Ciclo {session.current_cycle} iniciado** | Duração: `{foco}` min."
                )
            elif nova_fase == PhaseType.SHORT_BREAK:
                msg = (
                    f"☕ **Hora da pausa em {voice_channel.mention}!** {mentions_text}\n"
                    f"🌴 **Pausa Curta iniciada** | Duração: `{pausa_curta}` min."
                )
            else:
                msg = (
                    f"🎉 **Parabéns pelos 4 ciclos no canal {voice_channel.mention}!** {mentions_text}\n"
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