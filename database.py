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
                timezone TEXT,
                rules_channel_id INTEGER,
                rules_message_id INTEGER
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
            "rules_channel_id": "INTEGER",
            "rules_message_id": "INTEGER",
        }

        for column, column_type in new_columns.items():
            if column not in existing_columns:
                self.connection.execute(
                    f"ALTER TABLE guild_config ADD COLUMN "
                    f"{column} {column_type}"
                )

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS member_profiles (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                birthday_month INTEGER,
                birthday_day INTEGER,
                birthday_year INTEGER,

                pronouns TEXT,
                pronoun_index INTEGER NOT NULL DEFAULT 0,

                nickname TEXT,

                timezone TEXT,

                rules_acknowledged INTEGER NOT NULL DEFAULT 0,
                rules_acknowledged_at TEXT,

                onboarding_message_id INTEGER,
                onboarding_step TEXT,
                onboarding_completed_at TEXT,

                PRIMARY KEY (guild_id, user_id)
            )
        """)

        self.connection.commit()

        existing_member_columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(member_profiles)"
            ).fetchall()
        }

        new_member_columns = {
            "birthday_month": "INTEGER",
            "birthday_day": "INTEGER",
            "birthday_year": "INTEGER",
            "pronouns": "TEXT",
            "pronoun_index": "INTEGER NOT NULL DEFAULT 0",
            "nickname": "TEXT",
            "timezone": "TEXT",
            "rules_acknowledged": "INTEGER NOT NULL DEFAULT 0",
            "rules_acknowledged_at": "TEXT",
            "onboarding_message_id": "INTEGER",
            "onboarding_step": "TEXT",
            "onboarding_completed_at": "TEXT",
        }

        for column, column_type in new_member_columns.items():
            if column not in existing_member_columns:
                self.connection.execute(
                    f"ALTER TABLE member_profiles ADD COLUMN "
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
            "rules_channel_id",
            "rules_message_id",
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

    def ensure_member(self, guild_id: int, user_id: int):
        self.connection.execute("""
            INSERT OR IGNORE INTO member_profiles (
                guild_id,
                user_id
            )
            VALUES (?, ?)
        """, (guild_id, user_id))

        self.connection.commit()

    def get_member_profile(self, guild_id: int, user_id: int):
        self.ensure_member(guild_id, user_id)

        return self.connection.execute("""
            SELECT *
            FROM member_profiles
            WHERE guild_id = ?
            AND user_id = ?
        """, (guild_id, user_id)).fetchone()

    def set_member_profile(
        self,
        guild_id: int,
        user_id: int,
        setting: str,
        value
    ):
        allowed_settings = {
            "birthday_month",
            "birthday_day",
            "birthday_year",
            "pronouns",
            "pronoun_index",
            "nickname",
            "timezone",
            "rules_acknowledged",
            "rules_acknowledged_at",
            "onboarding_message_id",
            "onboarding_step",
            "onboarding_completed_at",
        }

        if setting not in allowed_settings:
            raise ValueError(
                f"Invalid member profile setting: {setting}"
            )

        self.ensure_member(guild_id, user_id)

        self.connection.execute(
            f"""
            UPDATE member_profiles
            SET {setting} = ?
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (value, guild_id, user_id)
        )

        self.connection.commit()

    def close(self):
        self.connection.close()
