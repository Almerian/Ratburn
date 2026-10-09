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
                rules_message_id INTEGER,
                icebreaker_channel_id INTEGER,
                icebreaker_enabled INTEGER NOT NULL DEFAULT 1,
                icebreaker_posting_time TEXT NOT NULL DEFAULT '09:00'
            )
        """)

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
            "icebreaker_channel_id": "INTEGER",
            "icebreaker_enabled": "INTEGER NOT NULL DEFAULT 1",
            "icebreaker_posting_time": "TEXT NOT NULL DEFAULT '09:00'",
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

                quiz_points INTEGER NOT NULL DEFAULT 0,
                quiz_questions_answered INTEGER NOT NULL DEFAULT 0,
                quiz_last_answered TEXT,

                profile_last_edited TEXT,

                PRIMARY KEY (guild_id, user_id)
            )
        """)

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
            "quiz_points": "INTEGER NOT NULL DEFAULT 0",
            "quiz_questions_answered": "INTEGER NOT NULL DEFAULT 0",
            "quiz_last_answered": "TEXT",
            "profile_last_edited": "TEXT",
        }

        for column, column_type in new_member_columns.items():
            if column not in existing_member_columns:
                self.connection.execute(
                    f"ALTER TABLE member_profiles ADD COLUMN "
                    f"{column} {column_type}"
                )

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS filtered_words (
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL COLLATE NOCASE,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, word)
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS discipline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                status TEXT NOT NULL DEFAULT 'active'
            )
        """)

        existing_discipline_columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(discipline)"
            ).fetchall()
        }

        if "expires_at" not in existing_discipline_columns:
            self.connection.execute(
                "ALTER TABLE discipline ADD COLUMN expires_at TEXT"
            )

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS discipline_config (
                guild_id INTEGER PRIMARY KEY,
                mute_demerit_threshold INTEGER,
                mute_duration_value INTEGER,
                mute_duration_unit TEXT,
                detention_demerit_threshold INTEGER,
                detention_duration_value INTEGER,
                detention_duration_unit TEXT,
                ban_demerit_threshold INTEGER,
                demerit_expiration_value INTEGER,
                demerit_expiration_unit TEXT
            )
        """)

        existing_discipline_columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(discipline_config)"
            ).fetchall()
        }

        new_discipline_columns = {
            "detention_duration_value": "INTEGER",
            "detention_duration_unit": "TEXT",
        }

        for column, column_type in new_discipline_columns.items():
            if column not in existing_discipline_columns:
                self.connection.execute(
                    f"ALTER TABLE discipline_config ADD COLUMN "
                    f"{column} {column_type}"
                )
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS icebreaker_custom_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                question TEXT NOT NULL COLLATE NOCASE,
                added_by INTEGER,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (guild_id, question)
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS icebreaker_question_usage (
                guild_id INTEGER NOT NULL,
                question_key TEXT NOT NULL,
                used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, question_key)
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS icebreaker_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                question_key TEXT NOT NULL,
                question_text TEXT NOT NULL,
                posted_date TEXT NOT NULL,
                posted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (guild_id, posted_date)
            )
        """)

        
        self.migrate_quiz_tables()

        self.connection.commit()

    def migrate_quiz_tables(self):
        quiz_scores_exists = self.connection.execute("""
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'quiz_scores'
        """).fetchone()

        quiz_answers_exists = self.connection.execute("""
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'quiz_answers'
        """).fetchone()

        if quiz_scores_exists:
            self.connection.execute("""
                INSERT OR IGNORE INTO member_profiles (
                    guild_id,
                    user_id
                )
                SELECT guild_id, user_id
                FROM quiz_scores
            """)

            self.connection.execute("""
                UPDATE member_profiles
                SET quiz_points = (
                    SELECT points
                    FROM quiz_scores
                    WHERE quiz_scores.guild_id = member_profiles.guild_id
                    AND quiz_scores.user_id = member_profiles.user_id
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM quiz_scores
                    WHERE quiz_scores.guild_id = member_profiles.guild_id
                    AND quiz_scores.user_id = member_profiles.user_id
                )
            """)

        if quiz_answers_exists:
            self.connection.execute("""
                INSERT OR IGNORE INTO member_profiles (
                    guild_id,
                    user_id
                )
                SELECT guild_id, user_id
                FROM quiz_answers
            """)

            self.connection.execute("""
                UPDATE member_profiles
                SET quiz_questions_answered = (
                    SELECT COUNT(*)
                    FROM quiz_answers
                    WHERE quiz_answers.guild_id = member_profiles.guild_id
                    AND quiz_answers.user_id = member_profiles.user_id
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM quiz_answers
                    WHERE quiz_answers.guild_id = member_profiles.guild_id
                    AND quiz_answers.user_id = member_profiles.user_id
                )
            """)

            self.connection.execute("""
                UPDATE member_profiles
                SET quiz_last_answered = (
                    SELECT MAX(quiz_date)
                    FROM quiz_answers
                    WHERE quiz_answers.guild_id = member_profiles.guild_id
                    AND quiz_answers.user_id = member_profiles.user_id
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM quiz_answers
                    WHERE quiz_answers.guild_id = member_profiles.guild_id
                    AND quiz_answers.user_id = member_profiles.user_id
                )
            """)

        if quiz_answers_exists:
            self.connection.execute("""
                DROP TABLE quiz_answers
            """)

        if quiz_scores_exists:
            self.connection.execute("""
                DROP TABLE quiz_scores
            """)

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
            "icebreaker_channel_id",
            "icebreaker_enabled",
            "icebreaker_posting_time",
        }

        if setting not in allowed_settings:
            raise ValueError(
                f"Invalid configuration setting: {setting}"
            )

        self.ensure_guild(guild_id)

        self.connection.execute(
            f"""
            UPDATE guild_config
            SET {setting} = ?
            WHERE guild_id = ?
            """,
            (value, guild_id)
        )

        self.connection.commit()

    def add_filtered_word(self, guild_id: int, word: str):
        self.connection.execute("""
            INSERT OR IGNORE INTO filtered_words (
                guild_id,
                word
            )
            VALUES (?, ?)
        """, (guild_id, word))

        self.connection.commit()

    def remove_filtered_word(self, guild_id: int, word: str):
        self.connection.execute("""
            DELETE FROM filtered_words
            WHERE guild_id = ?
            AND word = ?
        """, (guild_id, word))

        self.connection.commit()
    
    def clear_filtered_words(self, guild_id: int):
        self.connection.execute("""
            DELETE FROM filtered_words
            WHERE guild_id = ?
        """, (guild_id,))

        self.connection.commit()
    
    def reset_filtered_words_to_default(
        self,
        guild_id: int,
        default_words: list[str]
    ):
        self.connection.execute("""
            DELETE FROM filtered_words
            WHERE guild_id = ?
        """, (guild_id,))

        self.connection.executemany("""
            INSERT OR IGNORE INTO filtered_words (
                guild_id,
                word
            )
            VALUES (?, ?)
        """, [
            (guild_id, word)
            for word in default_words
        ])

        self.connection.commit()

    def get_filtered_words(self, guild_id: int):
        return self.connection.execute("""
            SELECT word
            FROM filtered_words
            WHERE guild_id = ?
            ORDER BY word COLLATE NOCASE
        """, (guild_id,)).fetchall()

    def add_discipline_record(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        reason: str,
        expires_at: str | None = None
    ):
        self.connection.execute("""
            INSERT INTO discipline (
                guild_id,
                user_id,
                action,
                reason,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            guild_id,
            user_id,
            action,
            reason,
            expires_at
        ))

        self.connection.commit()

    def get_active_discipline_records(
        self,
        guild_id: int,
        user_id: int
    ):
        return self.connection.execute("""
            SELECT *
            FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
            AND status = 'active'
            ORDER BY created_at ASC
        """, (
            guild_id,
            user_id
        )).fetchall()

    def mark_expired_detentions(self):
        self.connection.execute("""
            UPDATE discipline
            SET status = 'expired'
            WHERE action = 'detention'
            AND status = 'active'
            AND expires_at IS NOT NULL
            AND datetime(expires_at) <= datetime('now')
        """)

        self.connection.commit()

    def get_expired_detentions(self):
        return self.connection.execute("""
            SELECT *
            FROM discipline
            WHERE action = 'detention'
            AND status = 'expired'
            ORDER BY expires_at ASC
        """).fetchall()

    def complete_discipline_record(self, record_id: int):
        self.connection.execute("""
            UPDATE discipline
            SET status = 'complete'
            WHERE id = ?
        """, (record_id,))

        self.connection.commit()

    def get_demerit_count(
        self,
        guild_id: int,
        user_id: int
    ):
        return self.connection.execute("""
            SELECT COUNT(*)
            FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
            AND action = 'demerit'
            AND status = 'active'
        """, (
            guild_id,
            user_id
        )).fetchone()[0]

