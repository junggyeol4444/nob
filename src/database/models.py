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
    viewpoint: str = "3인칭"
    plot: str = ""
    plot_source: str = "user"
    total_chapters: int = 100
    chapter_length: int = 2000
    status: str = "active"
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
            viewpoint=row[5] or "3인칭",
            plot=row[6] or "",
            plot_source=row[7] or "user",
            total_chapters=row[8] or 100,
            chapter_length=row[9] or 2000,
            status=row[10] or "active",
            created_at=row[11],
            updated_at=row[12],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "description": self.description,
            "tone": self.tone,
            "viewpoint": self.viewpoint,
            "plot": self.plot,
            "plot_source": self.plot_source,
            "total_chapters": self.total_chapters,
            "chapter_length": self.chapter_length,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Outline:
    """목차 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    chapter_num: int = 1
    title: str = ""
    description: str = ""
    source: str = "user"
    order_index: Optional[int] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Outline":
        return cls(
            id=row[0],
            project_id=row[1],
            chapter_num=row[2],
            title=row[3] or "",
            description=row[4] or "",
            source=row[5] or "user",
            order_index=row[6],
            created_at=row[7],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "chapter_num": self.chapter_num,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "order_index": self.order_index,
            "created_at": self.created_at,
        }


@dataclass
class Chapter:
    """챕터 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    outline_id: Optional[int] = None
    chapter_num: int = 1
    title: str = ""
    content: str = ""
    summary: str = ""
    word_count: int = 0
    status: str = "draft"
    generation_prompt: str = ""
    generation_time: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Chapter":
        return cls(
            id=row[0],
            project_id=row[1],
            outline_id=row[2],
            chapter_num=row[3],
            title=row[4] or "",
            content=row[5] or "",
            summary=row[6] or "",
            word_count=row[7] or 0,
            status=row[8] or "draft",
            generation_prompt=row[9] or "",
            generation_time=row[10],
            created_at=row[11],
            updated_at=row[12],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "outline_id": self.outline_id,
            "chapter_num": self.chapter_num,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "word_count": self.word_count,
            "status": self.status,
            "generation_time": self.generation_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Character:
    """캐릭터 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    name: str = ""
    role: str = ""
    age: Optional[int] = None
    gender: str = ""
    personality: str = ""
    appearance: str = ""
    background: str = ""
    abilities: str = ""
    relationships: str = ""
    character_arc: str = ""
    notes: str = ""
    source: str = "user"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Character":
        return cls(
            id=row[0],
            project_id=row[1],
            name=row[2],
            role=row[3] or "",
            age=row[4],
            gender=row[5] or "",
            personality=row[6] or "",
            appearance=row[7] or "",
            background=row[8] or "",
            abilities=row[9] or "",
            relationships=row[10] or "",
            character_arc=row[11] or "",
            notes=row[12] or "",
            source=row[13] or "user",
            created_at=row[14],
            updated_at=row[15],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "role": self.role,
            "age": self.age,
            "gender": self.gender,
            "personality": self.personality,
            "appearance": self.appearance,
            "background": self.background,
            "abilities": self.abilities,
            "relationships": self.relationships,
            "character_arc": self.character_arc,
            "notes": self.notes,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorldBuilding:
    """세계관 설정 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    category: str = ""
    title: str = ""
    content: str = ""
    source: str = "user"
    tags: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "WorldBuilding":
        return cls(
            id=row[0],
            project_id=row[1],
            category=row[2] or "",
            title=row[3] or "",
            content=row[4] or "",
            source=row[5] or "user",
            tags=row[6] or "",
            created_at=row[7],
            updated_at=row[8],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "category": self.category,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class GenerationHistory:
    """생성 히스토리 모델"""
    id: Optional[int] = None
    chapter_id: Optional[int] = None
    version: int = 1
    content: str = ""
    prompt: str = ""
    generation_params: str = ""
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "GenerationHistory":
        return cls(
            id=row[0],
            chapter_id=row[1],
            version=row[2] or 1,
            content=row[3] or "",
            prompt=row[4] or "",
            generation_params=row[5] or "",
            created_at=row[6],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "version": self.version,
            "content": self.content,
            "prompt": self.prompt,
            "generation_params": self.generation_params,
            "created_at": self.created_at,
        }


@dataclass
class GenerationJob:
    """생성 작업 모델"""
    id: Optional[int] = None
    project_id: Optional[int] = None
    job_type: str = "single"
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None
    status: str = "pending"
    progress: int = 0
    current_chapter: Optional[int] = None
    total_chapters: Optional[int] = None
    error_message: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "GenerationJob":
        return cls(
            id=row[0],
            project_id=row[1],
            job_type=row[2],
            start_chapter=row[3],
            end_chapter=row[4],
            status=row[5] or "pending",
            progress=row[6] or 0,
            current_chapter=row[7],
            total_chapters=row[8],
            error_message=row[9] or "",
            started_at=row[10],
            completed_at=row[11],
            created_at=row[12],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "job_type": self.job_type,
            "start_chapter": self.start_chapter,
            "end_chapter": self.end_chapter,
            "status": self.status,
            "progress": self.progress,
            "current_chapter": self.current_chapter,
            "total_chapters": self.total_chapters,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at,
        }

