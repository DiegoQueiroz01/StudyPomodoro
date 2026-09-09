import asyncio
from enum import Enum, auto


class PomodoroStatus(Enum):
    STOPPED = "Encerrado"
    RUNNING = "Em andamento"
    PAUSED = "Pausado"


class PhaseType(Enum):
    WORK = "Foco"
    SHORT_BREAK = "Pausa Curta"
    LONG_BREAK = "Pausa Longa"


class PomodoroSession:
    """Gerencia os ciclos, participantes e o estado do temporizador do Pomodoro."""

    def __init__(
        self,
        voice_channel_id: int,
        initial_participants: list,
        work_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        cycles_before_long_break: int = 4,
    ):
        self.voice_channel_id = voice_channel_id
        self.participants = set(initial_participants)
        
        self.work_seconds = work_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.cycles_before_long_break = cycles_before_long_break

        self.status = PomodoroStatus.STOPPED
        self.current_cycle = 1
        self.phase = PhaseType.WORK
        self.remaining_seconds = self.work_seconds

    def add_participant(self, user_id: int):
        self.participants.add(user_id)

    def remove_participant(self, user_id: int):
        self.participants.discard(user_id)

    def start(self):
        self.status = PomodoroStatus.RUNNING

    def pause(self):
        if self.status == PomodoroStatus.RUNNING:
            self.status = PomodoroStatus.PAUSED

    def resume(self):
        if self.status == PomodoroStatus.PAUSED:
            self.status = PomodoroStatus.RUNNING

    def stop(self):
        self.status = PomodoroStatus.STOPPED
        self.current_cycle = 1
        self.phase = PhaseType.WORK
        self.remaining_seconds = self.work_seconds

    def next_phase(self) -> PhaseType:
        if self.phase == PhaseType.WORK:
            if self.current_cycle % self.cycles_before_long_break == 0:
                self.phase = PhaseType.LONG_BREAK
                self.remaining_seconds = self.long_break_seconds
            else:
                self.phase = PhaseType.SHORT_BREAK
                self.remaining_seconds = self.short_break_seconds
        else:
            self.phase = PhaseType.WORK
            self.remaining_seconds = self.work_seconds
            self.current_cycle += 1

        return self.phase

    def format_time(self) -> str:
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"