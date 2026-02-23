"""프롬프트 생성 모듈"""
from typing import List, Optional
from ..database.models import Project, Chapter, Character, WorldBuilding


SYSTEM_TEMPLATE = """당신은 한국 웹소설 작가입니다. {genre} 장르의 소설을 {tone}로 작성합니다.

컨텍스트:
- 작품 제목: {title}
- 줄거리: {plot}
- 주요 캐릭터: {characters}
- 세계관: {worldbuilding}

이전 내용 요약:
{chapter_summaries}"""

USER_TEMPLATE = """사용자 요청:
{user_prompt}

지시사항:
다음 챕터를 약 {target_length}자 분량으로 작성해주세요. 이전 내용과의 연속성을 유지하고,
캐릭터의 성격과 말투를 일관되게 유지하세요. 챕터 내용만 작성하고, 별도의 설명은 추가하지 마세요."""

SUMMARY_SYSTEM = "당신은 소설 편집자입니다. 주어진 챕터 내용을 100~200자로 간결하게 요약해주세요."

SUMMARY_USER = "다음 챕터 내용을 100~200자로 요약해주세요:\n\n{content}"


class PromptBuilder:
    """AI 생성용 프롬프트 구성 클래스"""

    @staticmethod
    def build_character_summary(characters: List[Character]) -> str:
        if not characters:
            return "없음"
        parts = []
        for c in characters:
            desc = f"- {c.name}"
            if c.age:
                desc += f" ({c.age}세)"
            if c.personality:
                desc += f", 성격: {c.personality}"
            parts.append(desc)
        return "\n".join(parts)

    @staticmethod
    def build_worldbuilding_summary(wbs: List[WorldBuilding]) -> str:
        if not wbs:
            return "없음"
        parts = []
        for wb in wbs[:5]:  # 상위 5개만 포함
            parts.append(f"- [{wb.category}] {wb.title}: {wb.content[:100]}")
        return "\n".join(parts)

    @staticmethod
    def build_chapter_summaries(chapters: List[Chapter], recent_n: int = 3) -> str:
        if not chapters:
            return "없음 (첫 번째 챕터입니다)"
        recent = sorted(chapters, key=lambda c: c.chapter_num)[-recent_n:]
        parts = []
        for ch in recent:
            summary = ch.summary or ch.content[:150] + "..." if ch.content else "(내용 없음)"
            parts.append(f"- {ch.chapter_num}화: {summary}")
        return "\n".join(parts)

    def build_system_prompt(
        self,
        project: Project,
        characters: List[Character],
        worldbuildings: List[WorldBuilding],
        recent_chapters: List[Chapter],
    ) -> str:
        return SYSTEM_TEMPLATE.format(
            genre=project.genre or "판타지",
            tone=project.tone or "3인칭 관찰자 시점",
            title=project.title,
            plot=project.plot or "없음",
            characters=self.build_character_summary(characters),
            worldbuilding=self.build_worldbuilding_summary(worldbuildings),
            chapter_summaries=self.build_chapter_summaries(recent_chapters),
        )

    def build_user_prompt(self, user_request: str, target_length: int) -> str:
        return USER_TEMPLATE.format(
            user_prompt=user_request or "자연스러운 다음 내용을 작성해주세요.",
            target_length=target_length,
        )

    @staticmethod
    def build_summary_prompts(content: str):
        """챕터 요약용 프롬프트 반환 (system, user)"""
        return SUMMARY_SYSTEM, SUMMARY_USER.format(content=content[:2000])
