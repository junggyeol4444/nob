"""자동 소설 생성 엔진 - 배치/전체 자동 생성"""
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Callable

from ..database.db_manager import DatabaseManager
from ..database.models import Chapter, GenerationJob
from .context_manager import ContextManager

# 활성 생성 작업 추적 (job_id -> threading.Event)
_cancel_events: dict = {}
_pause_events: dict = {}
_lock = threading.Lock()


def _register_job(job_id: int):
    with _lock:
        _cancel_events[job_id] = threading.Event()
        _pause_events[job_id] = threading.Event()


def _unregister_job(job_id: int):
    with _lock:
        _cancel_events.pop(job_id, None)
        _pause_events.pop(job_id, None)


def cancel_job(job_id: int):
    with _lock:
        ev = _cancel_events.get(job_id)
    if ev:
        ev.set()


def pause_job(job_id: int):
    with _lock:
        ev = _pause_events.get(job_id)
    if ev:
        ev.set()


def resume_job(job_id: int):
    with _lock:
        ev = _pause_events.get(job_id)
    if ev:
        ev.clear()


def is_cancelled(job_id: int) -> bool:
    with _lock:
        ev = _cancel_events.get(job_id)
    return ev.is_set() if ev else False


def is_paused(job_id: int) -> bool:
    with _lock:
        ev = _pause_events.get(job_id)
    return ev.is_set() if ev else False


class AutoGenerator:
    """배치/전체 자동 챕터 생성 엔진"""

    def __init__(self, db: DatabaseManager, ctx: ContextManager,
                 on_progress: Optional[Callable] = None):
        self.db = db
        self.ctx = ctx
        self.on_progress = on_progress  # callback(job_id, job_dict)

    def start_job(self, job: GenerationJob, target_length: int = 2000,
                  temperature: float = 0.7, user_instruction: str = "") -> threading.Thread:
        """생성 작업을 백그라운드 스레드에서 시작"""
        _register_job(job.id)
        t = threading.Thread(
            target=self._run_job,
            args=(job, target_length, temperature, user_instruction),
            daemon=True,
        )
        t.start()
        return t

    def _run_job(self, job: GenerationJob, target_length: int,
                 temperature: float, user_instruction: str):
        job.status = "running"
        job.started_at = datetime.now(timezone.utc).isoformat()
        self.db.update_generation_job(job)
        self._notify(job)

        start_ch = job.start_chapter or 1
        end_ch = job.end_chapter or start_ch
        total = end_ch - start_ch + 1
        job.total_chapters = total
        completed = 0

        try:
            for ch_num in range(start_ch, end_ch + 1):
                # 취소 확인
                if is_cancelled(job.id):
                    job.status = "failed"
                    job.error_message = "사용자에 의해 취소됨"
                    break

                # 일시정지 대기
                while is_paused(job.id):
                    job.status = "paused"
                    self.db.update_generation_job(job)
                    self._notify(job)
                    time.sleep(1)
                    if is_cancelled(job.id):
                        break

                if is_cancelled(job.id):
                    job.status = "failed"
                    job.error_message = "사용자에 의해 취소됨"
                    break

                job.status = "running"
                job.current_chapter = ch_num
                self.db.update_generation_job(job)
                self._notify(job)

                # 목차에서 제목 조회
                outlines = self.db.get_outlines_by_project(job.project_id)
                outline_map = {o.chapter_num: o for o in outlines}
                outline = outline_map.get(ch_num)
                chapter_title = outline.title if outline else f"{ch_num}편"

                # 이미 생성된 챕터 확인 (중복 방지)
                existing = self.db.get_chapter_by_num(job.project_id, ch_num)

                t0 = time.time()
                try:
                    content = self.ctx.generate_chapter(
                        project_id=job.project_id,
                        user_request=user_instruction or "자연스러운 다음 내용을 작성해주세요.",
                        target_length=target_length,
                        chapter_num=ch_num,
                        chapter_title=chapter_title,
                    )
                except Exception as e:
                    job.status = "failed"
                    job.error_message = f"{ch_num}편 생성 실패: {str(e)}"
                    self.db.update_generation_job(job)
                    self._notify(job)
                    _unregister_job(job.id)
                    return

                elapsed = time.time() - t0
                word_count = len(content)

                if existing:
                    # 히스토리 저장 후 덮어쓰기
                    self.db.save_generation_history(existing.id, existing.content)
                    existing.content = content
                    existing.title = chapter_title
                    existing.word_count = word_count
                    existing.status = "generated"
                    existing.generation_time = elapsed
                    self.db.update_chapter(existing)
                    chapter_id = existing.id
                else:
                    chapter = Chapter(
                        project_id=job.project_id,
                        outline_id=outline.id if outline else None,
                        chapter_num=ch_num,
                        title=chapter_title,
                        content=content,
                        word_count=word_count,
                        status="generated",
                        generation_time=elapsed,
                    )
                    chapter_id = self.db.create_chapter(chapter)

                # 요약 자동 생성
                try:
                    ch = self.db.get_chapter(chapter_id)
                    if ch:
                        self.ctx.auto_summarize_and_save(ch)
                except Exception:
                    pass

                completed += 1
                job.progress = int(completed / total * 100)
                self.db.update_generation_job(job)
                self._notify(job)

            else:
                # 정상 완료
                job.status = "completed"
                job.progress = 100
                job.completed_at = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)

        self.db.update_generation_job(job)
        self._notify(job)
        _unregister_job(job.id)

    def _notify(self, job: GenerationJob):
        if self.on_progress:
            try:
                self.on_progress(job.id, job.to_dict())
            except Exception:
                pass
