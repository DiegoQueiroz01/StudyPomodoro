import sqlite3
from pathlib import Path

# Define o caminho do arquivo do banco de dados na raiz do projeto
DB_PATH = Path(__file__).parent.parent.parent / "pomodoro.db"


class DatabaseService:
    """Gerencia a conexão e operações no banco de dados SQLite."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Cria as tabelas do banco de dados caso não existam."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela para estatísticas acumuladas dos usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    total_focus_minutes INTEGER DEFAULT 0,
                    completed_cycles INTEGER DEFAULT 0,
                    last_study_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_focus_session(self, user_id: int, guild_id: int, minutes_studied: int):
        """Registra os minutos estudados e incrementa 1 ciclo para um usuário."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_stats (user_id, guild_id, total_focus_minutes, completed_cycles, last_study_date)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_focus_minutes = total_focus_minutes + excluded.total_focus_minutes,
                    completed_cycles = completed_cycles + 1,
                    last_study_date = CURRENT_TIMESTAMP
            """, (user_id, guild_id, minutes_studied))
            conn.commit()

    def get_user_stats(self, user_id: int) -> dict:
        """Retorna o total de minutos e ciclos de um usuário específico."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT total_focus_minutes, completed_cycles
                FROM user_stats
                WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            
            if row:
                return {"minutes": row[0], "cycles": row[1]}
            return {"minutes": 0, "cycles": 0}