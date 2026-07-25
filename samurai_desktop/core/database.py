import sqlite3
import json
import sys
import os
from datetime import datetime
from typing import Optional, List
from pathlib import Path

def _get_data_dir() -> Path:
    """Возвращает папку data рядом с exe или рядом с main.py."""
    if getattr(sys, 'frozen', False):
        # Запущено как exe
        base = Path(sys.executable).parent
    else:
        # Запущено как скрипт
        base = Path(__file__).parent.parent
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

DB_PATH = _get_data_dir() / "samurai.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                login TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                project_type TEXT NOT NULL,
                date_created TEXT NOT NULL,
                date_launched TEXT,
                status TEXT NOT NULL DEFAULT 'seed',
                file_path TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS idea_entries (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                theme TEXT NOT NULL,
                description TEXT NOT NULL,
                date_received TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT 'red',
                phase INTEGER NOT NULL DEFAULT 0,
                project_name TEXT DEFAULT '',
                checklist TEXT NOT NULL DEFAULT '[]',
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS mvp_tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                parent_task_id TEXT,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'in_work',
                test_mark TEXT NOT NULL DEFAULT 'none',
                task_order INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS eco_entries (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                source_project_id TEXT,
                description TEXT NOT NULL,
                date_received TEXT NOT NULL,
                entry_type TEXT NOT NULL DEFAULT 'new',
                result TEXT DEFAULT '',
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS tree_projects (
                project_id TEXT PRIMARY KEY,
                checklists TEXT NOT NULL DEFAULT '[]',
                keys_tools TEXT NOT NULL DEFAULT '[]',
                finance_data TEXT NOT NULL DEFAULT '{}',
                stability_achieved INTEGER NOT NULL DEFAULT 0,
                eco_sent INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                entry_id TEXT NOT NULL,
                prompt_id TEXT NOT NULL,
                phase INTEGER NOT NULL DEFAULT 1,
                messages TEXT NOT NULL DEFAULT '[]',
                is_complete INTEGER NOT NULL DEFAULT 0,
                revision_used INTEGER NOT NULL DEFAULT 0
            );
                           
            CREATE TABLE IF NOT EXISTS eco_release_projects (
                id TEXT PRIMARY KEY,
                eco_entry_id TEXT NOT NULL,
                description TEXT DEFAULT '',
                checklist TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL DEFAULT '[]',
                date_received TEXT NOT NULL,
                date_launched TEXT DEFAULT ''
            );
        """)
        # Миграция — добавляем колонки если не существуют
        try:
            conn.execute("ALTER TABLE idea_entries ADD COLUMN project_name TEXT DEFAULT ''")
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE idea_entries ADD COLUMN checklist TEXT NOT NULL DEFAULT '[]'")
            conn.commit()
        except Exception:
            pass
        conn.commit()


# ── Users ──────────────────────────────────────────────
def create_user(login: str, password_hash: str, user_id: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (id, login, password_hash) VALUES (?, ?, ?)",
                (user_id, login, password_hash)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def get_user(login: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE login = ?", (login,)
        ).fetchone()


def user_exists() -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        return row["cnt"] > 0


# ── IdeaEntry ──────────────────────────────────────────
def save_idea_entry(entry) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO idea_entries
            (id, project_id, theme, description, date_received, color, phase)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.project_id,
            entry.theme.value,
            entry.description,
            entry.date_received.isoformat(),
            entry.color.value,
            entry.phase
        ))
        conn.commit()


def get_idea_entries(theme: Optional[str] = None) -> List[sqlite3.Row]:
    with get_connection() as conn:
        if theme:
            return conn.execute(
                "SELECT * FROM idea_entries WHERE theme = ? ORDER BY date_received DESC",
                (theme,)
            ).fetchall()
        return conn.execute(
            "SELECT * FROM idea_entries ORDER BY date_received DESC"
        ).fetchall()


def update_idea_entry_color(entry_id: str, color: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE idea_entries SET color = ? WHERE id = ?",
            (color, entry_id)
        )
        conn.commit()


def update_idea_entry_phase(entry_id: str, phase: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE idea_entries SET phase = ? WHERE id = ?",
            (phase, entry_id)
        )
        conn.commit()


def delete_idea_entry(entry_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM idea_entries WHERE id = ?", (entry_id,))
        conn.commit()


# ── ChatSession ────────────────────────────────────────
def save_chat_session(session) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO chat_sessions
            (id, entry_id, prompt_id, phase, messages, is_complete, revision_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session.id,
            session.entry_id,
            session.prompt_id,
            session.phase,
            json.dumps(session.messages, ensure_ascii=False),
            int(session.is_complete),
            int(session.revision_used)
        ))
        conn.commit()


def get_chat_session(entry_id: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM chat_sessions WHERE entry_id = ?", (entry_id,)
        ).fetchone()


# ── Projects ───────────────────────────────────────────
def save_project(project) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO projects
            (id, title, description, project_type, date_created, date_launched, status, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project.id,
            project.title,
            project.description,
            project.project_type.value,
            project.date_created.isoformat(),
            project.date_launched.isoformat() if project.date_launched else None,
            project.status.value,
            project.file_path
        ))
        conn.commit()


def get_all_projects() -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM projects ORDER BY date_created DESC"
        ).fetchall()


# ── MVPTask ────────────────────────────────────────────
def save_mvp_task(task) -> None:
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO mvp_tasks
            (id, project_id, parent_task_id, title, status, test_mark, task_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.project_id,
            task.parent_task_id,
            task.title,
            task.status.value,
            task.test_mark.value,
            task.order
        ))
        conn.commit()


def get_mvp_tasks(project_id: str) -> List[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM mvp_tasks WHERE project_id = ? ORDER BY task_order",
            (project_id,)
        ).fetchall()

# ── Archive ────────────────────────────────────────────────
def save_to_archive(entry) -> None:
    """Сохраняет запись в архив при переходе на следующий этап."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS idea_archive (
                id TEXT PRIMARY KEY,
                original_id TEXT,
                theme TEXT NOT NULL,
                description TEXT NOT NULL,
                date_received TEXT NOT NULL,
                date_archived TEXT NOT NULL,
                project_name TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            INSERT OR REPLACE INTO idea_archive
            (id, original_id, theme, description, date_received, date_archived, project_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(__import__('uuid').uuid4()),
            entry["id"],
            entry["theme"],
            entry["description"],
            entry["date_received"],
            __import__('datetime').datetime.now().isoformat(),
            entry.get("project_name", "")
        ))
        conn.commit()


def get_archive_entries(theme: str = None):
    """Получает все записи из архива."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS idea_archive (
                id TEXT PRIMARY KEY,
                original_id TEXT,
                theme TEXT NOT NULL,
                description TEXT NOT NULL,
                date_received TEXT NOT NULL,
                date_archived TEXT NOT NULL,
                project_name TEXT DEFAULT ''
            )
        """)
        if theme:
            return conn.execute(
                "SELECT * FROM idea_archive WHERE theme = ? ORDER BY date_archived DESC",
                (theme,)
            ).fetchall()
        return conn.execute(
            "SELECT * FROM idea_archive ORDER BY date_archived DESC"
        ).fetchall()


