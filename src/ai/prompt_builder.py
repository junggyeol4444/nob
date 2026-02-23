"""프롬프트 생성 모듈"""
from typing import List, Optional
from ..database.models import Project, Chapter, Character, WorldBuilding, Outline


SYSTEM_TEMPLATE = """당신은 전문 한국 웹소설 작가입니다. {genre} 장르의 소설을 {tone}로 작성합니다.
시점: {viewpoint}

작품 정보:
- 제목: {title}
- 전체 편수: {total_chapters}편
- 편당 목표 분량: {chapter_length}자
- 줄거리: {plot}

주요 등장인물:
{characters}

세계관 설정:
{worldbuilding}

이전 내용 요약:
{chapter_summaries}"""

USER_TEMPLATE = """{user_prompt}

지시사항:
- {chapter_num}편 "{chapter_title}"을(를) 약 {target_length}자 분량으로 작성하세요.
- 이전 편과 자연스럽게 연결되어야 합니다.
- 등장인물의 성격과 말투를 일관되게 유지하세요.
- 세계관 설정을 일관되게 유지하세요.
- 소설 본문만 작성하고, 별도의 설명이나 메타 텍스트는 추가하지 마세요."""

PLOT_SYSTEM = "당신은 한국 웹소설 전문 기획자입니다. 제목과 장르를 바탕으로 흥미로운 줄거리를 작성합니다."
PLOT_USER = """다음 웹소설의 줄거리를 300~500자로 작성해주세요.
제목: {title}
장르: {genre}
총 편수: {total_chapters}편

줄거리만 작성하고 별도 설명은 추가하지 마세요."""

OUTLINE_SYSTEM = "당신은 한국 웹소설 전문 기획자입니다. 줄거리를 바탕으로 각 편의 제목을 기승전결 구조로 작성합니다."
OUTLINE_USER = """다음 웹소설의 목차를 작성해주세요.
제목: {title}
장르: {genre}
줄거리: {plot}
총 편수: {total_chapters}편

형식: 각 줄에 "편번호. 제목" 형식으로 작성
예시:
1. 환생
2. 새로운 시작
3. 첫 번째 시련
...

{total_chapters}개의 편 제목만 작성하세요."""

CHARACTER_SYSTEM = "당신은 한국 웹소설 캐릭터 디자이너입니다. 장르와 줄거리에 맞는 매력적인 캐릭터를 설계합니다."
CHARACTER_USER = """다음 웹소설의 {role} 캐릭터를 만들어주세요.
제목: {title}
장르: {genre}
줄거리: {plot}

다음 형식으로 작성하세요:
이름: [캐릭터 이름]
나이: [나이]
성별: [성별]
성격: [성격 특징]
외모: [외모 특징]
배경: [배경 스토리]
능력: [특수 능력/스킬]
캐릭터 아크: [성장 방향]"""

WORLDBUILDING_SYSTEM = "당신은 한국 웹소설 세계관 설계 전문가입니다. 장르에 맞는 풍부한 세계관을 구축합니다."
WORLDBUILDING_USER = """다음 웹소설의 세계관을 {category} 카테고리로 상세히 작성해주세요.
제목: {title}
장르: {genre}
줄거리: {plot}

세계관 내용만 작성하고 별도 설명은 추가하지 마세요."""

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
            if c.role:
                desc += f" ({c.role})"
            if c.age:
                desc += f", {c.age}세"
            if c.gender:
                desc += f", {c.gender}"
            if c.personality:
                desc += f"\n  성격: {c.personality}"
            if c.appearance:
                desc += f"\n  외모: {c.appearance}"
            if c.abilities:
                desc += f"\n  능력: {c.abilities}"
            parts.append(desc)
        return "\n".join(parts)

    @staticmethod
    def build_worldbuilding_summary(wbs: List[WorldBuilding]) -> str:
        if not wbs:
            return "없음"
        parts = []
        for wb in wbs[:8]:
            parts.append(f"- [{wb.category}] {wb.title}: {wb.content[:150]}")
        return "\n".join(parts)

    @staticmethod
    def build_chapter_summaries(chapters: List[Chapter], recent_n: int = 5) -> str:
        if not chapters:
            return "없음 (첫 번째 챕터입니다)"
        recent = sorted(chapters, key=lambda c: c.chapter_num)[-recent_n:]
        parts = []
        for ch in recent:
            summary = ch.summary or (ch.content[:150] + "..." if ch.content else "(내용 없음)")
            title_str = f" '{ch.title}'" if ch.title else ""
            parts.append(f"- {ch.chapter_num}편{title_str}: {summary}")
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
            viewpoint=project.viewpoint or "3인칭",
            title=project.title,
            total_chapters=project.total_chapters,
            chapter_length=project.chapter_length,
            plot=project.plot or "없음",
            characters=self.build_character_summary(characters),
            worldbuilding=self.build_worldbuilding_summary(worldbuildings),
            chapter_summaries=self.build_chapter_summaries(recent_chapters),
        )

    def build_user_prompt(
        self,
        user_request: str,
        target_length: int,
        chapter_num: int = 1,
        chapter_title: str = "",
    ) -> str:
        return USER_TEMPLATE.format(
            user_prompt=user_request or "자연스러운 다음 내용을 작성해주세요.",
            target_length=target_length,
            chapter_num=chapter_num,
            chapter_title=chapter_title or f"{chapter_num}편",
        )

    @staticmethod
    def build_plot_prompts(title: str, genre: str, total_chapters: int):
        return PLOT_SYSTEM, PLOT_USER.format(
            title=title, genre=genre, total_chapters=total_chapters
        )

    @staticmethod
    def build_outline_prompts(project: Project):
        return OUTLINE_SYSTEM, OUTLINE_USER.format(
            title=project.title,
            genre=project.genre or "판타지",
            plot=project.plot or "",
            total_chapters=project.total_chapters,
        )

    @staticmethod
    def build_character_prompts(project: Project, role: str):
        return CHARACTER_SYSTEM, CHARACTER_USER.format(
            title=project.title,
            genre=project.genre or "판타지",
            plot=project.plot or "",
            role=role,
        )

    @staticmethod
    def build_worldbuilding_prompts(project: Project, category: str):
        return WORLDBUILDING_SYSTEM, WORLDBUILDING_USER.format(
            title=project.title,
            genre=project.genre or "판타지",
            plot=project.plot or "",
            category=category,
        )

    @staticmethod
    def build_summary_prompts(content: str):
        return SUMMARY_SYSTEM, SUMMARY_USER.format(content=content[:2000])
