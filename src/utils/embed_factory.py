import discord
from services.pomodoro_service import PhaseType, PomodoroStatus


class EmbedFactory:
    """Classe responsável por gerar Embeds padronizados e elegantes para o bot."""

    COLOR_WORK = discord.Color.red()  # Vermelho / Tomate
    COLOR_SHORT_BREAK = discord.Color.green()  # Verde / Descanso
    COLOR_LONG_BREAK = discord.Color.blue()  # Azul / Pausa Longa
    COLOR_INFO = discord.Color.gold()  # Amarelo / Info / Status

    @staticmethod
    def create_pomodoro_start_embed(
        voice_channel_name: str,
        participants: list,
        foco: int,
        pausa_curta: int,
        pausa_longa: int,
    ) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Sessão Pomodoro Iniciada!",
            description=f"Acompanhe o tempo de estudo no canal **{voice_channel_name}**.",
            color=EmbedFactory.COLOR_WORK,
        )

        mentions_text = (
            ", ".join([f"<@{uid}>" for uid in participants])
            if participants
            else "Nenhum participante."
        )

        embed.add_field(name="🔊 Canal de Voz", value=f"`{voice_channel_name}`", inline=True)
        embed.add_field(name="👥 Estudantes", value=f"`{len(participants)}` ativo(s)", inline=True)
        embed.add_field(name="⏱️ Configuração", value=f"`{foco}/{pausa_curta}/{pausa_longa}` min", inline=False)
        embed.add_field(name="📋 Participantes", value=mentions_text, inline=False)
        embed.set_footer(text="Mantenha o foco! O tempo está rodando.")
        return embed

    @staticmethod
    def create_phase_change_embed(
        phase: PhaseType,
        cycle: int,
        duration_minutes: int,
        participants: list,
        voice_channel_name: str,
    ) -> discord.Embed:
        if phase == PhaseType.WORK:
            title = f"🔔 Hora do Foco! (Ciclo {cycle})"
            description = f"Voltem ao trabalho no canal **{voice_channel_name}**!"
            color = EmbedFactory.COLOR_WORK
        elif phase == PhaseType.SHORT_BREAK:
            title = "☕ Pausa Curta"
            description = f"Hora de esticar as pernas e relaxar, turma do **{voice_channel_name}**!"
            color = EmbedFactory.COLOR_SHORT_BREAK
        else:
            title = "🎉 Pausa Longa!"
            description = f"Parabéns por completarem 4 ciclos no canal **{voice_channel_name}**!"
            color = EmbedFactory.COLOR_LONG_BREAK

        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name="⏱️ Duração", value=f"`{duration_minutes}` minutos", inline=True)

        if participants:
            mentions_text = " ".join([f"<@{uid}>" for uid in participants])
            embed.add_field(name="👥 Chamada de Voz", value=mentions_text, inline=False)

        embed.set_footer(text="Aproveite seu tempo!")
        return embed

    @staticmethod
    def create_status_embed(session, voice_channel_name: str) -> discord.Embed:
        status_color = (
            EmbedFactory.COLOR_WORK
            if session.status == PomodoroStatus.RUNNING
            else EmbedFactory.COLOR_INFO
        )

        embed = discord.Embed(
            title="📊 Painel de Status do Pomodoro",
            color=status_color,
        )

        mentions_text = (
            ", ".join([f"<@{uid}>" for uid in session.participants])
            if session.participants
            else "Nenhum participante no momento."
        )

        embed.add_field(name="📌 Estado", value=f"`{session.status.value}`", inline=True)
        embed.add_field(name="🔄 Fase Atual", value=f"`{session.phase.value}`", inline=True)
        embed.add_field(name="🔢 Ciclo", value=f"`{session.current_cycle}`", inline=True)
        embed.add_field(name="⏳ Tempo Restante", value=f"`{session.format_time()}`", inline=True)
        embed.add_field(name="🔊 Canal", value=f"`{voice_channel_name}`", inline=True)
        embed.add_field(name="👥 Estudantes", value=mentions_text, inline=False)

        return embed

    @staticmethod
    def create_profile_embed(user: discord.User, stats: dict) -> discord.Embed:
        minutes = stats["minutes"]
        cycles = stats["cycles"]
        hours = minutes // 60
        remaining_mins = minutes % 60

        embed = discord.Embed(
            title=f"📊 Perfil de Estudos - {user.display_name}",
            color=discord.Color.purple(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="⏱️ Tempo Total de Foco", value=f"`{hours}h {remaining_mins}min`", inline=True)
        embed.add_field(name="🍅 Ciclos Concluídos", value=f"`{cycles}` ciclos", inline=True)
        embed.set_footer(text="Continue praticando todos os dias!")
        return embed