#==================================DO NOT REMOVE==================================
    def clear_discipline_records(
        self,
        guild_id: int,
        user_id: int
    ):
        self.connection.execute("""
            DELETE FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
        """, (
            guild_id,
            user_id
        ))

        self.connection.commit()
#==================================DO NOT REMOVE==================================

    def get_discipline_config(self, guild_id: int):
        return self.connection.execute("""
            SELECT *
            FROM discipline_config
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()

    def set_discipline_config(
        self,
        guild_id: int,
        setting: str,
        value
    ):
        allowed_settings = {
            "mute_demerit_threshold",
            "mute_duration_value",
            "mute_duration_unit",
            "detention_demerit_threshold",
            "detention_duration_value",
            "detention_duration_unit",
            "ban_demerit_threshold",
            "demerit_expiration_value",
            "demerit_expiration_unit",
        }

        if setting not in allowed_settings:
            raise ValueError(
                f"Invalid discipline configuration setting: {setting}"
            )

        self.connection.execute(
            f"""
            INSERT INTO discipline_config (
                guild_id,
                {setting}
            )
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET
                {setting} = excluded.{setting}
            """,
            (guild_id, value)
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
        """, (
            guild_id,
            user_id
        )).fetchone()

    def get_birthdays(
        self,
        guild_id: int,
        month: int,
        day: int
    ):
        return self.connection.execute("""
            SELECT *
            FROM member_profiles
            WHERE guild_id = ?
            AND birthday_month = ?
            AND birthday_day = ?
        """, (
            guild_id,
            month,
            day
        )).fetchall()

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

    def get_profile_last_edited(
        self,
        guild_id: int,
        user_id: int
    ):
        profile = self.get_member_profile(
            guild_id,
            user_id
        )

        return profile["profile_last_edited"]

    def set_profile_last_edited(
        self,
        guild_id: int,
        user_id: int,
        timestamp: str
    ):
        self.ensure_member(
            guild_id,
            user_id
        )

        self.connection.execute("""
            UPDATE member_profiles
            SET profile_last_edited = ?
            WHERE guild_id = ?
            AND user_id = ?
        """, (
            timestamp,
            guild_id,
            user_id
        ))

        self.connection.commit()

    def get_quiz_score(
        self,
        guild_id: int,
        user_id: int
    ):
        profile = self.get_member_profile(
            guild_id,
            user_id
        )

        return profile["quiz_points"]

    def add_quiz_point(
        self,
        guild_id: int,
        user_id: int
    ):
        self.ensure_member(
            guild_id,
            user_id
        )

        self.connection.execute("""
            UPDATE member_profiles
            SET quiz_points = quiz_points + 1
            WHERE guild_id = ?
            AND user_id = ?
        """, (
            guild_id,
            user_id
        ))

        self.connection.commit()

    def has_answered_quiz(
        self,
        guild_id: int,
        user_id: int,
        quiz_date: str
    ):
        profile = self.get_member_profile(
            guild_id,
            user_id
        )

        return profile["quiz_last_answered"] == quiz_date

    def record_quiz_answer(
        self,
        guild_id: int,
        user_id: int,
        quiz_date: str,
        correct: bool
    ):
        self.ensure_member(
            guild_id,
            user_id
        )

        cursor = self.connection.execute("""
            UPDATE member_profiles
            SET
                quiz_questions_answered =
                    quiz_questions_answered + 1,
                quiz_last_answered = ?
            WHERE guild_id = ?
            AND user_id = ?
            AND (
                quiz_last_answered IS NULL
                OR quiz_last_answered != ?
            )
        """, (
            quiz_date,
            guild_id,
            user_id,
            quiz_date
        ))

        if cursor.rowcount == 0:
            raise sqlite3.IntegrityError(
                "Quiz answer already recorded for this date."
            )

        self.connection.commit()


    def add_icebreaker_question(
        self,
        guild_id: int,
        question: str,
        added_by: int | None = None
    ):
        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        self.connection.execute("""
            INSERT OR IGNORE INTO icebreaker_custom_questions (
                guild_id,
                question,
                added_by
            )
            VALUES (?, ?, ?)
        """, (
            guild_id,
            question,
            added_by
        ))

        self.connection.commit()

    def get_icebreaker_questions(self, guild_id: int):
        return self.connection.execute("""
            SELECT *
            FROM icebreaker_custom_questions
            WHERE guild_id = ?
            ORDER BY question COLLATE NOCASE
        """, (guild_id,)).fetchall()

    def remove_icebreaker_question(
        self,
        guild_id: int,
        question_id: int
    ):
        self.connection.execute("""
            DELETE FROM icebreaker_custom_questions
            WHERE guild_id = ?
            AND id = ?
        """, (
            guild_id,
            question_id
        ))

        self.connection.commit()

    def get_icebreaker_used_questions(self, guild_id: int):
        return {
            row["question_key"]
            for row in self.connection.execute("""
                SELECT question_key
                FROM icebreaker_question_usage
                WHERE guild_id = ?
            """, (guild_id,)).fetchall()
        }

    def mark_icebreaker_question_used(
        self,
        guild_id: int,
        question_key: str
    ):
        self.connection.execute("""
            INSERT OR IGNORE INTO icebreaker_question_usage (
                guild_id,
                question_key
            )
            VALUES (?, ?)
        """, (
            guild_id,
            question_key
        ))

        self.connection.commit()

    def reset_icebreaker_question_usage(self, guild_id: int):
        self.connection.execute("""
            DELETE FROM icebreaker_question_usage
            WHERE guild_id = ?
        """, (guild_id,))

        self.connection.commit()

    def record_icebreaker_post(
        self,
        guild_id: int,
        question_key: str,
        question_text: str,
        posted_date: str
    ):
        self.connection.execute("""
            INSERT INTO icebreaker_history (
                guild_id,
                question_key,
                question_text,
                posted_date
            )
            VALUES (?, ?, ?, ?)
        """, (
            guild_id,
            question_key,
            question_text,
            posted_date
        ))

        self.connection.commit()

    def get_icebreaker_history(
        self,
        guild_id: int,
        limit: int = 30
    ):
        return self.connection.execute("""
            SELECT *
            FROM icebreaker_history
            WHERE guild_id = ?
            ORDER BY posted_date DESC
            LIMIT ?
        """, (
            guild_id,
            limit
        )).fetchall()

    def has_icebreaker_posted(
        self,
        guild_id: int,
        posted_date: str
    ) -> bool:
        return self.connection.execute("""
            SELECT 1
            FROM icebreaker_history
            WHERE guild_id = ?
            AND posted_date = ?
        """, (
            guild_id,
            posted_date
        )).fetchone() is not None


    def close(self):
        self.connection.close()
