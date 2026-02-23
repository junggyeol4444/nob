"""AI 컨텍스트 관리 모듈"""
from typing import Optional, Callable
from ..database.db_manager import DatabaseManager
from ..database.models import Chapter
from .llm_client import LLMClient
from .prompt_builder import PromptBuilder


class ContextManager:
    """챕터 생성 및 요약을 위한 컨텍스트 관리"""

    def __init__(self, db: DatabaseManager, client: LLMClient):
        self.db = db
        self.client = client
        self.builder = PromptBuilder()

    def generate_chapter(
        self,
        project_id: int,
        user_request: str,
        target_length: int = 2000,
        chapter_num: int = 1,
        chapter_title: str = "",
        include_context: bool = True,
        include_characters: bool = True,
        context_window: int = 5,
        on_token: Optional[Callable[[str], None]] = None,
    ) -> str:
        """새 챕터 내용 AI 생성"""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")

        characters = self.db.get_characters_by_project(project_id) if include_characters else []
        worldbuildings = self.db.get_worldbuilding_by_project(project_id)
        recent_chapters = []
        if include_context:
            all_chapters = self.db.get_chapters_by_project(project_id)
            recent_chapters = sorted(all_chapters, key=lambda c: c.chapter_num)[-context_window:]

        system_prompt = self.builder.build_system_prompt(
            project, characters, worldbuildings, recent_chapters
        )
        user_prompt = self.builder.build_user_prompt(
            user_request, target_length, chapter_num, chapter_title
        )

        return self.client.generate(system_prompt, user_prompt, stream=True, on_token=on_token)

    def generate_plot(self, project_id: int) -> str:
        """줄거리 자동 생성"""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")
        system_prompt, user_prompt = self.builder.build_plot_prompts(
            project.title, project.genre or "판타지", project.total_chapters
        )
        return self.client.generate(system_prompt, user_prompt, stream=False)

    def generate_outline(self, project_id: int) -> str:
        """목차 자동 생성 - 원시 텍스트 반환"""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")
        system_prompt, user_prompt = self.builder.build_outline_prompts(project)
        return self.client.generate(system_prompt, user_prompt, stream=False)

    def generate_character(self, project_id: int, role: str) -> str:
        """캐릭터 자동 생성"""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")
        system_prompt, user_prompt = self.builder.build_character_prompts(project, role)
        return self.client.generate(system_prompt, user_prompt, stream=False)

    def generate_worldbuilding(self, project_id: int, category: str) -> str:
        """세계관 항목 자동 생성"""
        project = self.db.get_project(project_id)
        if not project:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")
        system_prompt, user_prompt = self.builder.build_worldbuilding_prompts(project, category)
        return self.client.generate(system_prompt, user_prompt, stream=False)

    def generate_summary(self, chapter: Chapter) -> str:
        """챕터 내용 자동 요약 생성"""
        if not chapter.content:
            return ""
        system_prompt, user_prompt = self.builder.build_summary_prompts(chapter.content)
        return self.client.generate(system_prompt, user_prompt, stream=False)

    def auto_summarize_and_save(self, chapter: Chapter) -> str:
        """챕터 요약 생성 후 DB에 저장"""
        summary = self.generate_summary(chapter)
        if summary:
            chapter.summary = summary
            self.db.update_chapter(chapter)
        return summary
