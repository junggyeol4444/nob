"""데이터베이스 연결 및 기본 CRUD 작업 관리"""
import sqlite3
import os
import threading
from typing import List, Optional
from .models import Project, Chapter, Character, WorldBuilding, GenerationHistory


class DatabaseManager:
    """SQLite 데이터베이스 관리 클래스 (스레드 안전 - 스레드별 연결 사용)"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_db_dir()
        self._initialize()

    def _ensure_db_dir(self):
        """DB 파일 디렉토리 생성"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _initialize(self):
        """데이터베이스 초기화 및 스키마 적용"""
        conn = self._get_connection()
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """현재 스레드 전용 DB 연결 반환 (없으면 새로 생성)"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def close(self):
        """현재 스레드의 DB 연결 종료"""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    # ──────────────────────────────────────────
    # 프로젝트 CRUD
    # ──────────────────────────────────────────

    def create_project(self, project: Project) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO projects (title, genre, description, tone, plot)
               VALUES (?, ?, ?, ?, ?)""",
            (project.title, project.genre, project.description, project.tone, project.plot),
        )
        conn.commit()
        return cur.lastrowid

    def get_project(self, project_id: int) -> Optional[Project]:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT id, title, genre, description, tone, plot, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return Project.from_row(tuple(row)) if row else None

    def get_all_projects(self) -> List[Project]:
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT id, title, genre, description, tone, plot, created_at, updated_at FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        return [Project.from_row(tuple(r)) for r in rows]

    def update_project(self, project: Project):
        conn = self._get_connection()
        conn.execute(
            """UPDATE projects SET title=?, genre=?, description=?, tone=?, plot=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (project.title, project.genre, project.description, project.tone, project.plot, project.id),
        )
        conn.commit()

    def delete_project(self, project_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()

    # ──────────────────────────────────────────
    # 챕터 CRUD
    # ──────────────────────────────────────────

    def create_chapter(self, chapter: Chapter) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO chapters (project_id, chapter_num, title, content, summary, word_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (chapter.project_id, chapter.chapter_num, chapter.title,
             chapter.content, chapter.summary, chapter.word_count),
        )
        conn.commit()
        return cur.lastrowid

    def get_chapter(self, chapter_id: int) -> Optional[Chapter]:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT id, project_id, chapter_num, title, content, summary, word_count, created_at FROM chapters WHERE id=?",
            (chapter_id,),
        ).fetchone()
        return Chapter.from_row(tuple(row)) if row else None

    def get_chapters_by_project(self, project_id: int) -> List[Chapter]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, project_id, chapter_num, title, content, summary, word_count, created_at
               FROM chapters WHERE project_id=? ORDER BY chapter_num""",
            (project_id,),
        ).fetchall()
        return [Chapter.from_row(tuple(r)) for r in rows]

    def update_chapter(self, chapter: Chapter):
        conn = self._get_connection()
        conn.execute(
            """UPDATE chapters SET chapter_num=?, title=?, content=?, summary=?, word_count=?
               WHERE id=?""",
            (chapter.chapter_num, chapter.title, chapter.content,
             chapter.summary, chapter.word_count, chapter.id),
        )
        conn.commit()

    def delete_chapter(self, chapter_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM chapters WHERE id=?", (chapter_id,))
        conn.commit()

    def get_next_chapter_num(self, project_id: int) -> int:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT MAX(chapter_num) FROM chapters WHERE project_id=?", (project_id,)
        ).fetchone()
        max_num = row[0] if row[0] is not None else 0
        return max_num + 1

    # ──────────────────────────────────────────
    # 캐릭터 CRUD
    # ──────────────────────────────────────────

    def create_character(self, character: Character) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO characters (project_id, name, age, personality, appearance, background, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (character.project_id, character.name, character.age,
             character.personality, character.appearance, character.background, character.notes),
        )
        conn.commit()
        return cur.lastrowid

    def get_characters_by_project(self, project_id: int) -> List[Character]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, project_id, name, age, personality, appearance, background, notes
               FROM characters WHERE project_id=? ORDER BY name""",
            (project_id,),
        ).fetchall()
        return [Character.from_row(tuple(r)) for r in rows]

    def update_character(self, character: Character):
        conn = self._get_connection()
        conn.execute(
            """UPDATE characters SET name=?, age=?, personality=?, appearance=?, background=?, notes=?
               WHERE id=?""",
            (character.name, character.age, character.personality,
             character.appearance, character.background, character.notes, character.id),
        )
        conn.commit()

    def delete_character(self, character_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM characters WHERE id=?", (character_id,))
        conn.commit()

    # ──────────────────────────────────────────
    # 세계관 CRUD
    # ──────────────────────────────────────────

    def create_worldbuilding(self, wb: WorldBuilding) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            "INSERT INTO worldbuilding (project_id, category, title, content) VALUES (?, ?, ?, ?)",
            (wb.project_id, wb.category, wb.title, wb.content),
        )
        conn.commit()
        return cur.lastrowid

    def get_worldbuilding_by_project(self, project_id: int) -> List[WorldBuilding]:
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT id, project_id, category, title, content FROM worldbuilding WHERE project_id=? ORDER BY category, title",
            (project_id,),
        ).fetchall()
        return [WorldBuilding.from_row(tuple(r)) for r in rows]

    def update_worldbuilding(self, wb: WorldBuilding):
        conn = self._get_connection()
        conn.execute(
            "UPDATE worldbuilding SET category=?, title=?, content=? WHERE id=?",
            (wb.category, wb.title, wb.content, wb.id),
        )
        conn.commit()

    def delete_worldbuilding(self, wb_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM worldbuilding WHERE id=?", (wb_id,))
        conn.commit()

    # ──────────────────────────────────────────
    # 생성 히스토리
    # ──────────────────────────────────────────

    def save_generation_history(self, chapter_id: int, content: str) -> int:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT MAX(version) FROM generation_history WHERE chapter_id=?", (chapter_id,)
        ).fetchone()
        next_version = (row[0] or 0) + 1
        cur = conn.execute(
            "INSERT INTO generation_history (chapter_id, version, content) VALUES (?, ?, ?)",
            (chapter_id, next_version, content),
        )
        conn.commit()
        return cur.lastrowid

    def get_generation_history(self, chapter_id: int) -> List[GenerationHistory]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, chapter_id, version, content, created_at
               FROM generation_history WHERE chapter_id=? ORDER BY version DESC""",
            (chapter_id,),
        ).fetchall()
        return [GenerationHistory.from_row(tuple(r)) for r in rows]
