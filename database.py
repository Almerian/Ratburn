import sqlite3
from pathlib import Path


DATABASE_PATH = Path("data/ratburn.db")


class Database:
    def __init__(self):
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(DATABASE_PATH)
        self.connection.execute("PRAGMA foreign_keys = ON")
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
                birthdays_enabled INTEGER NOT NULL DEFAULT 1,
                event_channel_id INTEGER,
                events_enabled INTEGER NOT NULL DEFAULT 1,

                monthly_calendar_enabled INTEGER NOT NULL DEFAULT 0,
                monthly_calendar_channel_id INTEGER,
                monthly_calendar_last_posted TEXT,
                monthly_calendar_holiday_regions TEXT NOT NULL DEFAULT '["US"]',
                monthly_calendar_message_id INTEGER,
                monthly_calendar_guild_id INTEGER,

                audit_log_channel_id INTEGER,
                timezone TEXT,
                rules_channel_id INTEGER,
                rules_message_id INTEGER,
                icebreaker_channel_id INTEGER,
                icebreaker_enabled INTEGER NOT NULL DEFAULT 1,
                icebreaker_posting_time TEXT NOT NULL DEFAULT '09:00',
                quiz_enabled INTEGER NOT NULL DEFAULT 1,
                quiz_posting_time TEXT NOT NULL DEFAULT '10:00',
                ratburn_responses_enabled INTEGER NOT NULL DEFAULT 1
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
            "birthdays_enabled": "INTEGER NOT NULL DEFAULT 1",
            "event_channel_id": "INTEGER",
            "events_enabled": "INTEGER NOT NULL DEFAULT 1",

            "monthly_calendar_enabled": "INTEGER NOT NULL DEFAULT 0",
            "monthly_calendar_channel_id": "INTEGER",
            "monthly_calendar_last_posted": "TEXT",
            "monthly_calendar_holiday_regions": (
                "TEXT NOT NULL DEFAULT '[\"US\"]'"
            ),
            "monthly_calendar_message_id": "INTEGER",
            "monthly_calendar_guild_id": "INTEGER",

            "audit_log_channel_id": "INTEGER",
            "timezone": "TEXT",
            "rules_channel_id": "INTEGER",
            "rules_message_id": "INTEGER",
            "icebreaker_channel_id": "INTEGER",
            "icebreaker_enabled": "INTEGER NOT NULL DEFAULT 1",
            "icebreaker_posting_time": "TEXT NOT NULL DEFAULT '09:00'",
            "quiz_enabled": "INTEGER NOT NULL DEFAULT 1",
            "quiz_posting_time": "TEXT NOT NULL DEFAULT '10:00'",
            "ratburn_responses_enabled": "INTEGER NOT NULL DEFAULT 1",
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

        existing_discipline_config_columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(discipline_config)"
            ).fetchall()
        }

        new_discipline_config_columns = {
            "detention_duration_value": "INTEGER",
            "detention_duration_unit": "TEXT",
        }

        for column, column_type in new_discipline_config_columns.items():
            if column not in existing_discipline_config_columns:
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

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS reaction_role_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER,
                title TEXT NOT NULL DEFAULT 'Choose your roles!',
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'published')),
                draft_expires_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS reaction_role_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL DEFAULT 0,
                role_color INTEGER,
                role_icon TEXT,
                channel_permissions TEXT,
                FOREIGN KEY (post_id)
                    REFERENCES reaction_role_posts(id)
                    ON DELETE CASCADE,
                UNIQUE (post_id, role_id),
                UNIQUE (post_id, emoji)
            )
        """)

        existing_reaction_role_entry_columns = {
            row["name"]
            for row in self.connection.execute(
                "PRAGMA table_info(reaction_role_entries)"
            ).fetchall()
        }

        if "role_icon" not in existing_reaction_role_entry_columns:
            self.connection.execute(
                "ALTER TABLE reaction_role_entries ADD COLUMN role_icon TEXT"
            )

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS monthly_calendar_edits (
                message_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                holiday_date TEXT NOT NULL,
                holiday_name TEXT NOT NULL,
                action TEXT NOT NULL DEFAULT 'add'
                    CHECK (action IN ('add', 'move', 'remove')),
                PRIMARY KEY (
                    message_id,
                    holiday_date,
                    holiday_name
                )
            )
        """)

        self.migrate_quiz_tables()
        self.connection.commit()

    # ---------------- Quiz migration ----------------

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
                    guild_id, user_id
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
                    guild_id, user_id
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
            self.connection.execute("DROP TABLE quiz_answers")

        if quiz_scores_exists:
            self.connection.execute("DROP TABLE quiz_scores")

    # ---------------- Guild configuration ----------------

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
            "birthdays_enabled",
            "event_channel_id",
            "events_enabled",

            "monthly_calendar_enabled",
            "monthly_calendar_channel_id",
            "monthly_calendar_last_posted",
            "monthly_calendar_holiday_regions",
            "monthly_calendar_message_id",
            "monthly_calendar_guild_id",

            "audit_log_channel_id",
            "timezone",
            "rules_channel_id",
            "rules_message_id",
            "icebreaker_channel_id",
            "icebreaker_enabled",
            "icebreaker_posting_time",
            "quiz_enabled",
            "quiz_posting_time",
            "ratburn_responses_enabled",
        }

        if setting not in allowed_settings:
            raise ValueError(
                f"Invalid configuration setting: {setting}"
            )

        self.ensure_guild(guild_id)
        self.connection.execute(
            f"UPDATE guild_config SET {setting} = ? WHERE guild_id = ?",
            (value, guild_id),
        )
        self.connection.commit()

    # ---------------- Filtered words ----------------

    def add_filtered_word(self, guild_id: int, word: str):
        self.connection.execute("""
            INSERT OR IGNORE INTO filtered_words (guild_id, word)
            VALUES (?, ?)
        """, (guild_id, word))
        self.connection.commit()

    def remove_filtered_word(self, guild_id: int, word: str):
        self.connection.execute("""
            DELETE FROM filtered_words
            WHERE guild_id = ? AND word = ?
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
        default_words: list[str],
    ):
        self.connection.execute("""
            DELETE FROM filtered_words
            WHERE guild_id = ?
        """, (guild_id,))

        self.connection.executemany("""
            INSERT OR IGNORE INTO filtered_words (guild_id, word)
            VALUES (?, ?)
        """, [(guild_id, word) for word in default_words])

        self.connection.commit()

    def get_filtered_words(self, guild_id: int):
        return self.connection.execute("""
            SELECT word
            FROM filtered_words
            WHERE guild_id = ?
            ORDER BY word COLLATE NOCASE
        """, (guild_id,)).fetchall()

    # ---------------- Discipline ----------------

    def add_discipline_record(
        self,
        guild_id: int,
        user_id: int,
        action: str,
        reason: str,
        expires_at: str | None = None,
    ):
        self.connection.execute("""
            INSERT INTO discipline (
                guild_id, user_id, action, reason, expires_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (guild_id, user_id, action, reason, expires_at))
        self.connection.commit()

    def get_active_discipline_records(self, guild_id: int, user_id: int):
        return self.connection.execute("""
            SELECT *
            FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
            AND status = 'active'
            ORDER BY created_at ASC
        """, (guild_id, user_id)).fetchall()

    def get_retired_discipline_records(self, guild_id: int, user_id: int):
        return self.connection.execute("""
            SELECT *
            FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
            AND (
                status != 'active'
                OR (
                    expires_at IS NOT NULL
                    AND datetime(expires_at) <= datetime('now')
                )
            )
            ORDER BY created_at DESC
        """, (guild_id, user_id)).fetchall()

    def get_lifetime_demerit_count(self, guild_id: int, user_id: int) -> int:
        return self.connection.execute("""
            SELECT COUNT(*)
            FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
            AND action = 'demerit'
        """, (guild_id, user_id)).fetchone()[0]

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

    def get_demerit_count(self, guild_id: int, user_id: int):
        return self.connection.execute("""
            SELECT COUNT(*)
            FROM discipline
            WHERE guild_id = ?
            AND user_id = ?
            AND action = 'demerit'
            AND status = 'active'
        """, (guild_id, user_id)).fetchone()[0]

    #==================================DO NOT REMOVE==================================
    def clear_discipline_records(self, guild_id: int, user_id: int):
        self.connection.execute("""
            DELETE FROM discipline
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        self.connection.commit()
    #==================================DO NOT REMOVE==================================

    def get_discipline_config(self, guild_id: int):
        return self.connection.execute("""
            SELECT *
            FROM discipline_config
            WHERE guild_id = ?
        """, (guild_id,)).fetchone()

    def set_discipline_config(self, guild_id: int, setting: str, value):
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
            INSERT INTO discipline_config (guild_id, {setting})
            VALUES (?, ?)
            ON CONFLICT(guild_id)
            DO UPDATE SET {setting} = excluded.{setting}
            """,
            (guild_id, value),
        )
        self.connection.commit()

    # ---------------- Member profiles ----------------

    def ensure_member(self, guild_id: int, user_id: int):
        self.connection.execute("""
            INSERT OR IGNORE INTO member_profiles (guild_id, user_id)
            VALUES (?, ?)
        """, (guild_id, user_id))
        self.connection.commit()

    def get_member_profile(self, guild_id: int, user_id: int):
        self.ensure_member(guild_id, user_id)
        return self.connection.execute("""
            SELECT *
            FROM member_profiles
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id)).fetchone()

    def get_birthdays(self, guild_id: int, month: int, day: int):
        return self.connection.execute("""
            SELECT *
            FROM member_profiles
            WHERE guild_id = ?
            AND birthday_month = ?
            AND birthday_day = ?
        """, (guild_id, month, day)).fetchall()

    def get_birthdays_for_month(self, guild_id: int, month: int):
        return self.connection.execute(
            """
            SELECT user_id, birthday_month, birthday_day, nickname
            FROM member_profiles
            WHERE guild_id = ?
              AND birthday_month = ?
              AND birthday_day BETWEEN 1 AND 31
            ORDER BY birthday_day, user_id
            """,
            (guild_id, month),
        ).fetchall()

    def set_member_profile(
        self,
        guild_id: int,
        user_id: int,
        setting: str,
        value,
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
            raise ValueError(f"Invalid member profile setting: {setting}")

        self.ensure_member(guild_id, user_id)
        self.connection.execute(
            f"""
            UPDATE member_profiles
            SET {setting} = ?
            WHERE guild_id = ? AND user_id = ?
            """,
            (value, guild_id, user_id),
        )
        self.connection.commit()

    def get_profile_last_edited(self, guild_id: int, user_id: int):
        profile = self.get_member_profile(guild_id, user_id)
        return profile["profile_last_edited"]

    def set_profile_last_edited(
        self,
        guild_id: int,
        user_id: int,
        timestamp: str,
    ):
        self.ensure_member(guild_id, user_id)
        self.connection.execute("""
            UPDATE member_profiles
            SET profile_last_edited = ?
            WHERE guild_id = ? AND user_id = ?
        """, (timestamp, guild_id, user_id))
        self.connection.commit()

    # ---------------- Quiz ----------------

    def get_quiz_score(self, guild_id: int, user_id: int):
        profile = self.get_member_profile(guild_id, user_id)
        return profile["quiz_points"]

    def add_quiz_point(self, guild_id: int, user_id: int):
        self.ensure_member(guild_id, user_id)
        self.connection.execute("""
            UPDATE member_profiles
            SET quiz_points = quiz_points + 1
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        self.connection.commit()

    def has_answered_quiz(
        self,
        guild_id: int,
        user_id: int,
        quiz_date: str,
    ):
        profile = self.get_member_profile(guild_id, user_id)
        return profile["quiz_last_answered"] == quiz_date

    def record_quiz_answer(
        self,
        guild_id: int,
        user_id: int,
        quiz_date: str,
        correct: bool,
    ):
        self.ensure_member(guild_id, user_id)
        cursor = self.connection.execute("""
            UPDATE member_profiles
            SET quiz_questions_answered = quiz_questions_answered + 1,
                quiz_last_answered = ?
            WHERE guild_id = ?
            AND user_id = ?
            AND (
                quiz_last_answered IS NULL
                OR quiz_last_answered != ?
            )
        """, (quiz_date, guild_id, user_id, quiz_date))

        if cursor.rowcount == 0:
            raise sqlite3.IntegrityError(
                "Quiz answer already recorded for this date."
            )

        self.connection.commit()

    # ---------------- Icebreakers ----------------

    def add_icebreaker_question(
        self,
        guild_id: int,
        question: str,
        added_by: int | None = None,
    ):
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")

        self.connection.execute("""
            INSERT OR IGNORE INTO icebreaker_custom_questions (
                guild_id, question, added_by
            )
            VALUES (?, ?, ?)
        """, (guild_id, question, added_by))
        self.connection.commit()

    def get_icebreaker_questions(self, guild_id: int):
        return self.connection.execute("""
            SELECT *
            FROM icebreaker_custom_questions
            WHERE guild_id = ?
            ORDER BY question COLLATE NOCASE
        """, (guild_id,)).fetchall()

    def remove_icebreaker_question(self, guild_id: int, question_id: int):
        self.connection.execute("""
            DELETE FROM icebreaker_custom_questions
            WHERE guild_id = ? AND id = ?
        """, (guild_id, question_id))
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

    def mark_icebreaker_question_used(self, guild_id: int, question_key: str):
        self.connection.execute("""
            INSERT OR IGNORE INTO icebreaker_question_usage (
                guild_id, question_key
            )
            VALUES (?, ?)
        """, (guild_id, question_key))
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
        posted_date: str,
    ):
        self.connection.execute("""
            INSERT INTO icebreaker_history (
                guild_id, question_key, question_text, posted_date
            )
            VALUES (?, ?, ?, ?)
        """, (guild_id, question_key, question_text, posted_date))
        self.connection.commit()

    def get_icebreaker_history(self, guild_id: int, limit: int = 30):
        return self.connection.execute("""
            SELECT *
            FROM icebreaker_history
            WHERE guild_id = ?
            ORDER BY posted_date DESC
            LIMIT ?
        """, (guild_id, limit)).fetchall()

    def has_icebreaker_posted(self, guild_id: int, posted_date: str) -> bool:
        return self.connection.execute("""
            SELECT 1
            FROM icebreaker_history
            WHERE guild_id = ? AND posted_date = ?
        """, (guild_id, posted_date)).fetchone() is not None

    # ---------------- Reaction-role posts ----------------

    def create_reaction_role_post(
        self,
        guild_id: int,
        channel_id: int,
        title: str = "Choose your roles!",
        description: str = "",
        status: str = "draft",
    ) -> int:
        if status not in {"draft", "published"}:
            raise ValueError("Invalid reaction-role post status.")

        cursor = self.connection.execute("""
            INSERT INTO reaction_role_posts (
                guild_id,
                channel_id,
                title,
                description,
                status,
                draft_expires_at
            )
            VALUES (
                ?, ?, ?, ?, ?,
                CASE
                    WHEN ? = 'draft'
                    THEN datetime('now', '+14 days')
                    ELSE NULL
                END
            )
        """, (
            guild_id,
            channel_id,
            title,
            description,
            status,
            status,
        ))
        self.connection.commit()
        return cursor.lastrowid

    def get_reaction_role_posts(self, guild_id: int):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_posts
            WHERE guild_id = ?
            ORDER BY id DESC
        """, (guild_id,)).fetchall()

    def get_reaction_role_post(self, post_id: int):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_posts
            WHERE id = ?
        """, (post_id,)).fetchone()

    def get_reaction_role_post_by_message(self, message_id: int):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_posts
            WHERE message_id = ?
            AND status = 'published'
        """, (message_id,)).fetchone()

    def get_reaction_role_drafts(self, guild_id: int):
        self.delete_expired_reaction_role_drafts()
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_posts
            WHERE guild_id = ?
            AND status = 'draft'
            ORDER BY updated_at DESC, id DESC
        """, (guild_id,)).fetchall()

    def get_published_reaction_role_posts(self, guild_id: int):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_posts
            WHERE guild_id = ?
            AND status = 'published'
            ORDER BY id DESC
        """, (guild_id,)).fetchall()

    
    def save_reaction_role_draft(
        self,
        post_id: int | None,
        guild_id: int,
        channel_id: int | None,
        title: str,
        description: str,
    ) -> int:
        stored_channel_id = channel_id or 0

        if post_id is None:
            cursor = self.connection.execute("""
                INSERT INTO reaction_role_posts (
                    guild_id,
                    channel_id,
                    title,
                    description,
                    status,
                    draft_expires_at
                )
                VALUES (
                    ?, ?, ?, ?, 'draft',
                    datetime('now', '+14 days')
                )
            """, (
                guild_id,
                stored_channel_id,
                title,
                description,
            ))
            saved_id = cursor.lastrowid
        else:
            cursor = self.connection.execute("""
                UPDATE reaction_role_posts
                SET channel_id = ?,
                    title = ?,
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    draft_expires_at = datetime('now', '+14 days')
                WHERE id = ?
                AND guild_id = ?
                AND status = 'draft'
            """, (
                stored_channel_id,
                title,
                description,
                post_id,
                guild_id,
            ))

            if cursor.rowcount == 0:
                raise ValueError(
                    "This draft no longer exists or cannot be edited."
                )

            saved_id = post_id

        self.connection.commit()
        return saved_id

    def mark_reaction_role_post_published(
        self,
        post_id: int,
        message_id: int,
    ):
        cursor = self.connection.execute("""
            UPDATE reaction_role_posts
            SET message_id = ?,
                status = 'published',
                draft_expires_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (message_id, post_id))

        if cursor.rowcount == 0:
            raise ValueError("Reaction-role post not found.")

        self.connection.commit()

    def update_reaction_role_post(
        self,
        post_id: int,
        setting: str,
        value,
    ):
        allowed_settings = {
            "guild_id",
            "channel_id",
            "message_id",
            "title",
            "description",
            "status",
            "draft_expires_at",
        }

        if setting not in allowed_settings:
            raise ValueError(
                f"Invalid reaction-role post setting: {setting}"
            )

        self.connection.execute(
            f"""
            UPDATE reaction_role_posts
            SET {setting} = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (value, post_id),
        )
        self.connection.commit()

    def delete_expired_reaction_role_drafts(self):
        self.connection.execute("""
            DELETE FROM reaction_role_posts
            WHERE status = 'draft'
            AND draft_expires_at IS NOT NULL
            AND datetime(draft_expires_at) <= datetime('now')
        """)
        self.connection.commit()

    def delete_reaction_role_post(self, post_id: int):
        self.connection.execute("""
            DELETE FROM reaction_role_posts
            WHERE id = ?
        """, (post_id,))
        self.connection.commit()

    # ---------------- Reaction-role entries ----------------

    def add_reaction_role_entry(
        self,
        post_id: int,
        role_id: int,
        emoji: str,
        description: str = "",
        position: int = 0,
        role_color: int | None = None,
        channel_permissions: str | None = None,
        role_icon: str | None = None,
    ) -> int:
        cursor = self.connection.execute("""
            INSERT INTO reaction_role_entries (
                post_id,
                role_id,
                emoji,
                description,
                position,
                role_color,
                channel_permissions,
                role_icon
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id,
            role_id,
            emoji,
            description,
            position,
            role_color,
            channel_permissions,
            role_icon,
        ))
        self.connection.commit()
        return cursor.lastrowid

    def get_reaction_role_entries(self, post_id: int):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_entries
            WHERE post_id = ?
            ORDER BY position ASC, id ASC
        """, (post_id,)).fetchall()

    def get_reaction_role_entry_by_emoji(
        self,
        post_id: int,
        emoji: str,
    ):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_entries
            WHERE post_id = ? AND emoji = ?
        """, (post_id, emoji)).fetchone()

    def get_reaction_role_entry_by_role(
        self,
        post_id: int,
        role_id: int,
    ):
        return self.connection.execute("""
            SELECT *
            FROM reaction_role_entries
            WHERE post_id = ? AND role_id = ?
        """, (post_id, role_id)).fetchone()

    def update_reaction_role_entry(
        self,
        entry_id: int,
        setting: str,
        value,
    ):
        allowed_settings = {
            "role_id",
            "emoji",
            "description",
            "position",
            "role_color",
            "channel_permissions",
            "role_icon",
        }

        if setting not in allowed_settings:
            raise ValueError(
                f"Invalid reaction-role entry setting: {setting}"
            )

        self.connection.execute(
            f"""
            UPDATE reaction_role_entries
            SET {setting} = ?
            WHERE id = ?
            """,
            (value, entry_id),
        )
        self.connection.commit()

    def delete_reaction_role_entry(self, entry_id: int):
        self.connection.execute("""
            DELETE FROM reaction_role_entries
            WHERE id = ?
        """, (entry_id,))
        self.connection.commit()

    def close(self):
        self.connection.close()
