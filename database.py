import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/ratburn.db")


class Database:
    def __init__(self):
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(DATABASE_PATH)
        self.connection.row_factory = sqlite3.Row

        self.initialize()

    def initialize(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY
            )
        """)

        self.connection.commit()

    def close(self):
        self.connection.close()
