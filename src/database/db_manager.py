"""데이터베이스 연결 및 기본 CRUD 작업 관리"""
import sqlite3
import os
import threading
from typing import List, Optional
from .models import Project, Chapter, Character, WorldBuilding, GenerationHistory, Outline, GenerationJob


class DatabaseManager:
    """SQLite 데이터베이스 관리 클래스 (스레드 안전 - 스레드별 연결 사용)"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_db_dir()
        self._initialize()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _initialize(self):
        conn = self._get_connection()
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    # ── 프로젝트 CRUD ──

    def create_project(self, project: Project) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO projects (title, genre, description, tone, viewpoint, plot, plot_source, total_chapters, chapter_length, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (project.title, project.genre, project.description, project.tone,
             project.viewpoint, project.plot, project.plot_source,
             project.total_chapters, project.chapter_length, project.status),
        )
        conn.commit()
        return cur.lastrowid

    def get_project(self, project_id: int) -> Optional[Project]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, title, genre, description, tone, viewpoint, plot, plot_source,
                      total_chapters, chapter_length, status, created_at, updated_at
               FROM projects WHERE id = ?""",
            (project_id,),
        ).fetchone()
        return Project.from_row(tuple(row)) if row else None

    def get_all_projects(self) -> List[Project]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, title, genre, description, tone, viewpoint, plot, plot_source,
                      total_chapters, chapter_length, status, created_at, updated_at
               FROM projects ORDER BY updated_at DESC"""
        ).fetchall()
        return [Project.from_row(tuple(r)) for r in rows]

    def update_project(self, project: Project):
        conn = self._get_connection()
        conn.execute(
            """UPDATE projects SET title=?, genre=?, description=?, tone=?, viewpoint=?,
               plot=?, plot_source=?, total_chapters=?, chapter_length=?, status=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (project.title, project.genre, project.description, project.tone,
             project.viewpoint, project.plot, project.plot_source,
             project.total_chapters, project.chapter_length, project.status, project.id),
        )
        conn.commit()

    def delete_project(self, project_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.commit()

    # ── 목차 CRUD ──

    def create_outline(self, outline: Outline) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT OR REPLACE INTO outlines (project_id, chapter_num, title, description, source, order_index)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (outline.project_id, outline.chapter_num, outline.title,
             outline.description, outline.source, outline.order_index),
        )
        conn.commit()
        return cur.lastrowid

    def get_outlines_by_project(self, project_id: int) -> List[Outline]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, project_id, chapter_num, title, description, source, order_index, created_at
               FROM outlines WHERE project_id=? ORDER BY chapter_num""",
            (project_id,),
        ).fetchall()
        return [Outline.from_row(tuple(r)) for r in rows]

    def get_outline(self, outline_id: int) -> Optional[Outline]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, chapter_num, title, description, source, order_index, created_at
               FROM outlines WHERE id=?""",
            (outline_id,),
        ).fetchone()
        return Outline.from_row(tuple(row)) if row else None

    def update_outline(self, outline: Outline):
        conn = self._get_connection()
        conn.execute(
            "UPDATE outlines SET chapter_num=?, title=?, description=?, source=?, order_index=? WHERE id=?",
            (outline.chapter_num, outline.title, outline.description,
             outline.source, outline.order_index, outline.id),
        )
        conn.commit()

    def delete_outline(self, outline_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM outlines WHERE id=?", (outline_id,))
        conn.commit()

    def delete_all_outlines(self, project_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM outlines WHERE project_id=?", (project_id,))
        conn.commit()

    # ── 챕터 CRUD ──

    def create_chapter(self, chapter: Chapter) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO chapters (project_id, outline_id, chapter_num, title, content, summary,
               word_count, status, generation_prompt, generation_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (chapter.project_id, chapter.outline_id, chapter.chapter_num, chapter.title,
             chapter.content, chapter.summary, chapter.word_count, chapter.status,
             chapter.generation_prompt, chapter.generation_time),
        )
        conn.commit()
        return cur.lastrowid

    def get_chapter(self, chapter_id: int) -> Optional[Chapter]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, outline_id, chapter_num, title, content, summary, word_count,
                      status, generation_prompt, generation_time, created_at, updated_at
               FROM chapters WHERE id=?""",
            (chapter_id,),
        ).fetchone()
        return Chapter.from_row(tuple(row)) if row else None

    def get_chapter_by_num(self, project_id: int, chapter_num: int) -> Optional[Chapter]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, outline_id, chapter_num, title, content, summary, word_count,
                      status, generation_prompt, generation_time, created_at, updated_at
               FROM chapters WHERE project_id=? AND chapter_num=?""",
            (project_id, chapter_num),
        ).fetchone()
        return Chapter.from_row(tuple(row)) if row else None

    def get_chapters_by_project(self, project_id: int) -> List[Chapter]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, project_id, outline_id, chapter_num, title, content, summary, word_count,
                      status, generation_prompt, generation_time, created_at, updated_at
               FROM chapters WHERE project_id=? ORDER BY chapter_num""",
            (project_id,),
        ).fetchall()
        return [Chapter.from_row(tuple(r)) for r in rows]

    def update_chapter(self, chapter: Chapter):
        conn = self._get_connection()
        conn.execute(
            """UPDATE chapters SET outline_id=?, chapter_num=?, title=?, content=?, summary=?,
               word_count=?, status=?, generation_prompt=?, generation_time=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (chapter.outline_id, chapter.chapter_num, chapter.title, chapter.content,
             chapter.summary, chapter.word_count, chapter.status,
             chapter.generation_prompt, chapter.generation_time, chapter.id),
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

    # ── 캐릭터 CRUD ──

    def create_character(self, character: Character) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO characters (project_id, name, role, age, gender, personality, appearance,
               background, abilities, relationships, character_arc, notes, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (character.project_id, character.name, character.role, character.age,
             character.gender, character.personality, character.appearance,
             character.background, character.abilities, character.relationships,
             character.character_arc, character.notes, character.source),
        )
        conn.commit()
        return cur.lastrowid

    def get_characters_by_project(self, project_id: int) -> List[Character]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, project_id, name, role, age, gender, personality, appearance,
                      background, abilities, relationships, character_arc, notes, source, created_at, updated_at
               FROM characters WHERE project_id=? ORDER BY name""",
            (project_id,),
        ).fetchall()
        return [Character.from_row(tuple(r)) for r in rows]

    def get_character(self, character_id: int) -> Optional[Character]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, name, role, age, gender, personality, appearance,
                      background, abilities, relationships, character_arc, notes, source, created_at, updated_at
               FROM characters WHERE id=?""",
            (character_id,),
        ).fetchone()
        return Character.from_row(tuple(row)) if row else None

    def update_character(self, character: Character):
        conn = self._get_connection()
        conn.execute(
            """UPDATE characters SET name=?, role=?, age=?, gender=?, personality=?, appearance=?,
               background=?, abilities=?, relationships=?, character_arc=?, notes=?, source=?,
               updated_at=CURRENT_TIMESTAMP WHERE id=?""",
            (character.name, character.role, character.age, character.gender,
             character.personality, character.appearance, character.background,
             character.abilities, character.relationships, character.character_arc,
             character.notes, character.source, character.id),
        )
        conn.commit()

    def delete_character(self, character_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM characters WHERE id=?", (character_id,))
        conn.commit()

    # ── 세계관 CRUD ──

    def create_worldbuilding(self, wb: WorldBuilding) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            "INSERT INTO worldbuilding (project_id, category, title, content, source, tags) VALUES (?, ?, ?, ?, ?, ?)",
            (wb.project_id, wb.category, wb.title, wb.content, wb.source, wb.tags),
        )
        conn.commit()
        return cur.lastrowid

    def get_worldbuilding_by_project(self, project_id: int) -> List[WorldBuilding]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, project_id, category, title, content, source, tags, created_at, updated_at
               FROM worldbuilding WHERE project_id=? ORDER BY category, title""",
            (project_id,),
        ).fetchall()
        return [WorldBuilding.from_row(tuple(r)) for r in rows]

    def get_worldbuilding(self, wb_id: int) -> Optional[WorldBuilding]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, category, title, content, source, tags, created_at, updated_at
               FROM worldbuilding WHERE id=?""",
            (wb_id,),
        ).fetchone()
        return WorldBuilding.from_row(tuple(row)) if row else None

    def update_worldbuilding(self, wb: WorldBuilding):
        conn = self._get_connection()
        conn.execute(
            "UPDATE worldbuilding SET category=?, title=?, content=?, source=?, tags=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (wb.category, wb.title, wb.content, wb.source, wb.tags, wb.id),
        )
        conn.commit()

    def delete_worldbuilding(self, wb_id: int):
        conn = self._get_connection()
        conn.execute("DELETE FROM worldbuilding WHERE id=?", (wb_id,))
        conn.commit()

    # ── 생성 히스토리 ──

    def save_generation_history(self, chapter_id: int, content: str, prompt: str = "", params: str = "") -> int:
        conn = self._get_connection()
        row = conn.execute(
            "SELECT MAX(version) FROM generation_history WHERE chapter_id=?", (chapter_id,)
        ).fetchone()
        next_version = (row[0] or 0) + 1
        cur = conn.execute(
            "INSERT INTO generation_history (chapter_id, version, content, prompt, generation_params) VALUES (?, ?, ?, ?, ?)",
            (chapter_id, next_version, content, prompt, params),
        )
        conn.commit()
        return cur.lastrowid

    def get_generation_history(self, chapter_id: int) -> List[GenerationHistory]:
        conn = self._get_connection()
        rows = conn.execute(
            """SELECT id, chapter_id, version, content, prompt, generation_params, created_at
               FROM generation_history WHERE chapter_id=? ORDER BY version DESC""",
            (chapter_id,),
        ).fetchall()
        return [GenerationHistory.from_row(tuple(r)) for r in rows]

    # ── 생성 작업 ──

    def create_generation_job(self, job: GenerationJob) -> int:
        conn = self._get_connection()
        cur = conn.execute(
            """INSERT INTO generation_jobs (project_id, job_type, start_chapter, end_chapter, status, total_chapters)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (job.project_id, job.job_type, job.start_chapter, job.end_chapter,
             job.status, job.total_chapters),
        )
        conn.commit()
        return cur.lastrowid

    def get_generation_job(self, job_id: int) -> Optional[GenerationJob]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, job_type, start_chapter, end_chapter, status, progress,
                      current_chapter, total_chapters, error_message, started_at, completed_at, created_at
               FROM generation_jobs WHERE id=?""",
            (job_id,),
        ).fetchone()
        return GenerationJob.from_row(tuple(row)) if row else None

    def update_generation_job(self, job: GenerationJob):
        conn = self._get_connection()
        conn.execute(
            """UPDATE generation_jobs SET status=?, progress=?, current_chapter=?,
               error_message=?, started_at=?, completed_at=? WHERE id=?""",
            (job.status, job.progress, job.current_chapter,
             job.error_message, job.started_at, job.completed_at, job.id),
        )
        conn.commit()

    def get_active_job_by_project(self, project_id: int) -> Optional[GenerationJob]:
        conn = self._get_connection()
        row = conn.execute(
            """SELECT id, project_id, job_type, start_chapter, end_chapter, status, progress,
                      current_chapter, total_chapters, error_message, started_at, completed_at, created_at
               FROM generation_jobs WHERE project_id=? AND status IN ('pending','running','paused')
               ORDER BY created_at DESC LIMIT 1""",
            (project_id,),
        ).fetchone()
        return GenerationJob.from_row(tuple(row)) if row else None
