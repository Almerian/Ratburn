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
                guild_id INTEGER PRIMARY KEY,
                staff_role_id INTEGER,
                detention_role_id INTEGER,
                detention_channel_id INTEGER,
                rat_trap_channel_id INTEGER,
                welcome_channel_id INTEGER,
                birthday_channel_id INTEGER,
                event_channel_id INTEGER,
                audit_log_channel_id INTEGER,
                timezone TEXT
            )
        """)
    
        self.connection.commit()
    
        existing_columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(guild_config)"
            ).fetchall()
        }
    
        new_columns = {
            "staff_role_id": "INTEGER",
            "detention_role_id": "INTEGER",
            "detention_channel_id": "INTEGER",
            "rat_trap_channel_id": "INTEGER",
            "welcome_channel_id": "INTEGER",
            "birthday_channel_id": "INTEGER",
            "event_channel_id": "INTEGER",
            "audit_log_channel_id": "INTEGER",
            "timezone": "TEXT",
        }
    
        for column, column_type in new_columns.items():
            if column not in existing_columns:
                self.connection.execute(
                    f"ALTER TABLE guild_config ADD COLUMN "
                    f"{column} {column_type}"
                )
    
        self.connection.commit()

    def ensure_guild(self, guild_id: int):
        self.connection.execute("""
            INSERT OR IGNORE INTO guild_config (guild_id)
            VALUES (?)
        """, (guild_id,))

        self.connection.commit()

    def get_config(self, guild_id: int):
        self.ensure_guild(guild_id)

        return self.connection.execute("""
            SELECT *
            FROM guild_config
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()

    def set_config(self, guild_id: int, setting: str, value):
        self.ensure_guild(guild_id)

        allowed_settings = {
            "staff_role_id",
            "detention_role_id",
            "detention_channel_id",
            "rat_trap_channel_id",
            "welcome_channel_id",
            "birthday_channel_id",
            "event_channel_id",
            "audit_log_channel_id",
            "timezone",
        }

        if setting not in allowed_settings:
            raise ValueError(f"Invalid configuration setting: {setting}")

        self.connection.execute(
            f"""
            UPDATE guild_config
            SET {setting} = ?
            WHERE guild_id = ?
            """,
            (value, guild_id)
        )

        self.connection.commit()

    def close(self):
        self.connection.close()
