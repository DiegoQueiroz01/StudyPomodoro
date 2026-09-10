import asyncio
import discord
from discord.ext import commands
from discord import app_commands

from services.pomodoro_service import PomodoroSession, PomodoroStatus, PhaseType
from services.database_service import DatabaseService
from services.audio_service import AudioService
from utils.embed_factory import EmbedFactory


class PomodoroCog(commands.Cog):
    """Cog responsável pelo gerenciamento de sessões Pomodoro, áudio e perfil do usuário."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = DatabaseService()
        self.sessions = {}

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if member.bot:
            return

        guild_id = member.guild.id
        if guild_id not in self.sessions or self.sessions[guild_id].status == PomodoroStatus.STOPPED:
            return

        session = self.sessions[guild_id]

        if after.channel and after.channel.id == session.voice_channel_id:
            if before.channel is None or before.channel.id != session.voice_channel_id:
                session.add_participant(member.id)

        elif before.channel and before.channel.id == session.voice_channel_id:
            if after.channel is None or after.channel.id != session.voice_channel_id:
                session.remove_participant(member.id)

    @app_commands.command(name="ping", description="Responde com Pong! e a latência do bot.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 **Pong!** Latência atual: `{latency}ms`", ephemeral=True
        )

    @app_commands.command(name="pomodoro_iniciar", description="Inicia uma sessão Pomodoro no seu canal de voz.")
    @app_commands.describe(
        foco="Tempo de foco em minutos (padrão: 50)",
        pausa_curta="Tempo de pausa curta em minutos (padrão: 10)",
        pausa_longa="Tempo de pausa longa em minutos (padrão: 15)",
    )
    async def pomodoro_iniciar(
        self,
        interaction: discord.Interaction,
        foco: int = 50,
        pausa_curta: int = 10,
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

        if guild_id in self.sessions and self.sessions[guild_id].status != PomodoroStatus.STOPPED:
            await interaction.response.send_message(
                "⚠️ Já existe uma sessão Pomodoro ativa ou pausada neste servidor!",
                ephemeral=True,
            )
            return

        # Avisa ao Discord que estamos processando (evita o erro 10062 Unknown interaction)
        await interaction.response.defer()

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
        self.sessions[guild_id] = session

        embed = EmbedFactory.create_pomodoro_start_embed(
            voice_channel_name=voice_channel.name,
            participants=list(session.participants),
            foco=foco,
            pausa_curta=pausa_curta,
            pausa_longa=pausa_longa,
        )

        await interaction.followup.send(embed=embed)
        channel = interaction.channel

        # Conecta ao canal de voz e reproduz áudio
        voice_client = await AudioService.get_or_connect_voice(voice_channel)
        await AudioService.play_sound_then_music(
            voice_client, "start_focus.mp3", "focus_music.mp3"
        )

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
                        self.db.record_focus_session(
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

                if nova_fase == PhaseType.WORK:
                    await AudioService.play_sound_then_music(
                        voice_client, "start_focus.mp3", "focus_music.mp3"
                    )
                else:
                    await AudioService.play_sound_then_music(
                        voice_client, "start_break.mp3", "break_music.mp3"
                    )

                phase_embed = EmbedFactory.create_phase_change_embed(
                    phase=nova_fase,
                    cycle=session.current_cycle,
                    duration_minutes=duration,
                    participants=list(session.participants),
                    voice_channel_name=voice_channel.name,
                )

                await channel.send(embed=phase_embed)

    @app_commands.command(name="pomodoro_pausar", description="Pausa temporariamente o cronômetro do Pomodoro.")
    async def pomodoro_pausar(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self.sessions or self.sessions[guild_id].status != PomodoroStatus.RUNNING:
            await interaction.response.send_message(
                "⚠️ Não há nenhuma sessão em andamento para pausar.", ephemeral=True
            )
            return

        self.sessions[guild_id].pause()
        if interaction.guild.voice_client:
            AudioService.stop_audio(interaction.guild.voice_client)

        await interaction.response.send_message("⏸️ **Sessão Pomodoro e áudio pausados!**")

    @app_commands.command(name="pomodoro_continuar", description="Retoma o cronômetro do Pomodoro pausado.")
    async def pomodoro_continuar(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self.sessions or self.sessions[guild_id].status != PomodoroStatus.PAUSED:
            await interaction.response.send_message("⚠️ A sessão atual não está pausada.", ephemeral=True)
            return

        session = self.sessions[guild_id]
        session.resume()

        if interaction.guild.voice_client:
            voice_client = interaction.guild.voice_client
            if session.phase == PhaseType.WORK:
                await AudioService.play_sound_then_music(
                    voice_client, "start_focus.mp3", "focus_music.mp3"
                )
            else:
                await AudioService.play_sound_then_music(
                    voice_client, "start_break.mp3", "break_music.mp3"
                )

        await interaction.response.send_message("▶️ **Sessão Pomodoro e áudio retomados!**")

    @app_commands.command(name="pomodoro_status", description="Exibe o status e tempo restante da sessão atual.")
    async def pomodoro_status(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self.sessions or self.sessions[guild_id].status == PomodoroStatus.STOPPED:
            await interaction.response.send_message(
                "❌ Nenhuma sessão Pomodoro está ativa neste servidor.", ephemeral=True
            )
            return

        session = self.sessions[guild_id]
        voice_channel = self.bot.get_channel(session.voice_channel_id)
        channel_name = voice_channel.name if voice_channel else "Canal de Voz"

        embed = EmbedFactory.create_status_embed(session, voice_channel_name=channel_name)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="perfil", description="Exibe suas estatísticas acumuladas de estudo.")
    async def perfil(self, interaction: discord.Interaction):
        user_stats = self.db.get_user_stats(interaction.user.id)
        embed = EmbedFactory.create_profile_embed(user=interaction.user, stats=user_stats)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pomodoro_parar", description="Cancela e encerra a sessão Pomodoro atual.")
    async def pomodoro_parar(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if guild_id not in self.sessions or self.sessions[guild_id].status == PomodoroStatus.STOPPED:
            await interaction.response.send_message(
                "❌ Nenhuma sessão ativa encontrada para este servidor.", ephemeral=True
            )
            return

        self.sessions[guild_id].stop()

        if interaction.guild.voice_client:
            AudioService.stop_audio(interaction.guild.voice_client)
            await AudioService.disconnect_voice(interaction.guild)

        await interaction.response.send_message("🛑 **Sessão Pomodoro encerrada e bot desconectado da voz!**")


async def setup(bot: commands.Bot):
    """Função obrigatória para carregar a Cog."""
    await bot.add_cog(PomodoroCog(bot))