def find_similar_in_archive(description: str, theme: str, threshold: float = 0.3):
    """
    Ищет похожие записи в архиве по простому совпадению слов.
    Возвращает список похожих записей с процентом схожести.
    """
    archive = get_archive_entries(theme)
    if not archive:
        return []

    # Простое сравнение по словам
    words_new = set(description.lower().split())
    if len(words_new) < 2:
        return []

    similar = []
    for entry in archive:
        words_old = set(entry["description"].lower().split())
        if not words_old:
            continue

        # Коэффициент Жаккара
        intersection = len(words_new & words_old)
        union = len(words_new | words_old)
        similarity = intersection / union if union > 0 else 0

        if similarity >= threshold:
            similar.append({
                "entry": entry,
                "similarity": round(similarity * 100)
            })

    similar.sort(key=lambda x: x["similarity"], reverse=True)
    return similar[:3]  # Топ 3 похожих

def get_idea_entry(entry_id: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM idea_entries WHERE id = ?", (entry_id,)
        ).fetchone()


def update_idea_entry_project(entry_id: str, project_name: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE idea_entries SET project_name = ? WHERE id = ?",
            (project_name, entry_id)
        )
        conn.commit()


def update_idea_entry_checklist(entry_id: str, checklist) -> None:
    import json
    with get_connection() as conn:
        conn.execute(
            "UPDATE idea_entries SET checklist = ? WHERE id = ?",
            (json.dumps(checklist, ensure_ascii=False), entry_id)
        )
        conn.commit()