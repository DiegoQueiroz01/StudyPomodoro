import asyncio
from enum import Enum, auto


class PomodoroStatus(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class PhaseType(Enum):
    WORK = "Foco"
    SHORT_BREAK = "Pausa Curta"
    LONG_BREAK = "Pausa Longa"


class PomodoroSession:
    """Gerencia a transição de ciclos e contagem de tempo do Pomodoro."""

    def __init__(
        self,
        work_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        cycles_before_long_break: int = 4,
    ):
        self.work_seconds = work_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.cycles_before_long_break = cycles_before_long_break

        self.status = PomodoroStatus.STOPPED
        self.current_cycle = 1
        self.phase = PhaseType.WORK
        self.remaining_seconds = self.work_seconds

    def start(self):
        """Inicia a sessão."""
        self.status = PomodoroStatus.RUNNING

    def pause(self):
        """Pausa o temporizador."""
        if self.status == PomodoroStatus.RUNNING:
            self.status = PomodoroStatus.PAUSED

    def resume(self):
        """Retoma a sessão."""
        if self.status == PomodoroStatus.PAUSED:
            self.status = PomodoroStatus.RUNNING

    def stop(self):
        """Reseta o estado completo da sessão."""
        self.status = PomodoroStatus.STOPPED
        self.current_cycle = 1
        self.phase = PhaseType.WORK
        self.remaining_seconds = self.work_seconds

    def next_phase(self) -> PhaseType:
        """Calcula e alterna para a próxima fase do Pomodoro."""
        if self.phase == PhaseType.WORK:
            # Se concluiu a quantidade de ciclos para a pausa longa
            if self.current_cycle % self.cycles_before_long_break == 0:
                self.phase = PhaseType.LONG_BREAK
                self.remaining_seconds = self.long_break_seconds
            else:
                self.phase = PhaseType.SHORT_BREAK
                self.remaining_seconds = self.short_break_seconds
        else:
            # Saindo de uma pausa (curta ou longa) e voltando ao foco
            self.phase = PhaseType.WORK
            self.remaining_seconds = self.work_seconds
            self.current_cycle += 1

        return self.phase

    def format_time(self) -> str:
        """Formata os segundos em MM:SS."""
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"