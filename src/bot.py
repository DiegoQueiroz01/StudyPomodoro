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
from services.database_service import DatabaseService
from utils.embed_factory import EmbedFactory

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = DatabaseService()
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


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if member.bot:
        return

    guild_id = member.guild.id

    if guild_id not in sessions or sessions[guild_id].status == PomodoroStatus.STOPPED:
        return

    session = sessions[guild_id]

    if after.channel and after.channel.id == session.voice_channel_id:
        if before.channel is None or before.channel.id != session.voice_channel_id:
            session.add_participant(member.id)

    elif before.channel and before.channel.id == session.voice_channel_id:
        if after.channel is None or after.channel.id != session.voice_channel_id:
            session.remove_participant(member.id)


@bot.tree.command(name="ping", description="Responde com Pong! e a latência do bot.")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🏓 **Pong!** Latência atual: `{latency}ms`", ephemeral=True
    )


@bot.tree.command(name="pomodoro_iniciar", description="Inicia uma sessão Pomodoro no seu canal de voz.")
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

    if guild_id in sessions and sessions[guild_id].status != PomodoroStatus.STOPPED:
        await interaction.response.send_message(
            "⚠️ Já existe uma sessão Pomodoro ativa ou pausada neste servidor!",
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

    embed = EmbedFactory.create_pomodoro_start_embed(
        voice_channel_name=voice_channel.name,
        participants=list(session.participants),
        foco=foco,
        pausa_curta=pausa_curta,
        pausa_longa=pausa_longa,
    )

    await interaction.response.send_message(embed=embed)
    channel = interaction.channel

    while session.status != PomodoroStatus.STOPPED:
        if session.status == PomodoroStatus.RUNNING and session.remaining_seconds > 0:
            await asyncio.sleep(1)
            if session.status == PomodoroStatus.RUNNING:
                session.remaining_seconds -= 1
        elif session.status == PomodoroStatus.PAUSED:
            await asyncio.sleep(1)
            continue

        if session.status == PomodoroStatus.RUNNING and session.remaining_seconds == 0:
            current_phase = session.phase

            if current_phase == PhaseType.WORK:
                for participant_id in session.participants:
                    db.record_focus_session(
                        user_id=participant_id,
                        guild_id=guild_id,
                        minutes_studied=foco,
                    )

            nova_fase = session.next_phase()
            duration = (
                foco
                if nova_fase == PhaseType.WORK
                else (pausa_curta if nova_fase == PhaseType.SHORT_BREAK else pausa_longa)
            )

            phase_embed = EmbedFactory.create_phase_change_embed(
                phase=nova_fase,
                cycle=session.current_cycle,
                duration_minutes=duration,
                participants=list(session.participants),
                voice_channel_name=voice_channel.name,
            )

            await channel.send(embed=phase_embed)


@bot.tree.command(name="pomodoro_pausar", description="Pausa temporariamente o cronômetro do Pomodoro.")
async def pomodoro_pausar(interaction: discord.Interaction):
    guild_id = interaction.guild_id

    if guild_id not in sessions or sessions[guild_id].status != PomodoroStatus.RUNNING:
        await interaction.response.send_message(
            "⚠️ Não há nenhuma sessão em andamento para pausar.", ephemeral=True
        )
        return

    sessions[guild_id].pause()
    await interaction.response.send_message("⏸️ **Sessão Pomodoro pausada!**")


@bot.tree.command(name="pomodoro_continuar", description="Retoma o cronômetro do Pomodoro pausado.")
async def pomodoro_continuar(interaction: discord.Interaction):
    guild_id = interaction.guild_id

    if guild_id not in sessions or sessions[guild_id].status != PomodoroStatus.PAUSED:
        await interaction.response.send_message(
            "⚠️ A sessão atual não está pausada.", ephemeral=True
        )
        return

    sessions[guild_id].resume()
    await interaction.response.send_message("▶️ **Sessão Pomodoro retomada!**")


@bot.tree.command(name="pomodoro_status", description="Exibe o status e tempo restante da sessão atual.")
async def pomodoro_status(interaction: discord.Interaction):
    guild_id = interaction.guild_id

    if guild_id not in sessions or sessions[guild_id].status == PomodoroStatus.STOPPED:
        await interaction.response.send_message(
            "❌ Nenhuma sessão Pomodoro está ativa neste servidor.", ephemeral=True
        )
        return

    session = sessions[guild_id]
    voice_channel = bot.get_channel(session.voice_channel_id)
    channel_name = voice_channel.name if voice_channel else "Canal de Voz"

    embed = EmbedFactory.create_status_embed(session, voice_channel_name=channel_name)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="perfil", description="Exibe suas estatísticas acumuladas de estudo.")
async def perfil(interaction: discord.Interaction):
    user_stats = db.get_user_stats(interaction.user.id)
    embed = EmbedFactory.create_profile_embed(user=interaction.user, stats=user_stats)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pomodoro_parar", description="Cancela e encerra a sessão Pomodoro atual.")
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