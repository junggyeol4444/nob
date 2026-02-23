"""데이터 모델 정의"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Project:
    """프로젝트 모델"""
    id: Optional[int] = None
    title: str = ""
    genre: str = ""
    description: str = ""
    tone: str = ""
    plot: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Project":
        return cls(
            id=row[0],
            title=row[1],
            genre=row[2] or "",
            description=row[3] or "",
            tone=row[4] or "",
            plot=row[5] or "",
            created_at=row[6],
            updated_at=row[7],
        )


@dataclass
class Chapter:
    """챕터 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    chapter_num: int = 1
    title: str = ""
    content: str = ""
    summary: str = ""
    word_count: int = 0
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Chapter":
        return cls(
            id=row[0],
            project_id=row[1],
            chapter_num=row[2],
            title=row[3] or "",
            content=row[4] or "",
            summary=row[5] or "",
            word_count=row[6] or 0,
            created_at=row[7],
        )


@dataclass
class Character:
    """캐릭터 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""
    age: Optional[int] = None
    personality: str = ""
    appearance: str = ""
    background: str = ""
    notes: str = ""

    @classmethod
    def from_row(cls, row: tuple) -> "Character":
        return cls(
            id=row[0],
            project_id=row[1],
            name=row[2],
            age=row[3],
            personality=row[4] or "",
            appearance=row[5] or "",
            background=row[6] or "",
            notes=row[7] or "",
        )


@dataclass
class WorldBuilding:
    """세계관 설정 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    category: str = ""
    title: str = ""
    content: str = ""

    @classmethod
    def from_row(cls, row: tuple) -> "WorldBuilding":
        return cls(
            id=row[0],
            project_id=row[1],
            category=row[2] or "",
            title=row[3] or "",
            content=row[4] or "",
        )


@dataclass
class GenerationHistory:
    """생성 히스토리 모델"""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    version: int = 1
    content: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "GenerationHistory":
        return cls(
            id=row[0],
            chapter_id=row[1],
            version=row[2] or 1,
            content=row[3] or "",
            created_at=row[4],
        )
